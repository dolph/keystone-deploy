# Deploy keystone from source

This illustrates a deployment of [OpenStack
keystone](http://keystone.openstack.org/) from
[source](https://github.com/openstack/keystone), primarily geared towards
documenting and testing various configurations.

## Usage

This repository is designed to deploy keystone to an arbitrary host using
ansible. You'll at least need `sudo` access on that host, if not `root`. This
repository is tested with Travis CI, so Ubuntu 12.04 is recommended.

Start by installing the project's dependencies:

    pip install -r requirements.txt

Copy the sample Ansible inventory file to create a custom inventory, where you
can specify your host and any custom variables:

    cp sample_inventory inventory

Next, install ansible dependencies:

    ansible-galaxy install --roles-path=playbooks/roles/ --role-file=ansible-requirements.txt

And then you can deploy keystone:

    ansible-playbook -i inventory deploy.yaml

Note that you might need to specify how ansible should authenticate with the
host, and how to obtain root permissions. See `ansible-playbook --help` for
the available options.

## Testing

This repository is divided into several feature branches, wherein each feature
branch demonstrates and tests a deployment variation. The `master` branch
represents a vanilla deployment. All feature branches should be regularly
rebased onto the master branch.

| Branch        | Status                                                                                                                               |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------|
| master        | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=master)](https://travis-ci.org/dolph/keystone-deploy)        |
| eventlet      | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=eventlet)](https://travis-ci.org/dolph/keystone-deploy)      |
| fernet-tokens | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=fernet-tokens)](https://travis-ci.org/dolph/keystone-deploy) |
| pki-tokens    | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=pki-tokens)](https://travis-ci.org/dolph/keystone-deploy)    |
| pkiz-tokens   | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=pkiz-tokens)](https://travis-ci.org/dolph/keystone-deploy)   |
| v3-only       | [![Build Status](https://travis-ci.org/dolph/keystone-deploy.svg?branch=v3-only)](https://travis-ci.org/dolph/keystone-deploy)       |

To exercise a deployment, run:

    HOST=keystone.example.com python -m unittest discover

## Documentation

The primary goal of this repository is to provide working, tested configuration
documentation, which happens to be in the form of ansible plays.

To see documentation on how to switch from UUID-tokens to fernet-tokens, for
example, use `git diff`:

    git diff master fernet-tokens

To switch from PKI tokens to PKIZ tokens:

    git diff pki-tokens pkiz-tokens

To disable the Identity API v2 in favor of running v3 only:

    git diff master v3-only
