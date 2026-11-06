
import asyncio
import logging
import re

from typing import TypedDict

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
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
    r'.*?;(?P<temperature>-?[0-9]+);.*</bdle>$'
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


class _BrunnerUDPProtocol(asyncio.DatagramProtocol):
    """Receive packets directly on the Home Assistant event loop."""

    def __init__(self, coordinator: "BrunnerDataUpdateCoordinator") -> None:
        self.coordinator = coordinator

    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        if len(data) > self.coordinator.MAX_PACKET_BYTES:
            self.coordinator._warn_invalid("Oversized BRUNNER UDP packet ignored")
            return
        try:
            message = data.decode("utf-8")
        except UnicodeDecodeError:
            self.coordinator._warn_invalid("Invalid UTF-8 BRUNNER UDP packet")
            return
        try:
            self.coordinator.process_data(message, address)
        except (ValueError, TypeError, OverflowError) as exc:
            self.coordinator._warn_invalid(f"Malformed BRUNNER UDP packet: {type(exc).__name__}")

    def error_received(self, exc: Exception) -> None:
        _LOGGER.warning("Brunner UDP transport error: %s", exc)


class BrunnerDataUpdateCoordinator(DataUpdateCoordinator[BrunnerDataDict]):
    """Coordinator for Brunner EAS local UDP broadcasts."""

    # A stopped transmitter should not leave the last measured temperature live.
    PACKET_TIMEOUT_SECONDS = 180
    MAX_PACKET_BYTES = 2048

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self._transport: asyncio.DatagramTransport | None = None
        self._timeout_handle: asyncio.TimerHandle | None = None
        self._stopped = True
        self.is_receiving = False
        self._last_firmware: str | None = None
        self._last_invalid_log = 0.0

    async def _async_update_data(self) -> BrunnerDataDict:
        """Push-based coordinator: no network polling is necessary."""
        return self.data if self.data is not None else {}

    async def async_start_receiving(self) -> None:
        """Bind UDP without blocking the event loop."""
        if self._transport is not None:
            return
        self._stopped = False
        try:
            transport, _ = await self.hass.loop.create_datagram_endpoint(
                lambda: _BrunnerUDPProtocol(self),
                local_addr=("0.0.0.0", 45454),
            )
        except OSError as exc:
            self._stopped = True
            raise ConfigEntryNotReady(f"Unable to bind BRUNNER UDP port 45454: {exc}") from exc
        except Exception:
            self._stopped = True
            raise
        self._transport = transport
        self._reset_timeout()
        _LOGGER.debug("Started Brunner UDP listener on port 45454")

    def _reset_timeout(self) -> None:
        if self._timeout_handle is not None:
            self._timeout_handle.cancel()
        self._timeout_handle = self.hass.loop.call_later(
            self.PACKET_TIMEOUT_SECONDS, self._packet_timed_out
        )

    def _packet_timed_out(self) -> None:
        self._timeout_handle = None
        if self._stopped:
            return
        _LOGGER.warning(
            "No valid Brunner EAS packet received for %s seconds; marking entities unavailable",
            self.PACKET_TIMEOUT_SECONDS,
        )
        self.is_receiving = False
        self.async_update_listeners()
        # Remain unavailable until the next valid packet; no repeated warnings.

    async def async_disconnect(self) -> None:
        """Stop listening and cancel pending callbacks during unload/reload."""
        self._stopped = True
        self.is_receiving = False
        if self._timeout_handle is not None:
            self._timeout_handle.cancel()
            self._timeout_handle = None
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self.async_update_listeners()
        _LOGGER.debug("Stopped Brunner UDP listener")

    # -------------------------------------------------------------------------
    # UDP data processing

    def process_data(
        self,
        response_message: str,
        address: tuple[str, int],
    ) -> None:
        """Process received Brunner UDP data."""

        if self._stopped:
            return

        #_LOGGER.debug("Received UDP message from {}: {}".format(address, response_message))

        response_message = response_message.rstrip("\x00\r\n ")
        if not response_message.startswith("<bdle") or "</bdle>" not in response_message:
            return

        # e.g. "<bdle eas="0" pin="0" cmd="410" stat="5">0;1;1;85;2;4;0;331;2;0;48;0;155;1;</bdle> \0"
        # s+;öko;wifi?;disp;sum;nlh;dros?;vers;verp?;error;icon_flags;?;temp;?
        match = _REGEX_UDP_DATA.fullmatch(response_message)
        #_LOGGER.debug(match.groups())

        if match is None:
            self._warn_invalid("Invalid or incompatible BRUNNER packet")
            return

        try:
            error_state = BrunnerErrorStateEnum(
                int(match.group("error"))
            )
        except (ValueError, TypeError):
            _LOGGER.warning("Unknown Brunner error state")
            error_state = BrunnerErrorStateEnum.UNKNOWN

        try:
            combustion = BrunnerCombustionEnum(
                int(match.group("status"))
            )

            reloading_indications = BrunnerReloadingIndicationsEnum(
                int(match.group("reloading_indications"))
            )

            tone_loudness = BrunnerLoudnessEnum(
                int(match.group("loudness"))
            )

        except (ValueError, TypeError):
            _LOGGER.warning(
                "Received unsupported enum values: status=%s, "
                "reloading=%s, loudness=%s",
                match.group("status"),
                match.group("reloading_indications"),
                match.group("loudness"),
            )
            return

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
            "reloading_indications": reloading_indications,
            "temperature": int(match.group("temperature")),
            "tone_loudness": tone_loudness,
            "flag_door_error": flag_door_error,
            "flag_splus_on": flag_splus_on,
            "flag_eco_off": flag_eco_off,
            "flag_reload_start": flag_reload_start,
            "flag_reload_end": flag_reload_end,
        }

        firmware_changed = firmware != self._last_firmware

        self._reset_timeout()
        self.is_receiving = True
        self.async_set_updated_data(data)

        if firmware_changed:
            self.update_firmware_version(firmware)
            self._last_firmware = firmware

        _LOGGER.debug("Brunner data updated: %s", data)

    # -------------------------------------------------------------------------
    # Home Assistant device registry

    def _warn_invalid(self, message: str) -> None:
        """Rate-limit malformed packet logs."""
        now = self.hass.loop.time()
        if now - self._last_invalid_log >= 60 or self._last_invalid_log == 0:
            _LOGGER.warning("%s", message)
            self._last_invalid_log = now

    def device_info(self) -> DeviceInfo:
        """Return Brunner device information."""

        info: DeviceInfo = {
            "manufacturer": "BRUNNER",
            "model": "EAS",
            "name": "Combustion Control",
            "translation_key": "combustion_control",
            "identifiers": {(DOMAIN, "coordinator")},
        }
        if self.data and self.data.get("firmware"):
            info["sw_version"] = self.data["firmware"]

        discovery_info = self.config_entry.data.get("discovery_info")
        if discovery_info and discovery_info.get("macaddress"):
            info["connections"] = {
                (CONNECTION_NETWORK_MAC, discovery_info["macaddress"])
            }
        return info

    def update_firmware_version(self, firmware: str) -> None:
        """Synchronously update firmware in the device registry on the HA loop."""

        info = self.device_info()
        dr.async_get(self.hass).async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers=info["identifiers"],
            connections=info.get("connections"),
            manufacturer=info["manufacturer"],
            model=info["model"],
            name=info["name"],
            sw_version=firmware,
        )

    # -------------------------------------------------------------------------
    # Firmware version helper

    def version_to_major_minor(self, version: str) -> str:
        """Convert firmware version to major.minor format."""

        major = version[0]
        minor = version[1:]

        return f"{major}.{minor}"
