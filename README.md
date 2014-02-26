Bootstrap a Debian Server
=========================

To bootstrap a Debian server (`HOSTNAME`, in this case), run:

    ./bootstrap.sh HOSTNAME

You can also bootstrap multiple servers in parallel by using ansible directly:

    ansible-playbook -i "HOSTNAME1,HOSTNAME2,HOSTNAME3," --user="root" bootstrap.yaml

Testing
-------

Bootstrap a vagrant box with:

    vagrant up

When it's ready, you'll be able to use the box:

    ssh 192.168.111.222
