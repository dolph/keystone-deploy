#!/bin/bash
set -e
for branch in eventlet fernet-tokens pki-tokens pkiz-tokens v3-only; do
    git checkout $branch && git rebase master && git push -f;
done
git checkout master;
