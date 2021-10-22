import binascii

DLE = binascii.unhexlify('10')
STX = binascii.unhexlify('02')
ETX = binascii.unhexlify('03')

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")