#!/bin/bash
set -e

if [ -z "${SUDO_USER}" ]; then
    echo 'Run with sudo/root!'
    exit 1
fi

if [ -z "$(groups $SUDO_USER | grep sudo)" ]; then
    echo 'User ${SUDO_USER} is not in sudo group!'
    exit 1
fi

export BASEDIR=$(dirname $(dirname "$(realpath $0)"))

sudo -u $SUDO_USER echo "Setting up pool-pi."

sudo -u $SUDO_USER echo "Installing venv."
apt install python3-venv

sudo -u $SUDO_USER echo "Creating venv."
sudo -u $SUDO_USER -E -H python3 -m venv ${BASEDIR}"/src/.venv"

sudo -u $SUDO_USER echo "Installing requirements."
sudo -u $SUDO_USER -E -H bash -c 'source ${BASEDIR}"/src/.venv/bin/activate" && pip3 install -r ${BASEDIR}/setup/requirements.txt'

sudo -u $SUDO_USER echo "Configuring systemd."
cp ${BASEDIR}/setup/poolpi.service /etc/systemd/system/poolpi.service
chmod 644 /etc/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable redis-server
systemctl enable --now poolpi.service

sudo -u $SUDO_USER echo "Setup script complete."
exit 0
