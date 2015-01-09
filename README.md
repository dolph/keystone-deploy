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

This repository is divided into several feature branches, wherein each feature
branch demonstrates and tests a deployment variation. The `master` branch
represents a vanilla deployment. All feature branches should be regularly
rebased onto the master branch.

| Branch  | Status                                                                                                                         |
|---------|--------------------------------------------------------------------------------------------------------------------------------|
| master  | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=master)](https://travis-ci.org/dolph/keystone-deploy)  |
| v3-only | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=v3-only)](https://travis-ci.org/dolph/keystone-deploy) |

To exercise a Vagrant deployment as created above, run:

    python -m unittest discover

To exercise a deployment on an arbitrary host, run:

    HOST=keystone.example.com python -m unittest discover
