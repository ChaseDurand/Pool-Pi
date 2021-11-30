import json


# Represents the state of the system
class model:
    display = "foo"
    salinity = "bar"

    # air_temp = 0
    # pool_temp = 0
    # degrees_F = True
    # gas_heater_status = False
    # chlorinator_status = False
    # day = "Nullday"
    # time = ""

    def toJSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)


# Display

# Salinity
# Air Temp
# Pool Temp
# Gas Heater Status
# Chlorinator Status
# Day
# Time

# LEDs