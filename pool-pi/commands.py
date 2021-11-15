DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")
NON_KEEP_ALIVE = ('', '')
#TODO figure out structure for mapping input command to expected confirmation command

FRAME_UPDATE_LEDS = (b'\x01\x02', "FRAME_UPDATE_LEDS")
FRAME_UPDATE_DISPLAY = (b'\x01\x03', "FRAME_UPDATE_DISPLAY")
DISPLAY_AIRTEMP = (b'\x41\x69\x72\x20\x54\x65\x6D\x70')  #'Air Temp'
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