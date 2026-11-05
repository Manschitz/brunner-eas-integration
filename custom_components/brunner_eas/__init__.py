
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import BrunnerDataUpdateCoordinator


type BrunnerConfigEntry = ConfigEntry[BrunnerDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
) -> None:
    """Set up Brunner EAS."""

    coordinator = BrunnerDataUpdateCoordinator(hass, entry)
    entry.runtime_data = coordinator

    try:
        # Start listening for UDP packets.
        coordinator.start_receiving()

        # Perform the initial coordinator refresh.
        await coordinator.async_config_entry_first_refresh()

        # Set up the platforms.
        await hass.config_entries.async_forward_entry_setups(
            entry,
            PLATFORMS,
        )

    except Exception:
        await coordinator.async_disconnect()
        raise


async def async_unload_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
) -> None:
    """Unload Brunner EAS."""

    # Unload the platforms first.
    await hass.config_entries.async_unload_platforms_or_raise(
        entry,
        PLATFORMS,
    )

    # Stop the UDP receiver and close the socket.
    await entry.runtime_data.async_disconnect()
