from commands import *
import logging


def parseDisplay(data, poolModel):
    # Remove last bit (null)
    if data[-1] == 0:
        data = data[:-1]
    else:
        logging.error(f"Display data did\t end with null: {data}")
    # Check characters for 7th bit for blinking
    poolModel.display_mask.clear()
    for i in range(len(data)):
        if (data[i] & 0b01111111) == data[i]:
            # Character is not blinking
            poolModel.display_mask.append("0")
        else:
            # Character is blinking
            data[i] = data[i] & 0b01111111
            poolModel.display_mask.append("1")
    data = data.replace(
        b"\x5f", b"\xc2\xb0"
    )  # Degree symbol ° is encoded as underscore x5f
    try:
        poolModel.display = data.decode("utf-8")
    except (UnicodeDecodeError, Exception) as e:
        logging.error(f"Error while decoding display update {data}: {e}")
    logging.info(f"Display: {poolModel.display}")
    poolModel.flag_data_changed = True
    return


def parseLEDs(data, poolModel):
    poolModel.updateTimestamp()  # Record when we recieved this LED update
    ledsON = []
    ledsBLINK = []
    # Look at corrosponding LED bit flags to determine which LEDs are on
    for i in range(0, 4):
        for item in LED_MASK[i]:
            if item[0] & data[i]:
                # LED is either on or blinking
                if item[0] & data[i + 4]:
                    newState = "BLINK"
                    ledsBLINK.append(item[1])
                else:
                    newState = "ON"
                    ledsON.append(item[1])
            else:
                newState = "OFF"
            if poolModel.getParameterState(item[1]) != newState:
                poolModel.updateParameter(item[1], newState)
                poolModel.flag_data_changed = (
                    True  # Raise flag if any model parameter has changed
                )
    if len(ledsBLINK) == 0:
        logging.info(f"LED update: {ledsON} on.")
    else:
        logging.info(f"LED update: {ledsON} on and {ledsBLINK} blinking.")
    return


def confirmChecksum(message):
    """
    Check if the calculated checksum for messages equals the expected sent checksum
    Return True if checksums match, False if not
    Checksum is 4th and 3rd to last bytes of command (last bytes prior to DLE ETX)
    Checksum includes start DLE STX, frame type, and data
    """
    target_checksum = int.from_bytes(
        message[-4:-2], byteorder="big"
    )  # Convert two byte checksum to single value
    checksum = 0
    for i in message[:-4]:
        checksum += i
    if checksum == target_checksum:
        return True
    else:
        logging.error(
            f"Checksum mismatch: Target {target_checksum}, calculated {checksum}."
        )
        return False
