Deploy Keystone from source
===========================

This illustrates a deployment of [OpenStack
Keystone](http://keystone.openstack.org/) from
[source](https://github.com/openstack/keystone), primarily geared towards
testing recommended production configurations.

Usage
-----

To run against a [Vagrant](http://www.vagrantup.com/) box, just run:

    vagrant up

When it's ready, you'll be able to use the vagrant box as an identity endpoint:

    http://192.168.111.222:35357/

Once the vagrant box is up, you can also run individual playbooks against it,
for example:

    ansible-playbook -i "vagrant@192.168.111.222," --sudo playbooks/sql.yaml
