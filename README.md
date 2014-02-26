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
