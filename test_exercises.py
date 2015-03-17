import os
import unittest
import uuid

from keystoneclient.v3 import client
import requests


HOST = os.environ.get('HOST', '192.168.111.222')
ECHO_ENDPOINT = os.environ.get('ECHO_ENDPOINT', 'http://%s/' % HOST)
KEYSTONE_ENDPOINT = os.environ.get(
    'KEYSTONE_ENDPOINT', 'http://%s:35357/' % HOST)


class TestCase(unittest.TestCase):
    def setUp(self):
        c = client.Client(
            token='ADMIN',
            endpoint=KEYSTONE_ENDPOINT + 'v3')

        self.domain = c.domains.get('default')

        role = c.roles.create(name='admin')
        self.addCleanup(c.roles.delete, role)

        group = c.groups.create(domain=self.domain, name='admin')
        self.addCleanup(c.groups.delete, group)

        c.roles.grant(group=group, domain=self.domain, role=role)
        self.addCleanup(
            c.roles.revoke, group=group, domain=self.domain, role=role)

        self.project = c.projects.create(domain=self.domain, name='admin')
        self.addCleanup(c.projects.delete, self.project)

        c.roles.grant(group=group, project=self.project, role=role)
        self.addCleanup(
            c.roles.revoke, group=group, project=self.project, role=role)

        self.password = 'password'
        self.user = c.users.create(
            domain=self.domain, name='admin', password=self.password)
        self.addCleanup(c.users.delete, self.user)

        c.users.add_to_group(user=self.user, group=group)

        service = c.services.create(
            name='Keystone', type='identity')
        self.addCleanup(c.services.delete, service)

        public_endpoint = c.endpoints.create(
            service=service,
            interface='public',
            url=KEYSTONE_ENDPOINT + 'v3')
        self.addCleanup(c.endpoints.delete, public_endpoint)
        admin_endpoint = c.endpoints.create(
            service=service,
            interface='admin',
            url=KEYSTONE_ENDPOINT + 'v3')
        self.addCleanup(c.endpoints.delete, admin_endpoint)

    def test_domain_list(self):
        project_scoped = client.Client(
            user_id=self.user.id,
            password=self.password,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(project_scoped.auth_token)

        domains = project_scoped.domains.list()

        self.assertEqual(1, len(domains))

        domain = domains[0]
        self.assertEqual('default', domain.id)
        self.assertEqual('Default', domain.name)
        self.assertEqual(True, domain.enabled)
        self.assertTrue(domain.links['self'].endswith('/v3/domains/default'))

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

    def assertDomainScopedContext(self, domain, context):
        self.assertIdentityContext(context)
        self.assertEqual(None, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(domain.id, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(domain.name, context['HTTP_X_DOMAIN_NAME'])

    def validate_token(self, token, expected_status=200):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': token})
        self.assertEqual(expected_status, r.status_code)
        return r

    def assertUnscopedToken(self, token):
        r = self.validate_token(token)
        self.assertUnscopedContext(r.json())

    def assertProjectScopedToken(self, token):
        r = self.validate_token(token)
        self.assertProjectScopedContext(self.project, self.domain, r.json())

    def assertDomainScopedToken(self, token):
        r = self.validate_token(token)
        self.assertDomainScopedContext(self.domain, r.json())

    def test_unauthorized_request(self):
        self.validate_token(uuid.uuid4().hex, expected_status=401)

    def test_token_rescoping(self):
        # only tests rescoping that involves a narrowing scope

        unscoped = client.Client(
            username=self.user.name,
            password=self.password,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertUnscopedToken(unscoped.auth_token)

        project_scoped = client.Client(
            token=unscoped.auth_token,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertProjectScopedToken(project_scoped.auth_token)

        domain_scoped = client.Client(
            token=unscoped.auth_token,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertDomainScopedToken(domain_scoped.auth_token)

        project_scoped = client.Client(
            token=domain_scoped.auth_token,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertProjectScopedToken(project_scoped.auth_token)

    def test_unscoped_request(self):
        unscoped = client.Client(
            username=self.user.name,
            password=self.password,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertUnscopedToken(unscoped.auth_token)

    def test_project_scoped_request(self):
        project_scoped = client.Client(
            user_id=self.user.id,
            password=self.password,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertProjectScopedToken(project_scoped.auth_token)

    def test_domain_scoped_request(self):
        domain_scoped = client.Client(
            user_id=self.user.id,
            password=self.password,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertDomainScopedToken(domain_scoped.auth_token)
