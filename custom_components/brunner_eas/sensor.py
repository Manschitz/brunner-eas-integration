from .const import DOMAIN
from .coordinator import BrunnerDataUpdateCoordinator
from .entities import BrunnerTemperatureSensorEntity, BrunnerCombustionSensorEntity, BrunnerDisplayBrightnessSensorEntity, BrunnerErrorSensorEntity, BrunnerLoudnessSensorEntity, BrunnerReloadingIndicationsSensorEntity, BrunnerIPAddressSensorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# -----------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    coordinator: BrunnerDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([
        BrunnerTemperatureSensorEntity(coordinator),
        BrunnerCombustionSensorEntity(coordinator),
        BrunnerDisplayBrightnessSensorEntity(coordinator),
        BrunnerErrorSensorEntity(coordinator),
        BrunnerLoudnessSensorEntity(coordinator),
        BrunnerReloadingIndicationsSensorEntity(coordinator),
        BrunnerIPAddressSensorEntity(coordinator),
    ])

# -----------------------------------------------------------------------------
