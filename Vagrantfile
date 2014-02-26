# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "wheezy64"
  config.vm.box_url = "http://925d6bfd5e1189ef9e46-7f075c191524c4ac73c453596e6e8394.r48.cf1.rackcdn.com/wheezy64-debian-7.4.0-amd64.box"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network :private_network, ip: "192.168.111.222"

  # Ansible provisioning
  config.vm.provision :ansible do |ansible|
    ansible.playbook = "bootstrap.yaml"
    ansible.sudo = true
  end
end
