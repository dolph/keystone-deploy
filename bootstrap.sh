#!/bin/bash
set -e
if [ $# -ne 1 ]; then
    echo "Usage: ./bootstrap.sh <hostname>"
    exit 1
fi
command -v ansible-playbook >/dev/null 2>&1 || { echo "Switch to a Python virtualenv with ansible installed (pip install ansible)."; exit 1; }
ssh-copy-id root@$1
ansible-playbook -i "$1," bootstrap.yaml
echo 'Done.'
