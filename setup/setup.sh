#!/bin/bash
# This assumes setup.sh is located in */Pool-Pi/setup
BASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"; cd .. ; pwd -P)
echo "Setting up pool-pi."
echo "Creating venv."
pip3 install virtualenv
virtualenv ${BASEDIR}"/src/.venv"
source ${BASEDIR}"/src/.venv/bin/activate"
echo "Installing required python packages."
pip3 install -r /home/pi/Pool-Pi/setup/requirements.txt
echo "Configuring systemd."
cp /home/pi/Pool-Pi/setup/poolpi.service /etc/systemd/system/poolpi.service
chmod 644 /etc/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable redis-server
systemctl enable --now poolpi.service
echo "Setup script complete."