"""Command numbers for Zaber motor controllers.

See http://www.zaber.com/wiki/Manuals/Binary_Protocol_Manual for a complete list
of available commands.
"""

HOME =       1
MTRACK =     8  # move tracking
MANMTRACK = 10  # manual move tracking
MANMV =     11  # manual move displacement
MVABS =     20  # move absolute
STOP =      23  
MICRORES =  37  # microstep resolution
RUNCURR =   38
HOLDCURR =  39
MODE =      40  
GET =       53  # get value of setting in data field
STATUS =    54
ECHO =      55
POS =       60  # get current position
SERNUM =    63  # serial number
ERROR =    255

#Dictionary mapping error codes from the device to error strings.
ERRORDICT = {
    1    : "Device cannot home",
    2    : "Device numbering invalid",
    5    : "Register address invalid",
    14   : "Voltage low",
    15   : "Voltage high",
    18   : "Stored position invalid",
    20   : "Target position out of range",
    21   : "Target position out of range",
    22   : "Invalid velocity",
    36   : "Peripheral ID invalid",
    37   : "Microstep resolution invalid",
    38   : "Run current out of range",
    39   : "Hold current out of range",
    40   : "Device mode invalid",
    41   : "Home speed out of range",
    42   : "Target speed out of range",
    43   : "Target acceleration out of range",
    44   : "Maximum position out of range",
    45   : "Current position out of range",
    47   : "Home offset out of range",
    48   : "Alias out of range",
    53   : "Setting invalid",
    64   : "Command invalid",
    65   : "Park state invalid",
    67   : "Device temperature high",
    255  : "Device busy",
    2146 : "Target position out of range",
    6501 : "Device parked"
}

#Dictionary mapping error codes from the device to error strings.
STATUSDICT = {
    0   : "Idle",
    1   : "Homing",
    10  : "Manual move, velocity mode",
    11  : "Manual move, displacement mode",
    13  : "Stalled",
    18  : "Moving to stored postion",
    20  : "Moving to absolute position",
    21  : "Moving to relative position",
    22  : "Moving at constant velocity",
    23  : "Stopping",
    65  : "Parked",
    78  : "Moving to index"
}
