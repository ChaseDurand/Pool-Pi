DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")
#TODO figure out structure for mapping input command to expected confirmation command