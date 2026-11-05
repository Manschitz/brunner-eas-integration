
from typing import ClassVar

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    BrunnerCombustionEnum,
    BrunnerErrorStateEnum,
    BrunnerLoudnessEnum,
    BrunnerReloadingIndicationsEnum,
)
from .coordinator import BrunnerDataUpdateCoordinator


# -----------------------------------------------------------------------------

class AbstractBrunnerEntity(
    CoordinatorEntity[BrunnerDataUpdateCoordinator]
):
    """Base class for BRUNNER entities."""

    coordinator: BrunnerDataUpdateCoordinator

    _key: ClassVar[str]
    _entity_platform: ClassVar[str] = "sensor"

    _attr_should_poll = False
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""

        return self.coordinator.device_info()

    def __init__(
        self,
        coordinator: BrunnerDataUpdateCoordinator,
    ) -> None:
        """Initialize the entity."""

        # Initialize state before CoordinatorEntity subscribes to updates.
        # Home Assistant may access entity properties during registration.
        self._attr_native_value = None
        self._attr_is_on = None
        self._attr_translation_key = self._key
        self._attr_unique_id = (
            f"{self._entity_platform}.{DOMAIN}.{self._key}"
        )

        super().__init__(coordinator)
        self.update_from_coordinator()

    def update_from_coordinator(self) -> bool:
        """Update entity state from coordinator."""

        raise NotImplementedError


# -----------------------------------------------------------------------------

class AbstractBrunnerBinarySensorEntity(
    AbstractBrunnerEntity,
    BinarySensorEntity,
):
    """Base class for BRUNNER binary sensors."""

    _entity_platform = "binary_sensor"

    @property
    def available(self) -> bool:
        """Return entity availability."""

        return self.coordinator.is_receiving and self._attr_is_on is not None

    def update_from_coordinator(self) -> bool:
        """Update binary sensor state."""

        new_value = (self.coordinator.data or {}).get(self._key)

        if new_value != self._attr_is_on:
            self._attr_is_on = new_value
            return True

        return False


# -----------------------------------------------------------------------------

class AbstractBrunnerSensorEntity(
    AbstractBrunnerEntity,
    SensorEntity,
):
    """Base class for BRUNNER sensors."""

    @property
    def available(self) -> bool:
        """Return entity availability."""

        return self.coordinator.is_receiving and self.native_value is not None

    def update_from_coordinator(self) -> bool:
        """Update sensor state."""

        new_value = (self.coordinator.data or {}).get(self._key)

        if new_value != self._attr_native_value:
            self._attr_native_value = new_value
            return True

        return False


# -----------------------------------------------------------------------------

class BrunnerDisplayBrightnessSensorEntity(AbstractBrunnerSensorEntity):
    """Display brightness sensor."""

    _key = "display_brightness"
    #_attr_name = "Display Brightness"
    _attr_icon = "mdi:lightbulb-question-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int | None:
        """Return display brightness."""

        return self._attr_native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        if self.native_value is None:   self._attr_icon = "mdi:lightbulb-question-outline"
        elif self.native_value == 0:    self._attr_icon = "mdi:lightbulb-outline"
        elif self.native_value < 10:    self._attr_icon = "mdi:lightbulb-on-outline"
        elif self.native_value < 20:    self._attr_icon = "mdi:lightbulb-on-10"
        elif self.native_value < 30:    self._attr_icon = "mdi:lightbulb-on-20"
        elif self.native_value < 40:    self._attr_icon = "mdi:lightbulb-on-30"
        elif self.native_value < 50:    self._attr_icon = "mdi:lightbulb-on-40"
        elif self.native_value < 60:    self._attr_icon = "mdi:lightbulb-on-50"
        elif self.native_value < 70:    self._attr_icon = "mdi:lightbulb-on-60"
        elif self.native_value < 80:    self._attr_icon = "mdi:lightbulb-on-70"
        elif self.native_value < 90:    self._attr_icon = "mdi:lightbulb-on-80"
        elif self.native_value < 100:   self._attr_icon = "mdi:lightbulb-on-90"
        elif self.native_value >= 100:  self._attr_icon = "mdi:lightbulb-on"
        

        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerDoorSensorEntity(AbstractBrunnerBinarySensorEntity):
    """Door sensor."""

    _key = "door"
    #_attr_name = "Door"
    _attr_icon = "mdi:door"
    _attr_device_class = BinarySensorDeviceClass.DOOR

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_is_on:
            case True:
                self._attr_icon = "mdi:door-open"
            case False:
                self._attr_icon = "mdi:door"
            case _:
                self._attr_icon = "mdi:door"

        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerSPlusModeSensorEntity(AbstractBrunnerBinarySensorEntity):
    """S+ mode sensor."""

    _key = "splus"
    #_attr_name = "S+ Mode"
    _attr_icon = "mdi:clock-plus-outline"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_is_on:
            case True:
                self._attr_icon = "mdi:clock-plus"
            case False:
                self._attr_icon = "mdi:clock-remove-outline"
            case _:
                self._attr_icon = "mdi:clock-plus-outline"

        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerEcoModeSensorEntity(AbstractBrunnerBinarySensorEntity):
    """Eco mode sensor."""

    _key = "eco"
    #_attr_name = "Eco Mode"
    _attr_icon = "mdi:leaf"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_is_on:
            case True:
                self._attr_icon = "mdi:leaf"
            case False:
                self._attr_icon = "mdi:leaf-off"
            case _:
                self._attr_icon = "mdi:leaf"

        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerReloadingIndicationsSensorEntity(AbstractBrunnerSensorEntity):
    """Reloading indications sensor."""

    _key = "reloading_indications"
    #_attr_name = "Reloading Indications"
    _attr_icon = "mdi:flag-variant-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        member.name.lower()
        for member in BrunnerReloadingIndicationsEnum
    ]

    @property
    def native_value(self) -> str | None:
        """Return reloading indications."""

        value = self._attr_native_value
        return value.name.lower() if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_native_value:
            case BrunnerReloadingIndicationsEnum.OFF:                           self._attr_icon = "mdi:flag-variant-off-outline"
            case BrunnerReloadingIndicationsEnum.SYMBOLS:                       self._attr_icon = "mdi:flag-variant"
            case BrunnerReloadingIndicationsEnum.SYMBOLS_AND_BEEPS:             self._attr_icon = "mdi:bell-ring"
            case BrunnerReloadingIndicationsEnum.SYMBOLS_AND_BLINKING:          self._attr_icon = "mdi:flag-variant-plus"
            case BrunnerReloadingIndicationsEnum.SYMBOLS_BEEPS_AND_BLINKING:    self._attr_icon = "mdi:bell-ring"
            case _:                                                             self._attr_icon = "mdi:flag-variant-outline"
        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerReloadingNoteSensorEntity(AbstractBrunnerBinarySensorEntity):
    """Reloading note sensor."""

    _key = "reloading_note"
    #_attr_name = "Reload Wood"
    _attr_icon = "mdi:hand-back-right-off-outline"

    def update_from_coordinator(self) -> bool:
        """Update reloading note state."""

        data = self.coordinator.data or {}
        reload_start = data.get("flag_reload_start")
        reload_end = data.get("flag_reload_end")

        if reload_start is None or reload_end is None:
            new_value = None
        else:
            new_value = reload_start and not reload_end

        if new_value != self._attr_is_on:
            self._attr_is_on = new_value
            return True

        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_is_on:
            case True:
                self._attr_icon = "mdi:human-dolly"
            case False:
                self._attr_icon = "mdi:hand-back-right-off-outline"
            case _:
                self._attr_icon = "mdi:hand-back-right-off-outline"

        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerTemperatureSensorEntity(AbstractBrunnerSensorEntity):
    """Temperature sensor."""

    _key = "temperature"
    #_attr_name = "Temperature"
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> int | None:
        """Return temperature."""

        return self._attr_native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        if self.native_value is None:   self._attr_icon = "mdi:thermometer-off"
        elif self.native_value < 60:    self._attr_icon = "mdi:thermometer-low"
        elif self.native_value < 160:   self._attr_icon = "mdi:thermometer"
        elif self.native_value < 300:   self._attr_icon = "mdi:thermometer-high"
        elif self.native_value < 600:   self._attr_icon = "mdi:fire"
        elif self.native_value >= 600:  self._attr_icon = "mdi:fire-alert"
        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerCombustionSensorEntity(AbstractBrunnerSensorEntity):
    """Combustion sensor."""

    _key = "combustion"
    #_attr_name = "Combustion"
    _attr_icon = "mdi:help-circle-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        member.name.lower()
        for member in BrunnerCombustionEnum
    ]

    @property
    def native_value(self) -> str | None:
        """Return combustion state."""

        value = self._attr_native_value
        return value.name.lower() if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_native_value:
            case BrunnerCombustionEnum.UNKNOWN:     self._attr_icon = "mdi:help-circle-outline"
            case BrunnerCombustionEnum.DOOR_OPEN:   self._attr_icon = "mdi:door-open"
            case BrunnerCombustionEnum.STAGE1:      self._attr_icon = "mdi:circle-slice-1"
            case BrunnerCombustionEnum.STAGE2:      self._attr_icon = "mdi:circle-slice-2"
            case BrunnerCombustionEnum.STAGE3:      self._attr_icon = "mdi:circle-slice-3"
            case BrunnerCombustionEnum.STAGE4:      self._attr_icon = "mdi:circle-slice-4"
            case BrunnerCombustionEnum.EMBERS:      self._attr_icon = "mdi:circle-slice-5"
            case BrunnerCombustionEnum.REST:        self._attr_icon = "mdi:circle-slice-7"
            case BrunnerCombustionEnum.ENDED:       self._attr_icon = "mdi:circle-slice-8"
            case _:                                 self._attr_icon = "mdi:help-circle-outline"
        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerErrorSensorEntity(AbstractBrunnerSensorEntity):
    """Error state sensor."""

    _key = "error_state"
    #_attr_name = "Error State"
    _attr_icon = "mdi:alert-circle-check-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        member.name.lower()
        for member in BrunnerErrorStateEnum
    ]

    @property
    def native_value(self) -> str | None:
        """Return error state."""

        value = self._attr_native_value
        return value.name.lower() if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_native_value:
            case BrunnerErrorStateEnum.UNKNOWN: self._attr_icon = "mdi:help"
            case BrunnerErrorStateEnum.NONE:    self._attr_icon = "mdi:alert-circle-check-outline"
            case _:                             self._attr_icon = "mdi:alert-decagram"
        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerLoudnessSensorEntity(AbstractBrunnerSensorEntity):
    """Tone loudness sensor."""

    _key = "tone_loudness"
    #_attr_name = "Tone Loudness"
    _attr_icon = "mdi:volume-variant-off"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        member.name.lower()
        for member in BrunnerLoudnessEnum
    ]

    @property
    def native_value(self) -> str | None:
        """Return tone loudness."""

        value = self._attr_native_value
        return value.name.lower() if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""

        self.update_from_coordinator()
        match self._attr_native_value:
            case BrunnerLoudnessEnum.SILENT:    self._attr_icon = "mdi:volume-variant-off"
            case BrunnerLoudnessEnum.MEDIUM:    self._attr_icon = "mdi:volume-medium"
            case BrunnerLoudnessEnum.LOUD:      self._attr_icon = "mdi:volume-high"
            case _:                             self._attr_icon = "mdi:volume-variant-off"
        self.async_write_ha_state()
# -----------------------------------------------------------------------------

class BrunnerIPAddressSensorEntity(AbstractBrunnerSensorEntity):
    """IP address sensor."""

    _key = "ip_address"
    #_attr_name = "IP Address"
    _attr_icon = "mdi:wifi"

    @property
    def native_value(self) -> str | None:
        """Return IP address."""

        return self._attr_native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the IP address when a UDP packet is received."""
        self.update_from_coordinator()
        self.async_write_ha_state()


# -----------------------------------------------------------------------------
