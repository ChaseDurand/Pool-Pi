#!/bin/bash
echo "Setting up pool-pi."
echo "Installing required python packages."
pip3 install -r /home/pi/Pool-Pi/setup/requirements.txt
echo "Configuring systemd."
mv /home/pi/Pool-Pi/setup/poolpi.service /lib/systemd/system/poolpi.service
chmod 644 /lib/systemd/system/poolpi.service
systemctl daemon-reload
systemctl enable myscript.service
echo "Setup complete."
echo "Rebooting in 10 seconds."
sleep 10
reboot