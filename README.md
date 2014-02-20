Bootstrap a Debian Server
=========================

To bootstrap a Debian server (`HOSTNAME`, in this case), run:

    ansible-playbook -i "HOSTNAME," bootstrap.yaml

Note the trailing comma, which is required. You can also bootstrap multiple
servers in parallel with:

    ansible-playbook -i "HOSTNAME1,HOSTNAME2,HOSTNAME3," bootstrap.yaml
