"""Sensors for the shell_recharge_ev integration."""
from __future__ import annotations
import typing
import logging

import shellrechargeev

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ShellRechargeEVDataUpdateCoordinator
from .const import DOMAIN, EvseId

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a shell_recharge_ev sensor entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    evse_id = 0

    for evse in coordinator.data.evses:
        evse_id = evse.uid
        sensor = ShellRechargeEVSensor(evse_id=evse_id, coordinator=coordinator)
        entities.append(sensor)

    async_add_entities(entities, True)


class ShellRechargeEVSensor(
    CoordinatorEntity[ShellRechargeEVDataUpdateCoordinator], SensorEntity
):
    """Main feature of this integration. This sensor represents an EVSE and shows its realtime availability status."""

    # _attr_has_entity_name = True
    # _attr_name = None

    def __init__(
        self,
        evse_id: EvseId,
        coordinator: ShellRechargeEVDataUpdateCoordinator,
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.evse_id = evse_id
        self.coordinator = coordinator
        self.location = self.coordinator.data
        self._attr_unique_id = f"{evse_id}-charger"
        self._attr_attribution = "shellrecharge.com"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        if 'suboperatorName' in self.location and self.location.suboperatorName:
            operator = self.location.suboperatorName
        else:
            operator = self.location.operatorName
        self._attr_device_info = DeviceInfo(
            name=operator,
            identifiers={(DOMAIN, self.evse_id)},
            entry_type=None,
        )
        self._attr_has_entity_name = False
        self._attr_name = f"{operator} {self.location.address.streetAndNumber} {self.location.address.city}"
        self._attr_device_info = {}
        self._attr_options = list(typing.get_args(shellrechargeev.Status))
        # read data from coordinator, which should have data by now
        self._read_coordinator_data()

    def _get_evse(self) -> shellrechargeev.Evse:
        for evse in self.coordinator.data.evses:
            if evse.uid == self.evse_id:
                return evse

    def _choose_icon(self, connectors: list[shellrechargeev.Connector]):
        iconmap: dict[str, str] = {
            "Type1": "mdi:ev-plug-type1",
            "Type2": "mdi:ev-plug-type2",
            "Type3": "mdi:ev-plug-type2",
            "Type1Combo": "mdi:ev-plug-ccs1",
            "Type2Combo": "mdi:ev-plug-ccs2",
            "SAEJ1772": "mdi:ev-plug-chademo",
            "TepcoCHAdeMO": "mdi:ev-plug-chademo",
            "Tesla": "mdi:ev-plug-tesla",
            "Domestic": "mdi:power-socket-eu",
            "Unspecified": "mdi:ev-station"
        }
        if len(connectors) != 1:
            return "mdi:ev-station"
        return iconmap.get(connectors[0].connectorType, "mdi:ev-station")


    def _read_coordinator_data(self) -> None:
        evse = self._get_evse()
        self._attr_native_value = evse.status
        self._attr_icon = self._choose_icon(evse.connectors)
        extra_data = {
            "address": self.location.address.streetAndNumber,
            "city": self.location.address.city,
            "postal_code": self.location.address.postalCode,
            "country": self.location.address.country,
            "latitude": self.location.coordinates.latitude,
            "longitude": self.location.coordinates.longitude,
            "operator_name": self.location.operatorName,
            "suboperator_name": self.location.suboperatorName,
            "support_phonenumber": self.location.supportPhoneNumber,
            "tariff": [
                {
                    "tariff_per_kwh": connector.tariff.perKWh,
                    "currency": connector.tariff.currency,
                    "updated": connector.tariff.updated,
                    "updated_by": connector.tariff.updatedBy,
                    "structure": connector.tariff.structure,
                    "vat": self.location.vat,
                }
                for connector in evse.connectors
            ],
            "connectors": [
                {
                    "power_type": connector.electricalProperties.powerType,
                    "voltage": connector.electricalProperties.voltage,
                    "ampere": connector.electricalProperties.amperage,
                    "max_power": connector.electricalProperties.maxElectricPower,
                    "fixed_cable": connector.fixedCable,
                }
                for connector in evse.connectors
            ],
            "accessibility": self.location.accessibilityV2.status,
            "recharge_id": str(self.location.uid),
            "evse_id": str(evse.evseId),
        }
        self._attr_extra_state_attributes = extra_data


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()
