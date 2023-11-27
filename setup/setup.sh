#!/bin/bash
sudo -u $SUDO_UID BASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"; cd .. ; pwd -P)
sudo -u $SUDO_UID echo "Setting up pool-pi."
sudo -u $SUDO_UID echo "Creating venv."
sudo -u $SUDO_UID pip3 install virtualenv
sudo -u $SUDO_UID virtualenv ${BASEDIR}"/src/.venv"
sudo -u $SUDO_UID source ${BASEDIR}"/src/.venv/bin/activate"
sudo -u $SUDO_UID echo "Installing required python packages."
sudo -u $SUDO_UID pip3 install -r ${BASEDIR}/setup/requirements.txt
sudo -u $SUDO_UID echo "Configuring systemd."
cp ${BASEDIR}/setup/poolpi.service /etc/systemd/system/poolpi.service
chmod 644 /etc/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable redis-server
systemctl enable --now poolpi.service
sudo -u $SUDO_UID echo "Setup script complete."