import os
import unittest

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

        domain = c.domains.get('default')

        role = c.roles.create(name='admin')
        self.addCleanup(c.roles.delete, role)

        group = c.groups.create(domain=domain, name='admin')
        self.addCleanup(c.groups.delete, group)

        c.roles.grant(group=group, domain=domain, role=role)
        self.addCleanup(c.roles.revoke, group=group, domain=domain, role=role)

        project = c.projects.create(domain=domain, name='admin')
        self.addCleanup(c.projects.delete, project)

        c.roles.grant(group=group, project=project, role=role)
        self.addCleanup(
            c.roles.revoke, group=group, project=project, role=role)

        password = 'password'
        user = c.users.create(
            domain=domain, name='admin', password=password)
        self.addCleanup(c.users.delete, user)

        c.users.add_to_group(user=user, group=group)

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
            username=user.name,
            password=password,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.unscoped.auth_token)

        self.project_scoped = client.Client(
            user_id=user.id,
            password=password,
            project_id=project.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.project_scoped.auth_token)

        self.domain_scoped = client.Client(
            user_id=user.id,
            password=password,
            domain_id=domain.id,
            auth_url=KEYSTONE_ENDPOINT + 'v3')
        self.assertTrue(self.domain_scoped.auth_token)

    def test_domain_list(self):
        self.assertEqual(1, len(self.domain_scoped.domains.list()))

    def test_unscoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.unscoped.auth_token})

        self.assertEqual(200, r.status_code)
        self.assertEqual('default', r.json()['HTTP_X_USER_DOMAIN_ID'])
        self.assertEqual('Default', r.json()['HTTP_X_USER_DOMAIN_NAME'])

    def test_project_scoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.project_scoped.auth_token})

        self.assertEqual(200, r.status_code)
        self.assertEqual('default', r.json()['HTTP_X_USER_DOMAIN_ID'])
        self.assertEqual('Default', r.json()['HTTP_X_USER_DOMAIN_NAME'])
        self.assertEqual('default', r.json()['HTTP_X_PROJECT_DOMAIN_ID'])
        self.assertEqual('Default', r.json()['HTTP_X_PROJECT_DOMAIN_NAME'])

    def test_domain_scoped_request(self):
        r = requests.get(
            ECHO_ENDPOINT,
            headers={'X-Auth-Token': self.domain_scoped.auth_token})

        self.assertEqual(200, r.status_code)
        self.assertEqual('default', r.json()['HTTP_X_USER_DOMAIN_ID'])
        self.assertEqual('Default', r.json()['HTTP_X_USER_DOMAIN_NAME'])
        self.assertEqual('default', r.json()['HTTP_X_DOMAIN_ID'])
        self.assertEqual('Default', r.json()['HTTP_X_DOMAIN_NAME'])
