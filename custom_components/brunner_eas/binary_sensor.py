
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BrunnerDataUpdateCoordinator
from .entities import (
    BrunnerDoorSensorEntity,
    BrunnerEcoModeSensorEntity,
    BrunnerSPlusModeSensorEntity,
    BrunnerReloadingNoteSensorEntity,
)


# -----------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BrunnerDataUpdateCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Brunner EAS sensors."""

    coordinator = entry.runtime_data

    async_add_entities(
        [
            BrunnerDoorSensorEntity(coordinator),
            BrunnerSPlusModeSensorEntity(coordinator),
            BrunnerEcoModeSensorEntity(coordinator),
            BrunnerReloadingNoteSensorEntity(coordinator),
        ]
    )


# -----------------------------------------------------------------------------
