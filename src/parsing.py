LED_MASK = [[(1 << 0, 'heater1'), (1 << 1, 'valve3'), (1 << 2, 'checkSystem'),
             (1 << 3, 'pool'), (1 << 4, 'spa'), (1 << 5, 'filter'),
             (1 << 6, 'lights'), (1 << 7, 'aux1')],
            [(1 << 0, 'aux2'), (1 << 1, 'service'), (1 << 2, 'aux3'),
             (1 << 3, 'aux4'), (1 << 4, 'aux5'), (1 << 5, 'aux6'),
             (1 << 6, 'valve4'), (1 << 7, 'spillover')],
            [(1 << 0, 'systemOff'), (1 << 1, 'aux7'), (1 << 2, 'aux8'),
             (1 << 3, 'aux9'), (1 << 4, 'aux10'), (1 << 5, 'aux11'),
             (1 << 6, 'aux12'), (1 << 7, 'aux13')],
            [(1 << 0, 'aux14'), (1 << 1, 'superChlorinate')]]

FRAME_TYPE_KEEPALIVE = b'\x01\x01'
FRAME_TYPE_LEDS = b'\x01\x02'
FRAME_TYPE_DISPLAY = b'\x01\x03'
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

DLE = b'\x10'
STX = b'\x02'
ETX = b'\x03'

KEEP_ALIVE = (b'\x10\x02\x01\x01\x00\x14\x10\x03', "Keep Alive")


def parseDisplay(data, poolModel):
    # Classify display update and pass to appropriate parser
    data = data.replace(
        b'\x5f', b'\xc2\xb0')  #Degree symbol ° is encoded as underscore x5f
    data = data.replace(b'\xba', b'\x3a')  # Colon : is encoded as xBA
    if DISPLAY_AIRTEMP in data:
        parseAirTemp(data, poolModel)
    elif DISPLAY_POOLTEMP in data:
        parsePoolTemp(data, poolModel)
    elif DISPLAY_GASHEATER in data:
        print('Gas Heater update:', end='')
    elif DISPLAY_CHLORINATOR_PERCENT in data:
        print('Chlorinator Percent update:', end='')
    elif DISPLAY_CHLORINATOR_STATUS in data:
        print('Chlorinator Status update:', end='')
    elif DISPLAY_DATE in data:
        parseDateTime(data, poolModel)
    elif DISPLAY_CHECK in data:
        if DISPLAY_VERY_LOW_SALT in data:
            parseSalinity(data, poolModel)
        else:
            print('Check System update', end='')
    elif DISPLAY_SALT_LEVEL in data:
        parseSalinity(data, poolModel)
    elif DISPLAY_SPA_TEMP in data:
        print('Spa Temp update', end='')
    else:
        print('Unclassified display update', end='')
    try:
        poolModel.display = data.decode('utf-8')
    except (UnicodeDecodeError, Exception) as e:
        print(e)
        print(data)
    poolModel.flag_data_changed = True
    print(poolModel.display)
    return


def parseDateTime(data, poolModel):
    previousDateTIme = poolModel.datetime
    newDateTime = data.replace(b'\xba',
                               b'\x3a').decode('utf-8')  #: is encoded as xBA
    if newDateTime != previousDateTIme:
        poolModel.flag_data_changed = True
        poolModel.datetime = newDateTime
    print('Date Time update:', end='')
    return


def parseAirTemp(data, poolModel):
    previousAirTemp = poolModel.airtemp
    try:
        newAirTemp = data.decode('utf-8').split(
        )[2]  #TODO fix unknown error UnicodeDecodeError: 'utf-8' codec can't decode byte 0xdf in position 13: invalid continuation byte
    except UnicodeDecodeError as e:
        print(e)
        print(data)
        newAirTemp = "Error"
    if newAirTemp != previousAirTemp:
        poolModel.flag_data_changed = True
        poolModel.airtemp = newAirTemp
    print('Air Temp update:', end='')
    return


def parsePoolTemp(data, poolModel):
    previousPoolTemp = poolModel.pooltemp
    newPoolTemp = data.decode('utf-8').split()[2]
    if newPoolTemp != previousPoolTemp:
        poolModel.flag_data_changed = True
        poolModel.pooltemp = newPoolTemp
    print('Pool Temp update:', end='')
    return


def parseSalinity(data, poolModel):
    previousSaltLevel = poolModel.salinity
    if DISPLAY_VERY_LOW_SALT in data:
        newSaltLevel = "Very Low Salt"
    else:
        newSaltLevel = data.decode('utf-8').split()[-3]
    if newSaltLevel != previousSaltLevel:
        poolModel.flag_data_changed = True
        poolModel.salinity = newSaltLevel
    print('Salt Level update:', end='')
    return


def parseLEDs(data, poolModel):
    poolModel.updateTime()  # Record when we recieved this LED update
    print('LED update:')
    #Look at corrosponding LED bit flags to determine which LEDs are on
    for i in range(0, 4):
        for item in LED_MASK[i]:
            if item[0] & data[i]:
                #LED is either on or blinking
                if item[0] & data[i + 4]:
                    newState = "BLINK"
                    print('     ', item[1], 'blink')
                else:
                    newState = "ON"
                    print('     ', item[1], 'on')
            else:
                newState = "OFF"
            if poolModel.getParameterState(item[1]) != newState:
                poolModel.updateParameter(item[1], newState)
                poolModel.flag_data_changed = True  # Raise flag if any model parameter has changed
    return


def confirmChecksum(message):
    # Check if the calculated checksum for messages equals the expected sent checksum
    # Return True if checksums match, False if not
    # Checksum is 4th and 3rd to last bytes of command (last bytes prior to DLE ETX)
    # Checksum includes start DLE STX, frame type, and data
    target_checksum = int.from_bytes(
        message[-4:-2],
        byteorder='big')  # Convert two byte checksum to single value
    checksum = 0
    for i in message[:-4]:
        checksum += i
    if checksum == target_checksum:
        return True
    else:
        print("Target: ", target_checksum)
        print("Caclulated: ", checksum)
        return False