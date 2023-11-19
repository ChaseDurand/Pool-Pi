#!/bin/bash
echo "Setting up pool-pi."
echo "Creating venv."
pip3 install virtualenv
vertualenv .venv
echo "Installing required python packages."
pip3 install -r /home/pi/Pool-Pi/setup/requirements.txt
echo "Configuring systemd."
cp /home/pi/Pool-Pi/setup/poolpi.service /etc/systemd/system/poolpi.service
chmod 644 /etc/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable redis-server
systemctl enable --now poolpi.service
echo "Setup script complete."