DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")
NON_KEEP_ALIVE = ('', '')
#TODO figure out structure for mapping input command to expected confirmation command

FRAME_UPDATE_LEDS = (b'\x01\x03', "FRAME_UPDATE_LEDS")
FRAME_UPDATE_DISPLAY = (b'\x01\x04', "FRAME_UPDATE_DISPLAY")