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

# LEDs 1
LED_HEATER1 = 1 << 0
LED_VALVE3 = 1 << 1
LED_CHECKSYSTEM = 1 << 2
LED_POOL = 1 << 3
LED_SPA = 1 << 4
LED_FILTER = 1 << 5
LED_LIGHTS = 1 << 6
LED_AUX1 = 1 << 7
# LEDs 2
LED_AUX2 = 1 << 0
LED_SERVICE = 1 << 1
LED_AUX3 = 1 << 2
LED_AUX4 = 1 << 3
LED_AUX5 = 1 << 4
LED_AUX6 = 1 << 5
LED_VALVE4_HEATER2 = 1 << 6
LED_SPILLOVER = 1 << 7
# LEDs 3
LED_SYSTEMOFF = 1 << 0
LED_AUX7 = 1 << 1
LED_AUX8 = 1 << 2
LED_AUX9 = 1 << 3
LED_AUX10 = 1 << 4
LED_AUX11 = 1 << 5
LED_AUX12 = 1 << 6
LED_AUX13 = 1 << 7
# LEDs 4
LED_AUX14 = 1 << 0
LED_SUPERCHLORINATE = 1 << 1
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