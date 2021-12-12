# Represents the state of the system


class model:
    def __init__(self):
        self.display = "WAITING FOR DISPLAY"
        self.airtemp = "WAITING FOR AIRTEMP"
        self.pooltemp = "WAITING FOR POOLTEMP"
        self.datetime = "WAITING FOR DATETIME"
        self.salinity = "WAITING FOR SALINITY"
        self.waterfall = "INIT"


# class model:
# {
#     "display": "WAITING FOR DISPLAY",
#     "airtemp": "WAITING FOR AIRTEMP",
#     "pooltemp": "WAITING FOR POOLTEMP",
#     "datetime": "WAITING FOR DATETIME",
#     "salinity": "WAITING FOR SALINITY",
#     "waterfall": [
#         {"data": "INIT", "version": 0}
#     ]
# }