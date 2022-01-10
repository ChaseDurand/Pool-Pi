# Aqualogic RS485 Protocol Notes

The RS485 protocol that the Aqualogic board uses is not fully documented. The most official information can be found in the manual for the AQ-CO-SERIAL, a device designed to interface between a Prologic/Aqualogic unit and a home automation system by converting RS485 messages to RS232. However, the AQ-CO-SERIAL strips some messages from the serial bus, slightly modifies some commands, and handles response timing to the master unit, so a substitute must handle all messages and timing.

The serial bus is used to communicate between the Aqualogic board, the local display, and any additional devices (wired controllers, spa controllers, wireless adapters such as the GLX-BASE-RF). All devices on the bus are connected in parallel.

The protocol use 1 start bit, 8 data bits, no parity, and 2 stop bits with a baud rate of 19.2k.

Frames are structured with DLE STX (x10x02), two bytes indicating the command/frame type, multiple data bytes, a two byte checksum, and DLE ETX (x10x03). The two byte checksum includes all bytes before the checksum (excluding DLE STX). If any byte besides the start and end DLE (x10) are equal to x10, a NULL (x00) is inserted immediately after that byte. This NULL must be removed when parsing frames.

| Start | Frame Type | Command/Data | Checksum | End |
| :---: | :---:| :---: | :---: | :---: |
| x10x02 | <2 bytes> | <0-? bytes> | <2 bytes> | x10x03 |

## Aqualogic to Controller
The Aqualogic board acts as a master unit providing a heartbeat/keep alive packet, screen updates, and LED updates.

A keep alive frame is sent every 100ms with a frame type of x01x01 and zero data bytes. If any serial device has a message to send, it must respond immediately after the keep alive frame. OEM devices begin responding 0.5ms after the end of the keep alive frame.

Keep alive frame: x10x02x01x01x00x14x10x03

Screen updates have the frame type x01x03. Different devices have different screen sizes (2 by 16 instead of 2 by 20). I do not know if different display packets are sent, or if the local displays parse frames differently to accomodate different screen sizes. There might be a handshake between the Aqualogic and any connected devices on startup to communicate screen size and software versions (which could also explain Communication Err 1).

For display updates that show time, the colon : (x3A) is encoded as xBA and must be replaced.

For display updates that show temperature, the degree symbol ° is encoded as an underscore (x5F) and must be replaced with xC2xB0.

LED updates have the frame type x01x02. The first 4 bytes indicate on/off, and the second 4 bytes indicate blinking (if the corresponding on/off bit is also on). Within the bytes, a single bit corresponds to a specific LED.

| Start | Frame Type | LEDs1 | LEDs2 | LEDs3 | LEDs4 | Blink LEDs1 | Blink LEDs2 | Blink LEDs3 | Blink LEDs4 | Checksum | End |
| :---: | :---:| :---: | :---: | :---: | :---: | :---: | :---:| :---: | :---: | :---: | :---: |
| x10x02 | x01x02 | <1 byte> | <1 byte> | <1 byte> | <1 byte> | <1 byte> | <1 byte> | <1 byte> | <1 byte> | <2 bytes> | x10x03 |

The bit mask for each LED is shown below. The order of the LEDs is unintuitive because it reflects the evolution of the platform and its capabilities (AQL-P-4 to PS-8 to PS-16, each adding more parameters):

Example LED frame with Pool, Filter, and Aux4 On: x10x02x01x02x28x08x00x00x00x00x00x00x00x45x10x03

| Byte | Bit | Mask | LED |
| :---: | :---:| :---: | :--- |
| LEDs1 | 0 | 1<<0 | Heater1 |
| LEDs1 | 1 | 1<<1 | Valve3 |
| LEDs1 | 2 | 1<<2 | Check System |
| LEDs1 | 3 | 1<<3 | Pool |
| LEDs1 | 4 | 1<<4 | Spa |
| LEDs1 | 5 | 1<<5 | Filter |
| LEDs1 | 6 | 1<<6 | Lights |
| LEDs2 | 7 | 1<<7 | Aux1 |
| LEDs2 | 0 | 1<<0 | Aux2 |
| LEDs2 | 1 | 1<<1 | Service |
| LEDs2 | 2 | 1<<2 | Aux3 |
| LEDs2 | 3 | 1<<3 | Aux4 |
| LEDs2 | 4 | 1<<4 | Aux5 |
| LEDs2 | 5 | 1<<5 | Aux6 |
| LEDs2 | 6 | 1<<6 | Valve4/Heater2 |
| LEDs2 | 7 | 1<<7 | Spillover |
| LEDs3 | 0 | 1<<0 | System Off |
| LEDs3 | 1 | 1<<1 | Aux7 |
| LEDs3 | 2 | 1<<2 | Aux8 |
| LEDs3 | 3 | 1<<3 | Aux9 |
| LEDs3 | 4 | 1<<4 | Aux10 |
| LEDs3 | 5 | 1<<5 | Aux11 |
| LEDs3 | 6 | 1<<6 | Aux12 |
| LEDs3 | 7 | 1<<7 | Aux13 |
| LEDs4 | 0 | 1<<0 | Aux14 |
| LEDs4 | 1 | 1<<1 | Super Chlorinate |
| LEDs4 | 2 | 1<<2 | (unused) |
| LEDs4 | 3 | 1<<3 | (unused) |
| LEDs4 | 4 | 1<<4 | (unused) |
| LEDs4 | 5 | 1<<5 | (unused) |
| LEDs4 | 6 | 1<<6 | (unused) |
| LEDs4 | 7 | 1<<7 | (unused) |

## Controller to Aqualogic
Even though the PS-4/8/16 remotes know the state of the pool system through LED messages, all commands from this series act as toggle switches and are independent of the current state. There are no separate on/off commands for this series of remotes. The frame type from a local PS-8 is x00x02.

Example Aux 1 button toggle frame: x10x02x00x02x00x02x00x00x00x02x00x00x00x1Cx10x03. If Aux 1 is off, this will turn it on. If Aux 1 is on, this will turn it off.

| Function           | Command                                |
| :---               | :---                                   |
| Service            | x08x00x00x00                           |
| Pool/Spa/Spillover | x40x00x00x00                           |
| Filter             | x00x80x00x00                           |
| Lights             | x00x01x00x00                           |
| Heater1            | x00x00x04x00                           |
| Valve3             | x00x00x01x00                           |
| Aux1               | x00x02x00x00                           |
| Aux2               | x00x04x00x00                           |
| Aux3               | x00x08x00x00                           |
| Aux4               | x00x10x00x00<sup>[1](#footnote1)</sup> |
| Aux5               | x00x20x00x00                           |
| Aux6               | x00x40x00x00                           |
<!-- TODO add remaining commands -->

## Variable Speed Pump Control
Aqualogic supports Hayward variable speed pumps that send their own frame type with speed and power information. I don't have a Hawyard VSP, so I am not able to implement support.

## Bonus On/Off Commands
While commands from the PS-4/8/16 series are the same for on/off, older controllers such as the AQL-SS-RF and AQL-P-4 use slightly modified commands with separate on/off capabilities. The frame type is x00x05. The commands are repeated twice and end with x7F before the checksum. While using these commands would make programming far easier, these on/off commands only cover a subset of the PS-4/8/16 controls. Because my setup involves commands outside of this subset and I achieved high reliability with only the toggle commands, I did not implement them.

Example Aux 2 On frame: x10x02x00x05x08x00x08x00x7Fx00xA6x10x03. If Aux 2 is off, this will turn it on. If Aux 2 is already on, this has no effect.

| Function   | Command                          |
| :---       | :---                             |
| Heater On  | x01x00                           |
| Heater Off | x00x01                           |
| Filter On  | x02x00                           |
| Filter Off | x00x02                           |
| Pool On    | x04x00                           |
| Spa On     | x00x04                           |
| Aux 2 On   | x08x00                           |
| Aux 2 Off  | x00x08                           |
| Aux 1 On   | x10x00<sup>[1](#footnote1)</sup> |
| Aux 1 Off  | x00x10<sup>[1](#footnote1)</sup> |
| Light On   | x20x00                           |
| Light Off  | x00x20                           |







<a name="footnote1">1</a>: An extra x00 must be inserted after x10, not shown here