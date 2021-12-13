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
DISPLAY_VERY_LOW_SALT = 'Very Low Salt'.encode('utf-8')

AUX4 = b'\x10\x02\x00\x02\x00\x10\x00\x00\x00\x00\x10\x00\x00\x00\x00\x34\x10\x03'

LED = [[(1 << 0, 'heater1'), (1 << 1, 'valve3'), (1 << 2, 'checkSystem'),
        (1 << 3, 'pool'), (1 << 4, 'spa'), (1 << 5, 'filter'),
        (1 << 6, 'lights'), (1 << 7, 'aux1')],
       [(1 << 0, 'aux2'), (1 << 1, 'service'), (1 << 2, 'aux3'),
        (1 << 3, 'aux4'), (1 << 4, 'aux5'), (1 << 5, 'aux6'),
        (1 << 6, 'valve4'), (1 << 7, 'spillover')],
       [(1 << 0, 'systemOff'), (1 << 1, 'aux7'), (1 << 2, 'aux8'),
        (1 << 3, 'AUX 9'), (1 << 4, 'aux10'), (1 << 5, 'aux11'),
        (1 << 6, 'aux12'), (1 << 7, 'aux13')],
       [(1 << 0, 'aux14'), (1 << 1, 'superChlorinate')]]
