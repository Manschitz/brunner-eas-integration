from enum import Enum
from homeassistant.const import Platform

DOMAIN = "brunner_eas"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

# -----------------------------------------------------------------------------

class BrunnerErrorStateEnum(Enum):
    COMBUSTION_ERROR = -32768
    FIRE_STARTING_AND_COMBUSTION_ERROR = -16384
    UNKNOWN = -1
    NONE = 0
    FIRE_STARTING_ERROR = 16384
    # @TODO STOVE_HOT_ERROR

# -----------------------------------------------------------------------------

class BrunnerCombustionEnum(Enum):
    UNKNOWN = -1
    DOOR_OPEN = 0
    STAGE1 = 1
    STAGE2 = 2
    STAGE3 = 3
    STAGE4 = 4
    EMBERS = 5
    REST = 6
    ENDED = 7
        
# -----------------------------------------------------------------------------

class BrunnerLoudnessEnum(Enum):
    SILENT = 0
    MEDIUM = 1
    LOUD = 2

# -----------------------------------------------------------------------------

class BrunnerReloadingIndicationsEnum(Enum):
    OFF = 0
    SYMBOLS = 1
    SYMBOLS_AND_BEEPS = 2
    SYMBOLS_AND_BLINKING = 3
    SYMBOLS_BEEPS_AND_BLINKING = 4
        
# -----------------------------------------------------------------------------