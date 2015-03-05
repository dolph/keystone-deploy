# Deploy Keystone from source

This illustrates a deployment of [OpenStack
Keystone](http://keystone.openstack.org/) from
[source](https://github.com/openstack/keystone), primarily geared towards
testing recommended production configurations.

## Usage

### Using Vagrant

To run against a [Vagrant](http://www.vagrantup.com/) box, just run:

    vagrant up

When it's ready, you'll be able to use the vagrant box as an identity endpoint:

    http://192.168.111.222:35357/

Behind the scenes, Vagrant is just setting up a box to deploy to using Ansible.

### Using Ansible directly

Alternatively, copy the sample Ansible inventory file to create a custom
inventory, or with custom variables:

    cp sample_inventory inventory

And then you can deploy against an arbitrary inventory:

    ansible-playbook -i inventory --sudo deploy.yaml

Once the machine is running, you can also re-run individual playbooks against
it, for example:

    ansible-playbook -i inventory --sudo playbooks/sql.yaml

## Testing

This repository is divided into several feature branches, wherein each feature
branch demonstrates and tests a deployment variation. The `master` branch
represents a vanilla deployment. All feature branches should be regularly
rebased onto the master branch.

| Branch        | Status                                                                                                                               |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------|
| master        | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=master)](https://travis-ci.org/dolph/keystone-deploy)        |
| fernet-tokens | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=fernet-tokens)](https://travis-ci.org/dolph/keystone-deploy) |
| pki-tokens    | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=pki-tokens)](https://travis-ci.org/dolph/keystone-deploy)    |
| pkiz-tokens   | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=pkiz-tokens)](https://travis-ci.org/dolph/keystone-deploy)   |
| v3-only       | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=v3-only)](https://travis-ci.org/dolph/keystone-deploy)       |

To exercise a Vagrant deployment as created above, run:

    python -m unittest discover

To exercise a deployment on an arbitrary host, run:

    HOST=keystone.example.com python -m unittest discover
