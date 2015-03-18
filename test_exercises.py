import os
import unittest
import uuid

from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client
import requests


HOST = os.environ.get('HOST', '192.168.111.222')
ECHO_ENDPOINT = os.environ.get('ECHO_ENDPOINT', 'http://%s/' % HOST)
KEYSTONE_ENDPOINT = os.environ.get(
    'KEYSTONE_ENDPOINT', 'http://%s:35357/' % HOST)


def unique():
    return uuid.uuid4().hex


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c = v3_client.Client(
            token='ADMIN',
            endpoint=KEYSTONE_ENDPOINT + 'v3')

        domain = c.domains.get('default')

        roles = c.roles.list(name='admin')
        if roles:
            role = roles[0]
        else:
            role = c.roles.create(name='admin')

        groups = c.groups.list(domain=domain, name='admin')
        if groups:
            group = groups[0]
        else:
            group = c.groups.create(domain=domain, name='admin')

        c.roles.grant(group=group, domain=domain, role=role)

        projects = c.projects.list(domain=domain, name='admin')
        if projects:
            project = projects[0]
        else:
            project = c.projects.create(domain=domain, name='admin')

        c.roles.grant(group=group, project=project, role=role)

        password = 'password'
        users = c.users.list(domain=domain, name='admin')
        if users:
            user = users[0]
        else:
            user = c.users.create(
                domain=domain, name='admin', password=password)

        c.users.add_to_group(user=user, group=group)

        services = c.services.list(
            name='Keystone', type='identity')
        if services:
            service = services[0]
        else:
            service = c.services.create(
                name='Keystone', type='identity')

        endpoints = c.endpoints.list()
        if not [x for x in endpoints if x.interface == 'public']:
            c.endpoints.create(
                service=service,
                interface='public',
                url=KEYSTONE_ENDPOINT + 'v3')
        if not [x for x in endpoints if x.interface == 'admin']:
            c.endpoints.create(
                service=service,
                interface='admin',
                url=KEYSTONE_ENDPOINT + 'v3')

    def setUp(self):
        c = v3_client.Client(
            username='admin',
            password='password',
            project_name='admin',
            auth_url=KEYSTONE_ENDPOINT + 'v3')

        self.domain = c.domains.get('default')

        role = c.roles.create(name=unique())
        self.addCleanup(c.roles.delete, role)

        group = c.groups.create(domain=self.domain, name=unique())
        self.addCleanup(c.groups.delete, group)

        c.roles.grant(group=group, domain=self.domain, role=role)
        self.addCleanup(
            c.roles.revoke, group=group, domain=self.domain, role=role)

        self.project = c.projects.create(domain=self.domain, name=unique())
        self.addCleanup(c.projects.delete, self.project)

        c.roles.grant(group=group, project=self.project, role=role)
        self.addCleanup(
            c.roles.revoke, group=group, project=self.project, role=role)

        self.password = unique()
        self.user = c.users.create(
            domain=self.domain, name=unique(), password=self.password)
        self.addCleanup(c.users.delete, self.user)

        c.users.add_to_group(user=self.user, group=group)

    def assertIdentityContext(self, context):
        self.assertEqual('Confirmed', context['HTTP_X_IDENTITY_STATUS'])
        self.assertEqual(self.user.id, context['HTTP_X_USER_ID'])
        self.assertEqual(self.user.name, context['HTTP_X_USER_NAME'])
        self.assertEqual(self.domain.id, context['HTTP_X_USER_DOMAIN_ID'])
        self.assertEqual(self.domain.name, context['HTTP_X_USER_DOMAIN_NAME'])

        self.assertNotIn('HTTP_X_SERVICE_IDENTITY_STATUS', context)

    def assertUnscopedContext(self, context):
        self.assertIdentityContext(context)
        self.assertEqual(None, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_NAME'])

    def assertProjectScopedContext(self, project, project_domain, context):
        self.assertIdentityContext(context)
        self.assertEqual(project.id, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(project.name, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(
            project_domain.id, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(
            project_domain.name, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_NAME'])

    def exercise_token(self, token, expected_status=200):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': token})
        self.assertEqual(expected_status, r.status_code)
        return r

    def assertUnscopedToken(self, token):
        r = self.exercise_token(token)
        self.assertUnscopedContext(r.json())

    def assertProjectScopedToken(self, token):
        r = self.exercise_token(token)
        self.assertProjectScopedContext(self.project, self.domain, r.json())


class Common(object):
    def test_unauthorized_request(self):
        self.exercise_token(unique(), expected_status=401)

    def test_unscoped_to_project_scoped(self):
        unscoped = self.client.Client(**{
            'username': self.user.name,
            'password': self.password,
            'auth_url': KEYSTONE_ENDPOINT + self.version})
        self.assertUnscopedToken(unscoped.auth_token)

        project_scoped = self.client.Client(**{
            'token': unscoped.auth_token,
            '%s_id' % self.project_term: self.project.id,
            'auth_url': KEYSTONE_ENDPOINT + self.version})
        self.assertProjectScopedToken(project_scoped.auth_token)

    def test_unscoped_token(self):
        unscoped = self.client.Client(**{
            'username': self.user.name,
            'password': self.password,
            'auth_url': KEYSTONE_ENDPOINT + self.version})
        self.assertUnscopedToken(unscoped.auth_token)

    def test_project_scoped_token(self):
        project_scoped = self.client.Client(**{
            'username': self.user.name,
            'password': self.password,
            '%s_id' % self.project_term: self.project.id,
            'auth_url': KEYSTONE_ENDPOINT + self.version})
        self.assertProjectScopedToken(project_scoped.auth_token)


class V2(Base, Common):
    @property
    def version(self):
        return 'v2.0'

    @property
    def client(self):
        return v2_client

    @property
    def project_term(self):
        return 'project'


class V3(Base, Common):
    @property
    def version(self):
        return 'v3'

    @property
    def client(self):
        return v3_client

    @property
    def project_term(self):
        return 'tenant'

    def assertDomainScopedContext(self, domain, context):
        self.assertIdentityContext(context)
        self.assertEqual(None, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(domain.id, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(domain.name, context['HTTP_X_DOMAIN_NAME'])

    def assertDomainScopedToken(self, token):
        r = self.exercise_token(token)
        self.assertDomainScopedContext(self.domain, r.json())

    def test_accessible_projects_list(self):
        project_scoped = self.client.Client(
            user_id=self.user.id,
            password=self.password,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertProjectScopedToken(project_scoped.auth_token)

        projects = project_scoped.projects.list(user=self.user)

        self.assertEqual(1, len(projects))

        project = projects[0]
        self.assertEqual(self.project.id, project.id)
        self.assertEqual(self.project.name, project.name)
        self.assertEqual(self.project.enabled, project.enabled)
        self.assertEqual(self.project.description, project.description)
        self.assertTrue(
            project.links['self'].endswith(
                '/v3/projects/%s' % self.project.id))

    def test_unscoped_to_domain_scoped(self):
        unscoped = self.client.Client(
            username=self.user.name,
            password=self.password,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertUnscopedToken(unscoped.auth_token)

        domain_scoped = self.client.Client(
            token=unscoped.auth_token,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertDomainScopedToken(domain_scoped.auth_token)

    def test_domain_scoped_to_project_scoped(self):
        domain_scoped = self.client.Client(
            username=self.user.name,
            password=self.password,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertDomainScopedToken(domain_scoped.auth_token)

        project_scoped = self.client.Client(
            token=domain_scoped.auth_token,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertProjectScopedToken(project_scoped.auth_token)

    def test_domain_scoped_token(self):
        domain_scoped = self.client.Client(
            user_id=self.user.id,
            password=self.password,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + self.version)
        self.assertDomainScopedToken(domain_scoped.auth_token)
