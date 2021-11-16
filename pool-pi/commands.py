DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")
NON_KEEP_ALIVE = ('', '')
#TODO figure out structure for mapping input command to expected confirmation command

FRAME_UPDATE_LEDS = (b'\x01\x02', "FRAME_UPDATE_LEDS")
FRAME_UPDATE_DISPLAY = (b'\x01\x03', "FRAME_UPDATE_DISPLAY")
# DISPLAY_AIRTEMP = (b'\x41\x69\x72\x20\x54\x65\x6D\x70')  #'Air Temp'
DISPLAY_AIRTEMP = 'Air Temp'.encode('utf-8')
DISPLAY_POOLTEMP = (b'\x50\x6F\x6F\x6C\x20\x54\x65\x6D\x70')  #'Pool Temp'
DISPLAY_GASHEATER = (b'\x47\x61\x73\x20\x48\x65\x61\x74\x65\x72'
                     )  #'Gas Heater'
DISPLAY_CHLORINATOR_PERCENT = (
    b'\x50\x6F\x6F\x6C\x20\x43\x68\x6C\x6F\x72\x69\x6E\x61\x74\x6F\x72'
)  #'Pool Chlorinator'
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