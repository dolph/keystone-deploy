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

Alternatively, to deploy on an existing machine:

    ansible-playbook -i "root@example.com," deploy.yaml

When it's ready, you'll be able to use the vagrant box as an identity endpoint:

    http://192.168.111.222:35357/

Once the machine is running, you can also re-run individual playbooks against
it, for example:

    ansible-playbook -i "vagrant@192.168.111.222," --sudo playbooks/sql.yaml

Testing
-------

[![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=master)](https://travis-ci.org/dolph/keystone-deploy)

To exercise the Vagrant deployment, run:

    python -m unittest discover
