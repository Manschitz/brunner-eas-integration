
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_DEFAULT_UNIQUE_ID = "brunner_eas"


class BrunnerLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """BRUNNER EAS local config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""

        self._discovery_info: dict[str, str] | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle manual setup."""

        # Integration only supports one device.
        await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="BRUNNER EAS",
            data={},
        )

    async def async_step_dhcp(
        self,
        discovery_info: DhcpServiceInfo,
    ) -> ConfigFlowResult:
        """Handle DHCP discovery."""

        mac_address = format_mac(discovery_info.macaddress)

        _LOGGER.debug(
            "BRUNNER DHCP discovery: IP=%s, hostname=%s, MAC=%s",
            discovery_info.ip,
            discovery_info.hostname,
            mac_address,
        )

        # Integration only supports one device.
        await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)

        self._discovery_info = {
            "ip": discovery_info.ip,
            "hostname": discovery_info.hostname or "Unknown",
            "macaddress": mac_address,
        }

        # Update an existing manually configured entry with DHCP information.
        # This also reloads the entry if its data has changed.
        self._abort_if_unique_id_configured(
            updates={
                "discovery_info": self._discovery_info,
            }
        )

        # Ask the user before creating a new config entry.
        return await self.async_step_confirm()

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm DHCP discovery."""

        assert self._discovery_info is not None

        if user_input is None:
            return self.async_show_form(
                step_id="confirm",
                description_placeholders={
                    "ip": self._discovery_info["ip"],
                    "hostname": self._discovery_info["hostname"],
                },
            )

        return self.async_create_entry(
            title="BRUNNER EAS",
            data={
                "discovery_info": self._discovery_info,
            },
        )
