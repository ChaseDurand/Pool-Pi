# <img width='24' alt='Logo icon' src='src/static/favicon.ico'> Pool-Pi

Pool-Pi is a hardware+software system for interfacing with Goldline/Hayward Aqualogic pool control boards over WiFi via a Raspberry Pi. It adds wireless capabilities to non-wireless control boards and a web interface for viewing updates and sending commands.

<p align='center'>
    <img width=80% alt='GUI screenshot' src='docs/media/gui_1.png'>
    <img width=80% alt='GUI screenshot' src='docs/media/install_2.jpg'>
</p>


## Demo Video
This video shows multiple clients interfacing with the unit and demonstrates display updates, button presses, menu controls, blinking display characters, and LED updates.

https://user-images.githubusercontent.com/50851884/149863222-32523871-b4b8-4c59-9fa8-fe185a0315eb.mov


## Overview
<p align='center'>
<img width=90% alt='Diagram' src='docs/media/diagramv1.png'>
</p>

Pool-Pi provides a web interface which emulates a local PS-8 display, allowing for the same controls accessible from the physical unit. The serial bus exposes all 14 aux relays regardless of local display, so emulation of a PS-16 display is possible, allowing additional relays to be added without purchasing a larger local interface. An RS485 adapter is used to read and send messages in accordance with the [Aqualogic serial communication protocol](/docs/PROTOCOL_NOTES.md), mimicking an OEM device. The system also adds logging, which is unavailable on the OEM unit. A simplified GUI is available to show the most frequently used commands.
<p align='center'>
<img width=80% alt='GUI screenshot' src='docs/media/gui_2.png'>
</p>


## Setup
Project requirements and instructions can be found in [docs/SETUP.md](/docs/SETUP.md).

## Acknowledgements
Thank you to other people who have put their own resources/solutions for solving this problem online, including [draythomp](http://www.desert-home.com/), [swilson](https://github.com/swilson/aqualogic), and Pete Tompkins.

## Disclaimer
This project is not endorsed or affiliated with Goldline/Hayward in any way.
