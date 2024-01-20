"""Sensors for the shell_recharge_ev integration."""
from __future__ import annotations

import logging
import typing
from typing import Any

import shellrechargeev
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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
    evse_id = ""

    for evse in coordinator.data.evses:
        evse_id = evse.uid
        sensor = ShellRechargeEVSensor(evse_id=evse_id, coordinator=coordinator)
        entities.append(sensor)

    async_add_entities(entities, True)


class ShellRechargeEVSensor(
    CoordinatorEntity[ShellRechargeEVDataUpdateCoordinator], SensorEntity  # type: ignore
):
    """Main feature of this integration. This sensor represents an EVSE and shows its realtime availability status."""

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
        if "suboperatorName" in self.location and self.location.suboperatorName:
            operator = self.location.suboperatorName
        else:
            operator = self.location.operatorName
        self._attr_has_entity_name = False
        self._attr_name = f"{operator} {self.location.address.streetAndNumber} {self.location.address.city}"
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, self._attr_name)},
            entry_type=None,
        )
        self._attr_options = list(typing.get_args(shellrechargeev.models.Status))
        self._read_coordinator_data()

    def _get_evse(self) -> Any:
        for evse in self.coordinator.data.evses:
            if evse.uid == self.evse_id:
                return evse

    def _choose_icon(self, connectors: list[shellrechargeev.models.Connector]) -> str:
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
            "Unspecified": "mdi:ev-station",
        }
        if len(connectors) != 1:
            return "mdi:ev-station"
        return iconmap.get(connectors[0].connectorType, "mdi:ev-station")

    def _read_coordinator_data(self) -> None:
        """Read data from shell recharge ev."""
        evse = self._get_evse()
        _LOGGER.debug(evse)
        if evse:
            self._attr_native_value = evse.status
            self._attr_icon = self._choose_icon(evse.connectors)
            connector = evse.connectors[0]
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
                "tariff_per_kwh": connector.tariff.perKWh,
                "tariff_currency": connector.tariff.currency,
                "tariff_updated": connector.tariff.updated,
                "tariff_updated_by": connector.tariff.updatedBy,
                "tariff_structure": connector.tariff.structure,
                "connector_power_type": connector.electricalProperties.powerType,
                "connector_voltage": connector.electricalProperties.voltage,
                "connector_ampere": connector.electricalProperties.amperage,
                "connector_max_power": connector.electricalProperties.maxElectricPower,
                "connector_fixed_cable": connector.fixedCable,
                "accessibility": self.location.accessibilityV2.status,
                "external_id": str(self.location.externalId),
                "evse_id": str(evse.evseId),
                "opentwentyfourseven": self.location.openTwentyFourSeven,
            }
            self._attr_extra_state_attributes = extra_data

    @callback  # type: ignore
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()
