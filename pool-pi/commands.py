DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")
NON_KEEP_ALIVE = ('', '')
#TODO figure out structure for mapping input command to expected confirmation command

FRAME_UPDATE_LEDS = (b'\x01\x02', "FRAME_UPDATE_LEDS")
FRAME_UPDATE_DISPLAY = (b'\x01\x03', "FRAME_UPDATE_DISPLAY")
DISPLAY_AIRTEMP = 'Air Temp'.encode('utf-8')
DISPLAY_POOLTEMP = 'Pool Temp'.encode('utf-8')
DISPLAY_GASHEATER = 'Gas Heater'.encode('utf-8')
DISPLAY_CHLORINATOR_PERCENT = 'Pool Chlorinator'.encode('utf-8')
DISPLAY_CHLORINATOR_STATUS = 'Chlorinator'.encode('utf-8')
DISPLAY_SALT_LEVEL = 'Salt Level'.encode('utf-8')
DISPLAY_DATE = 'day'.encode('utf-8')
DISPLAY_CHECK = 'Check System'.encode('utf-8')

LED_1 = [(1 << 0, 'Heater 1'), (1 << 1, 'Valve 3'), (1 << 2, 'Check System'),
         (1 << 3, 'Pool'), (1 << 4, 'Spa'), (1 << 5, 'Filter'),
         (1 << 6, 'Lights'), (1 << 7, 'AUX 1')]
LED_2 = [(1 << 0, 'AUX 2'), (1 << 1, 'Service'), (1 << 2, 'AUX 3'),
         (1 << 3, 'AUX 4'), (1 << 4, 'AUX 5'), (1 << 5, 'AUX 6'),
         (1 << 6, 'Valve 4 / Heater 2'), (1 << 7, 'Spillover')]
LED_3 = [(1 << 0, 'System Off'), (1 << 1, 'Aux 7'), (1 << 2, 'AUX 8'),
         (1 << 3, 'AUX 9'), (1 << 4, 'AUX 10'), (1 << 5, 'AUX 11'),
         (1 << 6, 'AUX 12'), (1 << 7, 'AUX 13')]
LED_4 = [(1 << 0, 'AUX 14'), (1 << 1, 'Super Chlorinate')]
'''
regular display updates:
Gas heater status
Pool temp
Air temp
Chlorinator percent
Chlorinator status
Day time
Inspect cell
'''