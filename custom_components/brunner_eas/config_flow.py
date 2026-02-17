"""Config flow for Brunner EAS integration."""

from typing import Optional

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

_DEFAULT_UNIQUE_ID = "brunner_eas"

class BrunnerLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """BRUNNER EAS local config flow."""

    VERSION = 1

    async def async_step_user(self, info: Optional[dict] = None) -> FlowResult:
        """Handle step initialized by user."""

        if self._async_current_entries():
            raise AbortFlow("already_configured")

        # Integration only supports one device
        await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        # This calls async_setup_entry() in __init__.py
        return self.async_create_entry(
            title = "BRUNNER EAS",
            data = {},
        )
    
    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> FlowResult:
        """Handle DHCP discovery."""

        _LOGGER.debug(discovery_info)

        if self._async_current_entries():
            raise AbortFlow("already_configured")

        # Integration only supports one device
        if not self.unique_id:
            await self.async_set_unique_id(_DEFAULT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        # This calls async_setup_entry() in __init__.py
        return self.async_create_entry(
            title = "BRUNNER EAS",
            data = {
                "discovery_info": {
                    "ip": discovery_info.ip,
                    "hostname": discovery_info.hostname,
                    "macaddress": discovery_info.macaddress,
                }
            },
        )

