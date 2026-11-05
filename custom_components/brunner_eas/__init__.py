
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import BrunnerDataUpdateCoordinator


type BrunnerConfigEntry = ConfigEntry[BrunnerDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
) -> None:
    """Set up BRUNNER EAS from a config entry."""
    coordinator = BrunnerDataUpdateCoordinator(hass, entry)

    try:
        await coordinator.async_start_receiving()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await coordinator.async_disconnect()
        raise


async def async_unload_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
) -> None:
    """Unload BRUNNER EAS and release the UDP listener."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
    await entry.runtime_data.async_disconnect()
