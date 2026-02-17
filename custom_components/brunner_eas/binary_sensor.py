from .const import DOMAIN
from .coordinator import BrunnerDataUpdateCoordinator
from .entities import BrunnerDoorSensorEntity, BrunnerEcoModeSensorEntity, BrunnerSPlusModeSensorEntity, BrunnerReloadingNoteSensorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# -----------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    coordinator: BrunnerDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([
        BrunnerDoorSensorEntity(coordinator),
        BrunnerSPlusModeSensorEntity(coordinator),
        BrunnerEcoModeSensorEntity(coordinator),
        BrunnerReloadingNoteSensorEntity(coordinator),
    ])

# -----------------------------------------------------------------------------
