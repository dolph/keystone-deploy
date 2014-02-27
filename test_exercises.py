import unittest

from keystoneclient.v3 import client


class TestCase(unittest.TestCase):
    def setUp(self):
        self.c = client.Client(
            token='ADMIN',
            endpoint='http://192.168.111.222:35357/v3')

    def test_default_domain(self):
        default_domain = self.c.domains.get('default')
        self.assertEqual('default', default_domain.id)
        self.assertEqual('Default', default_domain.name)
