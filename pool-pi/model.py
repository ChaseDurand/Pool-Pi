# Represents the state of the system
import json


class model:
    def __init__(self):
        self.display = "WAITING FOR DISPLAY"
        self.airtemp = "WAITING FOR AIRTEMP"
        self.pooltemp = "WAITING FOR POOLTEMP"
        self.datetime = "WAITING FOR DATETIME"
        self.salinity = "WAITING FOR SALINITY"
        self.waterfall = "INIT"

    def toJSON(self):
        return json.dumps(vars(self))