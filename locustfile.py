import json
import logging
import random
import uuid

import locust


logging.basicConfig()
LOG = logging.getLogger(__name__)


MAX_LIST_LENGTH = 10000


class ConstrainedList(list):
    """A memory-conscious list."""
    def append(self, x):
        if len(self) > MAX_LIST_LENGTH:
            self.pop(0)
        return super(ConstrainedList, self).append(x)

    def random(self):
        return random.choice(self)


TOKENS = ConstrainedList()
USERS = ConstrainedList()

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'}


class WebsiteTasks(locust.TaskSet):
    def on_start(self, retry=True):
        self.admin_token = self.get_token(
            'admin', 'password', project_name='admin')

        if not self.create_user():
            if retry:
                return self.on_start(retry=False)
            raise Exception('Failed to create initial user.')
        if not self.authenticate():
            if retry:
                return self.on_start(retry=False)
            raise Exception('Failed to authenticate initial user.')
        if not self.validate():
            if retry:
                return self.on_start(retry=False)
            raise Exception('Failed to validate initial user.')

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
        if r.status_code != 201:
            LOG.error('%s creating token: %s', r.status_code, r.content)
            return False

        return r.headers['X-Subject-Token']

    @locust.task(1)
    def create_user(self):
        headers = HEADERS.copy()
        headers['X-Auth-Token'] = self.admin_token

        name = uuid.uuid4().hex

        r = self.client.get(
            '/v3/roles',
            name='/v3/roles?name={role_name}',
            headers=headers)
        if r.status_code != 200:
            LOG.error('%s fetching member role: %s', r.status_code, r.content)
            return False
        role = json.loads(r.content)['roles'][0]

        r = self.client.post(
            '/v3/projects',
            data=json.dumps({
                'project': {
                    'domain_id': 'default',
                    'name': name}}),
            headers=headers)
        if r.status_code != 201:
            LOG.error('%s creating project: %s', r.status_code, r.content)
            return False
        project = json.loads(r.content)['project']

        r = self.client.post(
            '/v3/users',
            data=json.dumps({
                'user': {
                    'domain_id': 'default',
                    'password': name,
                    'name': name}}),
            headers=headers)
        if r.status_code != 201:
            LOG.error('%s creating project: %s', r.status_code, r.content)
            return False
        user = json.loads(r.content)['user']

        r = self.client.put(
            '/v3/projects/%(project)s/users/%(user)s/roles/%(role)s' % {
                'project': project['id'],
                'user': user['id'],
                'role': role['id']},
            name='/v3/projects/{project_id}/users/{user_id}/roles/{role_id}',
            headers=headers)
        if r.status_code != 204:
            LOG.error('%s assigning role: %s', r.status_code, r.content)
            return False

        USERS.append(name)

        return name

    @locust.task(99)
    def authenticate(self):
        user_name = USERS.random()

        token = self.get_token(
            user_name, user_name, project_name=user_name)

        TOKENS.append(token)

        return token

    @locust.task(99)
    def validate(self):
        token = TOKENS.random()

        headers = HEADERS.copy()
        headers['X-Auth-Token'] = self.admin_token
        headers['X-Subject-Token'] = token
        r = self.client.get(
            '/v3/auth/tokens',
            headers=headers)
        if r.status_code != 200:
            LOG.error('%s validating token: %s', r.status_code, r.content)
            return False

        return True


class WebsiteUser(locust.HttpLocust):
    task_set = WebsiteTasks
    min_wait = 0
    max_wait = 1000  # auth=100, validate=100, create_user=1000
