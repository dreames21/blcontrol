""" Packet ID numbers for the DP5.

These packet IDs are used by the dp5io module for communicating with the
DP5.  They characterize both commands to and replies from the device.
"""

SYNC = chr(0xF5) + chr(0xFA)

## Request packet PIDs ##
GETSTAT = chr(1) + chr(1)
GETSPEC = chr(2) + chr(1)        ## requests spectrum
GETSPECSTAT = chr(2) + chr(3)
ARMSCOPE = chr(0xf0) + chr(4)  ## arm digital scope
GETSCOPE = chr(3) + chr(1)     ## request digital scope data
CONFIG = chr(0x20) + chr(2)     ## send text configuration
CONFIG_REQ = chr(0x20) + chr(3)     ## read text configuration
CLRSPEC = chr(0xf0) + chr(1)        ## clear spectrum
ENMCA = chr(0xf0) + chr(2)      ## enables MCA
DISMCA = chr(0xf0) + chr(3)        ## disables MCA
AUTOOFFS = chr(0xf0) + chr(5)           ## autoset input offset
SETBAUD = chr(0xf0) + chr(0x13)
ECHO_REQ = chr(0xf1) + chr(0x7f)

## Response packet PIDs ##
STATUS = chr(0x80) + chr(1)
CONFIG_READ = chr(0x82) + chr(7)
ECHO_RES = chr(0x8f) + chr(0x7f)
SCOPEDATA = chr(0x82) + chr(1)
SCOPE_OVFL = chr(0x82) + chr(3)

## Spectrum and status packet PIDs ##
SPEC = chr(0x81)

SPEC_CHAN = {
    SPEC + chr(2) :  256,
    SPEC + chr(4) :  512,
    SPEC + chr(6) : 1024,
    SPEC + chr(8) : 2048,
    SPEC + chr(0x0A) : 4096,
    SPEC + chr(0x0C) : 8192
}

## Acknowledge packet PIDs ##
ACK = chr(0xFF)
ACK_OK = ACK + chr(0)

ERRORS = {
    ACK + chr(1) : "Sync error",
    ACK + chr(2) : "PID error",
    ACK + chr(3) : "Packet LEN error",
    ACK + chr(4) : "Checksum error",
    ACK + chr(5) : "Bad parameter",
    ACK + chr(6) : "Bad hex record",
    ACK + chr(7) : "Command not recognized",
    ACK + chr(8) : "FPGA error",
    ACK + chr(0x0a) : "Scope data not available",
    ACK + chr(0x0d) : "Busy - another interface in use",
    ACK + chr(0x0e) : "I2C error"
}

## Digital oscilloscope timebase if FPGA clock = 20MHz
SCOPE_TB_FPGA20 = {
    (0.8, 6.4): 0.05,
    (6.6, 12.8): 0.1,
    (13.2, 25.6): 0.2,
    (26.4, 51.2): 0.4,
    (52.8, 102.4): 0.8
}

## Digital oscilloscope timebase if FPGA clock = 80MHz
SCOPE_TB_FPGA80 = {
    (0.20, 1.60): 0.0125,
    (1.65, 3.20): 0.025,
    (3.30, 6.40): 0.05,
    (6.60, 12.80): 0.1,
    (13.20, 25.60): 0.2
}

### Settings to be set or printed by a settings import/export.
### See DP5 Programmer's Guide, sec 7, for the meaning of these settings.
SETTINGS_LIST = [
    # Order 2:
    'CLKL',
    # Order 3:
    'TPEA',
    # Order 4:
    'GAIF', 'GAIN', 'PURE', 'RESL', 'TFLA', 'TPFA',
    # Order 5:
    'RTDE',
    # Order 6:
    'MCAS',
    # No order:
    'AINP', 'AUO1', 'AUO2', 'BLRD', 'BLRM', 'BLRU', 'BOOT', 'CLCK',
    'CUSP', 'DACF', 'DACO', 'GAIA', 'GATE', 'GPED', 'GPGA', 'GPIN',
    'GPMC', 'GPME', 'HVSE', 'INOF', 'MCAC', 'MCAE', 'MCSL', 'MCSH',
    'MCST', 'PAPS', 'PDMD', 'PRCL', 'PRCH', 'PREC', 'PRER', 'PRET',
    'RTDT', 'SCAW', 'SCOE', 'SCOG', 'SCOT', 'SOFF', 'SYNC', 'TECS',
    'THFA', 'THSL', 'TLLD', 'TPMO'
    ]

## Settings related to the risetime discrimination.
## These settings can only be set if risetime discrimination is enabled.
RTD_SETTINGS = ['RTDW', 'RTDD', 'RTDS']

SCA_INDEX = "SCAI"
SCA_OUTPUT = "SCAO"   ### SCA output, only for SCAs 1-8

### Settings related to SCAs 1-16.
SCA_SETTINGS16 = ['SCAH', 'SCAL']
