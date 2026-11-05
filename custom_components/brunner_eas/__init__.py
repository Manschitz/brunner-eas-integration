
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event

from .const import DOMAIN, PLATFORMS
from .coordinator import BrunnerDataUpdateCoordinator

eas_coordinator: BrunnerDataUpdateCoordinator | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Brunner EAS."""

    global eas_coordinator

    eas_coordinator = BrunnerDataUpdateCoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = eas_coordinator

    # Register shutdown event
    async def on_shutdown(event: Event) -> None:
        global eas_coordinator

        if eas_coordinator is not None:
            await eas_coordinator.async_disconnect()
            eas_coordinator = None

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP,
        on_shutdown,
    )

    # Start listening for UDP packets
    eas_coordinator.start_receiving()

    # Delete existing config entries:
    #await remove_all_entries(hass)

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    await eas_coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Brunner EAS."""

    global eas_coordinator

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    ):
        coordinator = hass.data[DOMAIN].get("coordinator")

        if coordinator is not None:
            await coordinator.async_disconnect()

        hass.data[DOMAIN].pop("coordinator", None)

        if eas_coordinator is coordinator:
            eas_coordinator = None

    return unload_ok


async def remove_all_entries(hass: HomeAssistant) -> None:
    """Remove all Brunner EAS config entries."""

    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        await hass.config_entries.async_remove(entry.entry_id)
