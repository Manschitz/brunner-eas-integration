
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_DEFAULT_UNIQUE_ID = "brunner_eas"


class BrunnerLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """BRUNNER EAS local config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""

        self._discovery_info: dict[str, Any] | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle manual setup."""

        # Integration only supports one device
        await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        # This calls async_setup_entry() in __init__.py
        return self.async_create_entry(
            title="BRUNNER EAS",
            data={},
        )

    async def async_step_dhcp(
        self,
        discovery_info: DhcpServiceInfo,
    ) -> FlowResult:
        """Handle DHCP discovery."""

        _LOGGER.debug("BRUNNER DHCP discovery: %s", discovery_info)

        # Integration only supports one device
        await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        self._discovery_info = {
            "ip": discovery_info.ip,
            "hostname": discovery_info.hostname,
            "macaddress": discovery_info.macaddress,
        }

        # Ask the user before creating the config entry.
        return await self.async_step_confirm()

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm DHCP discovery."""

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
