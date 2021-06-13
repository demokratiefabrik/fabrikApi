#!/usr/bin/env bash
#
# PREPARE DOCKER SECRETS (Workaround, since we are not in swarm mode)
# remove symbolic link => create real directory
rm -Rf /var/run
mkdir /var/run
cp -R /run/secrets /var/run/secrets
chmod -Rf 555 /var/run/secrets
#
# RUN gunicorn
(python setup.py develop; gunicorn --paste production.ini  --user www-data --bind 0.0.0.0:8020 --timeout 60 --workers 8 ./fabrikApi)
