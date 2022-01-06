# Pool-Pi
Pool-Pi is a system for interfacing with Goldline/Hayward pool control boards over WiFi via a Raspberry Pi. It adds wireless capabilities to non-wireless control boards and a web interface for viewing updates and sending commands. The web interface emulates a PS8-sized display (2x20 display, 6 AUX buttons), allowing for the same controls accessible from the physical unit.

## Demo
TODO add video

## Requirements
* Goldline/Hayward AquaLogic control board (tested on Main Software Revision 2.86)
* Raspberry Pi with Wifi (ex. Raspberry Pi Zero W)
* Adjustable DC-DC step down buck boost converter (ex. LM2596)
* TTL to RS485 adapter (ex. MAX485)
* Installation hardware:
    * Weatherproof junction box
    * Non metalic liquid tight flexible conduit
    * Concrete screws (ex. Tapcon)
    * Wire
* Tools:
    * Multimeter
    * Drill

## Installation
* Setup a Raspberry Pi headless with WiFi, a static IP, and SSH access.
* Connect DC-DC converter to pool control board and adjust to reduce input voltage (~10.7-11V) to 5V.
* Connect Raspberry Pi and RS485 adapter.
* Clone this repository to the Pi.
* Install requirements.
* Run python3 pool-pi.py
* From a device on the same network, navigate to your Pi's IP address on port 5000 (ex. 192.168.###.###:5000)

## Example Installation
TODO add images

## Troubleshooting
Comm Error can appear when multiple devices attempt to drive the serial bus simultaneously.
* Comm Error 1 is a startup error that occurs when the local display is unable to communicate with the main control board when it powers up. This could be due to the RS485 adapter being in transmit mode on startup, as seen with Comm Error 2. Unlike Comm Error 2, this error does not clear automatically when the serial lines are cleared. To clear the error, the local display must be disconnected and reconnected.
* Comm Error 2 occurs when multiple devices attempt to write to the serial bus simultaneously. Depending on the hardware configuration, this error might occur when the Pool-Pi is powered off due to the RS485's state when powered off. To fix this, ensure that the RS485 adaptr is set to receive when not transmitting.

## Acknowledgements
Special thanks to other people who have put their own resources/solutions for solving this problem online, including [draythomp](http://www.desert-home.com/), [swilson](https://github.com/swilson/aqualogic), and Pete Tompkins.

## Disclaimer
This project is not endorsed or affiliated with Goldline/Hayward in any way.