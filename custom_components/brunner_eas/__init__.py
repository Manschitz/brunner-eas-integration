
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import BrunnerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Brunner EAS."""

    coordinator = BrunnerDataUpdateCoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator

    try:
        # Start listening for UDP packets
        coordinator.start_receiving()

        await hass.config_entries.async_forward_entry_setups(
            entry,
            PLATFORMS,
        )

        await coordinator.async_config_entry_first_refresh()

    except Exception:
        await coordinator.async_disconnect()

        hass.data[DOMAIN].pop("coordinator", None)

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

        raise

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Brunner EAS."""

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    ):
        coordinator = hass.data[DOMAIN].pop("coordinator", None)

        if coordinator is not None:
            await coordinator.async_disconnect()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
