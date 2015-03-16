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

        password = 'password'
        self.user = c.users.create(
            domain=self.domain, name='admin', password=password)
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

        self.unscoped = client.Client(
            username=self.user.name,
            password=password,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.unscoped.auth_token)

        self.project_scoped = client.Client(
            user_id=self.user.id,
            password=password,
            project_id=self.project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.project_scoped.auth_token)

        self.domain_scoped = client.Client(
            user_id=self.user.id,
            password=password,
            domain_id=self.domain.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.domain_scoped.auth_token)

    def test_domain_list(self):
        self.assertEqual(1, len(self.domain_scoped.domains.list()))

    def _identity_assertions(self, context):
        self.assertEqual('Confirmed', context['HTTP_X_IDENTITY_STATUS'])
        self.assertEqual(self.user.id, context['HTTP_X_USER_ID'])
        self.assertEqual(self.user.name, context['HTTP_X_USER_NAME'])
        self.assertEqual(self.domain.id, context['HTTP_X_USER_DOMAIN_ID'])
        self.assertEqual(self.domain.name, context['HTTP_X_USER_DOMAIN_NAME'])

        self.assertNotIn('HTTP_X_SERVICE_IDENTITY_STATUS', context)

    def test_unauthorized_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': uuid.uuid4().hex})
        self.assertEqual(401, r.status_code)

    def test_unscoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.unscoped.auth_token})
        self.assertEqual(200, r.status_code)

        context = r.json()
        self._identity_assertions(context)
        self.assertEqual(None, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_NAME'])

    def test_project_scoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.project_scoped.auth_token})
        self.assertEqual(200, r.status_code)

        context = r.json()
        self._identity_assertions(context)
        self.assertEqual(self.project.id, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(self.project.name, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(self.domain.id, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(
            self.domain.name, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_DOMAIN_NAME'])

    def test_domain_scoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.domain_scoped.auth_token})
        self.assertEqual(200, r.status_code)

        context = r.json()
        self._identity_assertions(context)
        self.assertEqual(None, context['HTTP_X_PROJECT_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_NAME'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual(None, context['HTTP_X_PROJECT_DOMAIN_NAME'])
        self.assertEqual(self.domain.id, context['HTTP_X_DOMAIN_ID'])
        self.assertEqual(self.domain.name, context['HTTP_X_DOMAIN_NAME'])
