# Setup

## Requirements
* Goldline/Hayward Aqualogic control board (tested on Main Software Revision 2.86)
* Raspberry Pi with Wifi
* Adjustable DC-DC step down buck boost converter
* TTL to RS485 adapter
* Installation hardware:
    * Weatherproof junction box
    * Non metalic liquid tight flexible conduit
    * Concrete screws
    * Wire
* Tools:
    * Multimeter
    * Drill

Exact parts used can be found in the [parts list](./PARTS_LIST.md).

## Hardware setup
* Connect DC-DC converter to pool control board and adjust to reduce input voltage (~10.7-11V) to 5V.
* Connect Raspberry Pi and RS485 adapter.

## Software setup
* Setup a Raspberry Pi headless with WiFi, a static IP, and SSH access.
* Clone this repository to the Pi.
* Install requirements.
* Run python3 src/pool-pi.py
* From a device on the same network, navigate to your Pi's IP address on port 5000 (ex. 192.168.###.###:5000)
<!-- TODO configure GUI to match local aqualogic system -->

## Troubleshooting
Comm Error can appear when multiple devices attempt to drive the serial bus simultaneously.
* Comm Error 1 is a startup error that occurs when the local display is unable to communicate with the main control board when it powers up. This could be due to the RS485 adapter being in transmit mode on startup, as seen with Comm Error 2. Unlike Comm Error 2, this error does not clear automatically when the serial lines are cleared. To clear the error, the local display must be disconnected and reconnected.
* Comm Error 2 occurs when multiple devices attempt to write to the serial bus simultaneously. Depending on the hardware configuration, this error might occur when the Pool-Pi is powered off due to the RS485's state when powered off. To fix this, ensure that the RS485 adaptr is set to receive when not transmitting.