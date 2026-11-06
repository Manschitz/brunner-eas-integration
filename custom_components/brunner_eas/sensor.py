
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrunnerDataUpdateCoordinator
from .entities import (
    BrunnerTemperatureSensorEntity,
    BrunnerCombustionSensorEntity,
    BrunnerDisplayBrightnessSensorEntity,
    BrunnerErrorSensorEntity,
    BrunnerLoudnessSensorEntity,
    BrunnerReloadingIndicationsSensorEntity,
    BrunnerIPAddressSensorEntity,
)


# -----------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BrunnerDataUpdateCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up BRUNNER EAS sensors."""

    coordinator = entry.runtime_data

    async_add_entities(
        [
            BrunnerTemperatureSensorEntity(coordinator),
            BrunnerCombustionSensorEntity(coordinator),
            BrunnerDisplayBrightnessSensorEntity(coordinator),
            BrunnerErrorSensorEntity(coordinator),
            BrunnerLoudnessSensorEntity(coordinator),
            BrunnerReloadingIndicationsSensorEntity(coordinator),
            BrunnerIPAddressSensorEntity(coordinator),
        ]
    )


# -----------------------------------------------------------------------------
