import re
import socket
import logging
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntry, CONNECTION_NETWORK_MAC
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, BrunnerCombustionEnum, BrunnerErrorStateEnum, BrunnerLoudnessEnum, BrunnerReloadingIndicationsEnum

_LOGGER = logging.getLogger(__name__)

_REGEX_UDP_DATA = re.compile('^<bdle.*stat="(?P<status>-?[0-9]+)".*>(?P<splus>[01]);(?P<eco>[01]);.*?;(?P<display>[0-9]+);(?P<loudness>[012]);(?P<reloading_indications>[01234]);.*?;(?P<firmware>[0-9]+);.*?;(?P<error>-?[0-9]+);(?P<icon_flags>[0-9]+);.*?;(?P<temperature>-?[0-9]+);.*$')

# -----------------------------------------------------------------------------

class BrunnerDataDict(TypedDict, total=True):
    debug: str = None
    ip_address: str = None
    port: str = None
    error_state: BrunnerErrorStateEnum = None
    display_brightness: int = None
    door: bool = None
    eco: bool = None
    splus: bool = None
    status: BrunnerCombustionEnum = None
    firmware: str = None
    temperature: int = None
    flag_door_error: bool = None
    flag_splus_on: bool = None
    flag_eco_off: bool = None
    flag_reload_start: bool = None
    flag_reload_end: bool = None

# -----------------------------------------------------------------------------
# see https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py
class BrunnerDataUpdateCoordinator(DataUpdateCoordinator[BrunnerDataDict]):

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:

        self.config_entry = config_entry

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=None
        )

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("0.0.0.0", 45454))
        #self.udp_socket.setblocking(False)
        self.running = False

    async def _async_update_data(self) -> BrunnerDataDict:
        return self.data
    
    def start_receiving(self) -> None:
        self.running = True
        self.hass.loop.run_in_executor(None, self.receive_data)

    def stop_receiving(self) -> None:
        self.running = False

    def disconnect(self) -> None:
        if self.running:
            self.stop_receiving()
        if self.udp_socket:
            self.udp_socket.close()

    def receive_data(self) -> None:
        while self.running:
            try:
                data, address = self.udp_socket.recvfrom(1024)
                response_message = data.decode('utf-8')
                self.process_data(response_message, address)

            except Exception as e:
                self.logger.error(f"Error receiving data: {e}")

    def process_data(self, response_message, address) -> None:
        #self.logger.debug("Received UDP message from {}: {}".format(address, response_message))
        if not response_message.startswith("<bdle"):
            return

        # e.g. "<bdle eas="0" pin="0" cmd="410" stat="5">0;1;1;85;2;4;0;331;2;0;48;0;155;1;</bdle> \0"
        # s+;öko;wifi?;disp;sum;nlh;dros?;vers;verp?;error;icon_flags;?;temp;?
        match = re.search(_REGEX_UDP_DATA, response_message)
        #self.logger.debug(match.groups())

        if match == None:
            self.logger.error("Invalid or incompatible data format in response message: %s", response_message)
            return self.data

        try:
            error_state = (BrunnerErrorStateEnum)(int(match.group("error")))
        except Exception as ex:
            self.logger.error(ex)
            error_state = BrunnerErrorStateEnum.UNKNOWN

        combustion = (BrunnerCombustionEnum)(int(match.group("status")))

        icon_flags = int(match.group("icon_flags"))
        flag_door_error = (icon_flags & (1 << 0)) != 0 # 1
        #unknown = (icon_flags & (1 << 1)) != 0 # 2
        flag_splus_on = (icon_flags & (1 << 2)) != 0 # 4
        flag_eco_off = (icon_flags & (1 << 3)) != 0 # 8
        flag_reload_start = (icon_flags & (1 << 4)) != 0 # 16
        flag_reload_end = (icon_flags & (1 << 5)) != 0 # 32
        #unknown = (icon_flags & (1 << 6)) != 0 # 64

        firmware: str = self.version_to_major_minor(match.group("firmware"))

        data: BrunnerDataDict = {
            "debug": response_message,
            "ip_address": address[0],
            "port": address[1],
            "error_state": error_state,
            "display_brightness": int(match.group("display")),
            "door": combustion == BrunnerCombustionEnum.DOOR_OPEN,
            "eco": match.group("eco") == "1",
            "splus": match.group("splus") == "1",
            "combustion": combustion,
            "firmware": firmware,
            "reloading_indications": (BrunnerReloadingIndicationsEnum)(int(match.group("reloading_indications"))),
            "temperature": int(match.group("temperature")),
            "tone_loudness": (BrunnerLoudnessEnum)(int(match.group("loudness"))),
            "flag_door_error": flag_door_error,
            "flag_splus_on": flag_splus_on,
            "flag_eco_off": flag_eco_off,
            "flag_reload_start": flag_reload_start,
            "flag_reload_end": flag_reload_end,
        }

        if (self.data == None or (firmware != self.data.get("firmware"))):
            self.hass.add_job(self.async_update_firmware_version, firmware)

        self.data = data;
        self.async_set_updated_data(data)
        self.logger.debug(data)

    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            manufacturer = "BRUNNER",
            model = "EAS",
            name = "BRUNNER EAS",
            connections = None if self.config_entry.data.get("discovery_info") == None else {(CONNECTION_NETWORK_MAC, self.config_entry.data.get("discovery_info")["macaddress"])},
            identifiers = {(DOMAIN, "coordinator")},
            sw_version = None if self.data == None else self.data.get("firmware")
        )
    
    async def async_update_firmware_version(self, firmware: str) -> None:
        device_info: DeviceInfo = self.device_info()
        device_entry: DeviceEntry = self.hass.data['device_registry'].async_get_device(device_info.get("identifiers"))
        #self.logger.debug(device_entry)
        self.hass.data['device_registry'].async_update_device(device_entry.id, sw_version=firmware)
    
    def version_to_major_minor(self, version: str) -> str:
        # Extract the first digit as the major version and the following two digits as the minor version
        major = version[0]
        minor = version[1:]
        return f"{major}.{minor}"
