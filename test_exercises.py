import unittest

from keystoneclient.v3 import client


class TestCase(unittest.TestCase):
    def setUp(self):
        c = client.Client(
            token='ADMIN',
            endpoint='http://192.168.111.222:35357/v3')

        domain = c.domains.get('default')

        role = c.roles.create(name='admin')
        self.addCleanup(c.roles.delete, role)

        group = c.groups.create(domain=domain, name='admin')
        self.addCleanup(c.groups.delete, group)

        password = 'password'
        user = c.users.create(
            domain=domain, name='admin', password=password)
        self.addCleanup(c.users.delete, user)

        c.roles.grant(user=user, domain=domain, role=role)
        self.addCleanup(c.roles.revoke, user=user, domain=domain, role=role)

        service = c.services.create(
            name='Keystone', type='identity')
        self.addCleanup(c.services.delete, service)

        public_endpoint = c.endpoints.create(
            service=service,
            interface='public',
            url='http://192.168.111.222:35357/v3')
        self.addCleanup(c.endpoints.delete, public_endpoint)
        admin_endpoint = c.endpoints.create(
            service=service,
            interface='admin',
            url='http://192.168.111.222:35357/v3')
        self.addCleanup(c.endpoints.delete, admin_endpoint)

        self.c = client.Client(
            username=user.name,
            password=password,
            auth_url='http://192.168.111.222:35357/v3')

        self.c = client.Client(
            user_id=user.id,
            password=password,
            domain_id=domain.id,
            auth_url='http://192.168.111.222:35357/v3')

    def test_domain_list(self):
        self.assertEqual(1, len(self.c.domains.list()))
