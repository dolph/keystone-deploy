import json
import logging
import threading
import uuid

import dataset
import locust


logging.basicConfig()
LOG = logging.getLogger(__name__)

DATASET_LOCK = threading.Lock()

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'}


class WebsiteTasks(locust.TaskSet):
    def on_start(self):
        self.admin_token = self.get_token(
            'admin', 'password', project_name='admin')

        self.create_user()
        self.authenticate()
        self.validate()

    def get_token(self, user_name, password, project_name=None):
        d = {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'name': user_name,
                            'password': password,
                            'domain': {
                                'id': 'default'}
                        }
                    }
                }
            }
        }

        if project_name:
            d['auth']['scope'] = {
                'project': {
                    'name': project_name,
                    'domain': {
                        'id': 'default'}}}

        r = self.client.post(
            '/v3/auth/tokens',
            data=json.dumps(d),
            headers=HEADERS)
        if r.status_code == 201:
            return r.headers['X-Subject-Token']
        else:
            LOG.error('%s: %s', r.status_code, r.content)

    @locust.task(1)
    def create_user(self):
        headers = HEADERS.copy()
        headers['X-Auth-Token'] = self.admin_token

        name = uuid.uuid4().hex

        r = self.client.get(
            '/v3/roles',
            name='/v3/roles?name={role_name}',
            headers=headers)
        role = json.loads(r.content)['roles'][0]

        r = self.client.post(
            '/v3/projects',
            data=json.dumps({
                'project': {
                    'domain_id': 'default',
                    'name': name}}),
            headers=headers)
        project = json.loads(r.content)['project']

        r = self.client.post(
            '/v3/users',
            data=json.dumps({
                'user': {
                    'domain_id': 'default',
                    'password': name,
                    'name': name}}),
            headers=headers)
        user = json.loads(r.content)['user']

        r = self.client.put(
            '/v3/projects/%(project)s/users/%(user)s/roles/%(role)s' % {
                'project': project['id'],
                'user': user['id'],
                'role': role['id']},
            name='/v3/projects/{project_id}/users/{user_id}/roles/{role_id}',
            headers=headers)

        with DATASET_LOCK:
            db = dataset.connect('sqlite:///dataset.db')
            db['users'].insert(dict(name=name))

    @locust.task(99)
    def authenticate(self):
        db = dataset.connect('sqlite:///dataset.db')
        for row in db.query('SELECT * FROM users ORDER BY RANDOM() LIMIT 1;'):
            user = row
            break

        auth_token = self.get_token(
            user['name'], user['name'], project_name=user['name'])

        with DATASET_LOCK:
            db = dataset.connect('sqlite:///dataset.db')
            db['tokens'].insert(dict(value=auth_token))

    @locust.task(99)
    def validate(self):
        db = dataset.connect('sqlite:///dataset.db')
        for row in db.query('SELECT * FROM tokens ORDER BY RANDOM() LIMIT 1;'):
            token = row['value']

        headers = HEADERS.copy()
        headers['X-Auth-Token'] = self.admin_token
        headers['X-Subject-Token'] = token
        r = self.client.get(
            '/v3/auth/tokens',
            headers=headers)
        if r.status_code != 200:
            LOG.error('%s: %s', r.status_code, r.content)


class WebsiteUser(locust.HttpLocust):
    task_set = WebsiteTasks
    min_wait = 0
    max_wait = 1000  # auth=100, validate=100, create_user=1000
