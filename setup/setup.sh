#!/bin/bash
parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P)
pushd "$parent_path"
echo "Setting up pool-pi."
echo "Creating venv."
pip3 install virtualenv
vertualenv .venv
echo "Installing required python packages."
pip3 install -r "$parent_path/requirements.txt"
echo "Configuring systemd."
cp "$parent_path/poolpi.service" /etc/systemd/system/poolpi.service
chmod 644 /etc/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable redis-server
systemctl enable --now poolpi.service
echo "Setup script complete"
popd
