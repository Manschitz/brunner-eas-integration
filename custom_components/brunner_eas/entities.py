from .const import DOMAIN, BrunnerCombustionEnum, BrunnerErrorStateEnum, BrunnerLoudnessEnum, BrunnerReloadingIndicationsEnum
from .coordinator import BrunnerDataUpdateCoordinator

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

# -----------------------------------------------------------------------------
    
class AbstractBrunnerEntity(CoordinatorEntity, Entity):

    coordinator: BrunnerDataUpdateCoordinator
    _key = None
    _attr_should_poll = False
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info()
        
    def __init__(self, coordinator: BrunnerDataUpdateCoordinator) -> None:
        self._attr_translation_key = self._key
        self._attr_unique_id = f"sensor.{DOMAIN}.{self._key}"
        super().__init__(coordinator)

    def update_from_coordinator(self) -> bool:
        raise NotImplementedError("Subclass has to implement this method.")

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------
    
class AbstractBrunnerBinarySensorEntity(AbstractBrunnerEntity, BinarySensorEntity):

    def __init__(self, coordinator: BrunnerDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"binary_sensor.{DOMAIN}.{self._key}"
    
    @property
    def available(self) -> bool:
        return self._attr_is_on != None
    
    def update_from_coordinator(self) -> bool:
        if self.coordinator.data == None:
            return False
        newValue = self.coordinator.data.get(self._key)
        if newValue != self._attr_is_on:
            self._attr_is_on = newValue
            return True
        return False
    
# -----------------------------------------------------------------------------
    
class AbstractBrunnerSensorEntity(AbstractBrunnerEntity, SensorEntity):
    
    @property
    def available(self) -> bool:
        return self.native_value != None
    
    def update_from_coordinator(self) -> bool:
        if self.coordinator.data == None:
            return False
        newValue = self.coordinator.data.get(self._key)
        if newValue != self._attr_native_value:
            self._attr_native_value = newValue
            return True
        return False
    
# -----------------------------------------------------------------------------
    
class BrunnerDisplayBrightnessSensorEntity(AbstractBrunnerSensorEntity):

    _key = "display_brightness"
    #_attr_name = "Display Brightness"
    _attr_icon = "mdi:lightbulb-question-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            if self.native_value == None:   self._attr_icon = "mdi:lightbulb-question-outline"
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
            
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerDoorSensorEntity(AbstractBrunnerBinarySensorEntity):

    _key = "door"
    #_attr_name = "Door"
    _attr_icon = "mdi:door"
    _attr_device_class = BinarySensorDeviceClass.DOOR

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self._attr_is_on:
                case True:
                    self._attr_icon = "mdi:door-open"
                case False:
                    self._attr_icon = "mdi:door"
                case _:
                    self._attr_icon = "mdi:door"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerSPlusModeSensorEntity(AbstractBrunnerBinarySensorEntity):

    _key = "splus"
    #_attr_name = "S+ Mode"
    _attr_icon = "mdi:clock-plus-outline"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self._attr_is_on:
                case True:
                    self._attr_icon = "mdi:clock-plus"
                case False:
                    self._attr_icon = "mdi:clock-remove-outline"
                case _:
                    self._attr_icon = "mdi:clock-plus-outline"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerEcoModeSensorEntity(AbstractBrunnerBinarySensorEntity):

    _key = "eco"
    #_attr_name = "Eco Mode"
    _attr_icon = "mdi:leaf"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self._attr_is_on:
                case True:
                    self._attr_icon = "mdi:leaf"
                case False:
                    self._attr_icon = "mdi:leaf-off"
                case _:
                    self._attr_icon = "mdi:leaf"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerReloadingIndicationsSensorEntity(AbstractBrunnerSensorEntity):

    _key = "reloading_indications"
    #_attr_name = "Reloading Indications"
    _attr_icon = "mdi:flag-variant-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options =  [member.name for member in BrunnerReloadingIndicationsEnum]

    @property
    def state(self) -> str | None:
        return self.native_value.name.lower() if self.native_value is not None else None
    
    @property
    def native_value(self) -> BrunnerReloadingIndicationsEnum | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self.native_value:
                case BrunnerReloadingIndicationsEnum.OFF:                           self._attr_icon = "mdi:flag-variant-off-outline"
                case BrunnerReloadingIndicationsEnum.SYMBOLS:                       self._attr_icon = "mdi:flag-variant"
                case BrunnerReloadingIndicationsEnum.SYMBOLS_AND_BEEPS:             self._attr_icon = "mdi:bell-ring"
                case BrunnerReloadingIndicationsEnum.SYMBOLS_AND_BLINKING:          self._attr_icon = "mdi:flag-variant-plus"
                case BrunnerReloadingIndicationsEnum.SYMBOLS_BEEPS_AND_BLINKING:    self._attr_icon = "mdi:bell-ring"
                case _:                                                             self._attr_icon = "mdi:flag-variant-outline"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerReloadingNoteSensorEntity(AbstractBrunnerBinarySensorEntity):

    _key = "reloading_note"
    #_attr_name = "Reload Wood"
    _attr_icon = "mdi:hand-back-right-off-outline"

    def update_from_coordinator(self) -> bool:
        if self.coordinator.data == None:
            return False
        newValue = (self.coordinator.data.get("flag_reload_start") and not self.coordinator.data.get("flag_reload_end"))
        if newValue != self._attr_is_on:
            self._attr_is_on = newValue
            return True
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self._attr_is_on:
                case True:
                    self._attr_icon = "mdi:human-dolly" #"mdi:download-multiple"
                case False:
                    self._attr_icon = "mdi:hand-back-right-off-outline"
                case _:
                    self._attr_icon = "mdi:hand-back-right-off-outline"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerTemperatureSensorEntity(AbstractBrunnerSensorEntity):

    _key = "temperature"
    #_attr_name = "Temperature"
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> int | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            if self.native_value == None:   self._attr_icon = "mdi:thermometer-off"
            elif self.native_value < 60:    self._attr_icon = "mdi:thermometer-low"
            elif self.native_value < 160:   self._attr_icon = "mdi:thermometer"
            elif self.native_value < 300:   self._attr_icon = "mdi:thermometer-high"
            elif self.native_value < 600:   self._attr_icon = "mdi:fire"
            elif self.native_value >= 600:  self._attr_icon = "mdi:fire-alert"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerCombustionSensorEntity(AbstractBrunnerSensorEntity):

    _key = "combustion"
    #_attr_name = "Combustion"
    _attr_icon = "mdi:help-circle-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options =  [member.name for member in BrunnerCombustionEnum]

    @property
    def state(self) -> str | None:
        return self.native_value.name.lower() if self.native_value is not None else None

    
    @property
    def native_value(self) -> BrunnerCombustionEnum | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self.native_value:
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
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------
            
class BrunnerErrorSensorEntity(AbstractBrunnerSensorEntity):

    _key = "error_state"
    #_attr_name = "Error State"
    _attr_icon = "mdi:alert-circle-check-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options =  [member.name for member in BrunnerErrorStateEnum]

    @property
    def state(self) -> str | None:
        return self.native_value.name.lower() if self.native_value is not None else None
    
    @property
    def native_value(self) -> BrunnerErrorStateEnum | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self.native_value:
                case BrunnerErrorStateEnum.UNKNOWN: self._attr_icon = "mdi:help"
                case BrunnerErrorStateEnum.NONE:    self._attr_icon = "mdi:alert-circle-check-outline"
                case _:                             self._attr_icon = "mdi:alert-decagram"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerLoudnessSensorEntity(AbstractBrunnerSensorEntity):

    _key = "tone_loudness"
    #_attr_name = "Tone Loudness"
    _attr_icon = "mdi:volume-variant-off"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options =  [member.name for member in BrunnerLoudnessEnum]

    @property
    def state(self) -> str | None:
        return self.native_value.name.lower() if self.native_value is not None else None
    
    @property
    def native_value(self) -> BrunnerLoudnessEnum | None:
        return self._attr_native_value
    
    @callback
    def _handle_coordinator_update(self) -> None:
        if self.update_from_coordinator():
            match self.native_value:
                case BrunnerLoudnessEnum.SILENT:    self._attr_icon = "mdi:volume-variant-off"
                case BrunnerLoudnessEnum.MEDIUM:    self._attr_icon = "mdi:volume-medium"
                case BrunnerLoudnessEnum.LOUD:      self._attr_icon = "mdi:volume-high"
                case _:                             self._attr_icon = "mdi:volume-variant-off"
            self.schedule_update_ha_state()

# -----------------------------------------------------------------------------

class BrunnerIPAddressSensorEntity(AbstractBrunnerSensorEntity):

    _key = "ip_address"
    #_attr_name = "IP Address"
    _attr_icon = "mdi:wifi"

    @property
    def state(self) -> str | None:
        return self.native_value
    
    @property
    def native_value(self) -> str | None:
        return self._attr_native_value

# -----------------------------------------------------------------------------
