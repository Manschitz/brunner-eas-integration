
import re
import socket
import logging
import threading
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    CONNECTION_NETWORK_MAC,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    BrunnerCombustionEnum,
    BrunnerErrorStateEnum,
    BrunnerLoudnessEnum,
    BrunnerReloadingIndicationsEnum,
)

_LOGGER = logging.getLogger(__name__)

_REGEX_UDP_DATA = re.compile(
    r'^<bdle.*stat="(?P<status>-?[0-9]+)".*>'
    r'(?P<splus>[01]);(?P<eco>[01]);.*?;'
    r'(?P<display>[0-9]+);'
    r'(?P<loudness>[012]);'
    r'(?P<reloading_indications>[01234]);'
    r'.*?;(?P<firmware>[0-9]+);'
    r'.*?;(?P<error>-?[0-9]+);'
    r'(?P<icon_flags>[0-9]+);'
    r'.*?;(?P<temperature>-?[0-9]+);.*$'
)


# -----------------------------------------------------------------------------

class BrunnerDataDict(TypedDict, total=False):
    debug: str
    ip_address: str
    port: int
    error_state: BrunnerErrorStateEnum
    display_brightness: int
    door: bool
    eco: bool
    splus: bool
    combustion: BrunnerCombustionEnum
    firmware: str
    reloading_indications: BrunnerReloadingIndicationsEnum
    temperature: int
    tone_loudness: BrunnerLoudnessEnum
    flag_door_error: bool
    flag_splus_on: bool
    flag_eco_off: bool
    flag_reload_start: bool
    flag_reload_end: bool


# -----------------------------------------------------------------------------

class BrunnerDataUpdateCoordinator(DataUpdateCoordinator[BrunnerDataDict]):
    """Coordinator for Brunner EAS."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        self.config_entry = config_entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

        self.udp_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )
        self.udp_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )
        self.udp_socket.settimeout(1.0)
        self.udp_socket.bind(("0.0.0.0", 45454))

        self._stop_event = threading.Event()
        self._receiver_future = None

    async def _async_update_data(self) -> BrunnerDataDict:
        return self.data

    # -------------------------------------------------------------------------
    # UDP receiver lifecycle

    def start_receiving(self) -> None:
        """Start the UDP receiver."""

        if (
            self._receiver_future is not None
            and not self._receiver_future.done()
        ):
            _LOGGER.debug("UDP receiver is already running")
            return

        if self.udp_socket is None:
            _LOGGER.error("Cannot start UDP receiver: socket is closed")
            return

        self._stop_event.clear()

        self._receiver_future = self.hass.async_add_executor_job(
            self.receive_data
        )

        _LOGGER.debug("Started Brunner UDP receiver")

    async def async_stop_receiving(self) -> None:
        """Stop the UDP receiver."""

        self._stop_event.set()

        if self._receiver_future is not None:
            await self._receiver_future
            self._receiver_future = None

        _LOGGER.debug("Stopped Brunner UDP receiver")

    async def async_disconnect(self) -> None:
        """Stop the receiver and close the UDP socket."""

        await self.async_stop_receiving()

        if self.udp_socket is not None:
            self.udp_socket.close()
            self.udp_socket = None

        _LOGGER.debug("Disconnected Brunner UDP receiver")

    # -------------------------------------------------------------------------
    # UDP data reception

    def receive_data(self) -> None:
        """Receive UDP packets in an executor thread."""

        while not self._stop_event.is_set():
            try:
                data, address = self.udp_socket.recvfrom(1024)

            except socket.timeout:
                continue

            except OSError:
                if not self._stop_event.is_set():
                    _LOGGER.exception("Error receiving Brunner UDP data")
                break

            except Exception:
                _LOGGER.exception("Unexpected error receiving UDP data")
                break

            if self._stop_event.is_set():
                break

            try:
                response_message = data.decode("utf-8")

                # Process packets on the Home Assistant event loop.
                self.hass.add_job(
                    self.process_data,
                    response_message,
                    address,
                )

            except UnicodeDecodeError:
                _LOGGER.warning("Received invalid UTF-8 UDP packet")

            except Exception:
                _LOGGER.exception("Error processing received UDP packet")

        _LOGGER.debug("Brunner UDP receiver thread exited")

    # -------------------------------------------------------------------------
    # UDP data processing

    def process_data(
        self,
        response_message: str,
        address: tuple,
    ) -> None:
        """Process received Brunner UDP data."""

        #_LOGGER.debug("Received UDP message from {}: {}".format(address, response_message))

        if not response_message.startswith("<bdle"):
            return

        # e.g. "<bdle eas="0" pin="0" cmd="410" stat="5">0;1;1;85;2;4;0;331;2;0;48;0;155;1;</bdle> \0"
        # s+;öko;wifi?;disp;sum;nlh;dros?;vers;verp?;error;icon_flags;?;temp;?
        match = _REGEX_UDP_DATA.search(response_message)
        #_LOGGER.debug(match.groups())

        if match is None:
            _LOGGER.error(
                "Invalid or incompatible data format in response message: %s",
                response_message,
            )
            return

        try:
            error_state = BrunnerErrorStateEnum(
                int(match.group("error"))
            )
        except (ValueError, TypeError):
            _LOGGER.warning("Unknown Brunner error state")
            error_state = BrunnerErrorStateEnum.UNKNOWN

        combustion = BrunnerCombustionEnum(
            int(match.group("status"))
        )

        icon_flags = int(match.group("icon_flags"))

        flag_door_error = (icon_flags & (1 << 0)) != 0 # 1
        #unknown = (icon_flags & (1 << 1)) != 0 # 2
        flag_splus_on = (icon_flags & (1 << 2)) != 0 # 4
        flag_eco_off = (icon_flags & (1 << 3)) != 0 # 8
        flag_reload_start = (icon_flags & (1 << 4)) != 0 # 16
        flag_reload_end = (icon_flags & (1 << 5)) != 0 # 32
        #unknown = (icon_flags & (1 << 6)) != 0 # 64

        firmware = self.version_to_major_minor(
            match.group("firmware")
        )

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
            "reloading_indications": BrunnerReloadingIndicationsEnum(
                int(match.group("reloading_indications"))
            ),
            "temperature": int(match.group("temperature")),
            "tone_loudness": BrunnerLoudnessEnum(
                int(match.group("loudness"))
            ),
            "flag_door_error": flag_door_error,
            "flag_splus_on": flag_splus_on,
            "flag_eco_off": flag_eco_off,
            "flag_reload_start": flag_reload_start,
            "flag_reload_end": flag_reload_end,
        }

        if self.data is None or firmware != self.data.get("firmware"):
            self.hass.add_job(
                self.async_update_firmware_version,
                firmware,
            )

        self.async_set_updated_data(data)

        _LOGGER.debug("Brunner data updated: %s", data)

    # -------------------------------------------------------------------------
    # Home Assistant device registry

    def device_info(self) -> DeviceInfo:
        """Return Brunner device information."""

        device_info = DeviceInfo(
            manufacturer="BRUNNER",
            model="EAS",
            name="BRUNNER EAS",
            identifiers={(DOMAIN, "coordinator")},
            sw_version=(
                None if self.data is None
                else self.data.get("firmware")
            ),
        )

        discovery_info = self.config_entry.data.get("discovery_info")

        if discovery_info and discovery_info.get("macaddress"):
            device_info["connections"] = {
                (
                    CONNECTION_NETWORK_MAC,
                    discovery_info["macaddress"],
                )
            }

        return device_info

    async def async_update_firmware_version(
        self,
        firmware: str,
    ) -> None:
        """Update firmware version in the device registry."""

        device_info = self.device_info()
        registry = dr.async_get(self.hass)

        device_entry = registry.async_get_device(
            identifiers=device_info["identifiers"]
        )

        if device_entry is None:
            _LOGGER.debug(
                "Brunner device not registered yet. "
                "Skipping firmware registry update."
            )
            return

        registry.async_update_device(
            device_entry.id,
            sw_version=firmware,
        )

    # -------------------------------------------------------------------------
    # Firmware version helper

    def version_to_major_minor(self, version: str) -> str:
        """Convert firmware version to major.minor format."""

        major = version[0]
        minor = version[1:]

        return f"{major}.{minor}"
