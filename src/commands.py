MAX_SEND_ATTEMPTS = 10  # Max number of times command will be sent if not confirmed

DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

FRAME_TYPE_KEEPALIVE = b'\x01\x01'
FRAME_TYPE_LEDS = b'\x01\x02'
FRAME_TYPE_DISPLAY = b'\x01\x03'
FRAME_TYPE_LOCAL_TOGGLE = b'\x00\x02'
DISPLAY_AIRTEMP = 'Air Temp'.encode('utf-8')
DISPLAY_POOLTEMP = 'Pool Temp'.encode('utf-8')
DISPLAY_GASHEATER = 'Gas Heater'.encode('utf-8')
DISPLAY_CHLORINATOR_PERCENT = 'Pool Chlorinator'.encode('utf-8')
DISPLAY_CHLORINATOR_STATUS = 'Chlorinator'.encode('utf-8')
DISPLAY_SALT_LEVEL = 'Salt Level'.encode('utf-8')
DISPLAY_DATE = 'day'.encode('utf-8')
DISPLAY_CHECK = 'Check System'.encode('utf-8')
DISPLAY_VERY_LOW_SALT = 'Very Low Salt'.encode('utf-8')
DISPLAY_SPA_TEMP = 'Spa Temp'.encode('utf-8')

LED_MASK = [[(1 << 0, 'heater1'), (1 << 1, 'valve3'), (1 << 2, 'checksystem'),
             (1 << 3, 'pool'), (1 << 4, 'spa'), (1 << 5, 'filter'),
             (1 << 6, 'lights'), (1 << 7, 'aux1')],
            [(1 << 0, 'aux2'), (1 << 1, 'service'), (1 << 2, 'aux3'),
             (1 << 3, 'aux4'), (1 << 4, 'aux5'), (1 << 5, 'aux6'),
             (1 << 6, 'valve4'), (1 << 7, 'spillover')],
            [(1 << 0, 'systemoff'), (1 << 1, 'aux7'), (1 << 2, 'aux8'),
             (1 << 3, 'aux9'), (1 << 4, 'aux10'), (1 << 5, 'aux11'),
             (1 << 6, 'aux12'), (1 << 7, 'aux13')],
            [(1 << 0, 'aux14'), (1 << 1, 'superchlorinate')]]

button_toggle = {
    'service': b'\x08\x00\x00\x00',
    'pool': b'\x40\x00\x00\x00',
    'spa': b'\x40\x00\x00\x00',
    'spillover': b'\x40\x00\x00\x00',
    'filter': b'\x00\x80\x00\x00',
    'lights': b'\x00\x01\x00\x00',
    'heater1': b'\x00\x00\x04\x00',
    'valve3': b'\x00\x00\x01\x00',
    'valve4': b'\x00\x00\x02\x00',
    'aux1': b'\x00\x02\x00\x00',
    'aux2': b'\x00\x04\x00\x00',
    'aux3': b'\x00\x08\x00\x00',
    'aux4': b'\x00\x10\x00\x00',
    'aux5': b'\x00\x20\x00\x00',
    'aux6': b'\x00\x40\x00\x00',
    'aux7': b'\x00\x80\x00\x00',
    'aux8': b'\x00\x00\x08\x00',
    'aux9': b'\x00\x00\x10\x00',
    'aux10': b'\x00\x00\x20\x00',
    'aux11': b'\x00\x00\x40\x00',
    'aux12': b'\x00\x00\x80\x00',
    'aux13': b'\x00\x00\x00\x01',
    'aux14': b'\x00\x00\x00\x02',
    'systemoff': b'',
    'superchlorinate': b''
}

buttons_menu = {
    'left': b'\x04\x00\x00\x00',
    'right': b'\x01\x00\x00\x00',
    'plus': b'\x20\x00\x00\x00',
    'minus': b'\x10\x00\x00\x00',
    'menu': b'\x02\x00\x00\x00'
}