from commands import *
from colorama import Fore, Style


def parseDisplay(data, poolModel):
    # Classify display update and pass to appropriate parser
    # Remove last bit (null)
    if data[-1] == 0:
        data = data[:-1]
    else:
        print(f'{Fore.RED}Display didn\'t end with null!{Style.RESET_ALL}')
        print(f'{Fore.RED}Display ended with: {Style.RESET_ALL}', data[-1])

    # Check characters for 7th bit for blinking
    poolModel.display_mask.clear()
    for i in range(len(data)):
        if (data[i] & 0b01111111) == data[i]:
            # Character is not blinking
            poolModel.display_mask.append('0')
        else:
            # Character is blinking
            data[i] = (data[i] & 0b01111111)
            poolModel.display_mask.append('1')

    data = data.replace(
        b'\x5f', b'\xc2\xb0')  #Degree symbol ° is encoded as underscore x5f

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
    print(poolModel.display)
    poolModel.flag_data_changed = True
    return


def parseDateTime(data, poolModel):
    previousDateTIme = poolModel.datetime
    newDateTime = data.decode('utf-8')
    if newDateTime != previousDateTIme:
        poolModel.flag_data_changed = True
        poolModel.datetime = newDateTime
    print('Date Time update:', end='')
    return


def parseAirTemp(data, poolModel):
    previousAirTemp = poolModel.airtemp
    try:
        newAirTemp = data.decode('utf-8').split()[2]
    except UnicodeDecodeError as e:
        print(e)
        print(data)
        newAirTemp = 'Error'
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
        newSaltLevel = 'Very Low Salt'
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
                    newState = 'BLINK'
                    print('     ', item[1], 'blink')
                else:
                    newState = 'ON'
                    print('     ', item[1], 'on')
            else:
                newState = 'OFF'
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
        print('Target: ', target_checksum)
        print('Caclulated: ', checksum)
        return False