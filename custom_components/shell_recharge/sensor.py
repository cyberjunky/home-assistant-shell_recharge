"""Sensors for the shell_recharge integration."""

from __future__ import annotations

import logging
import typing
from typing import Any

import shellrecharge
import voluptuous as vol
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_platform, entity_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from shellrecharge.models import Location
from shellrecharge.usermodels import DetailedAssets, DetailedChargePoint, DetailedEvse

from . import (
    ShellRechargePublicDataUpdateCoordinator,
    ShellRechargeUserDataUpdateCoordinator,
)
from .const import DOMAIN, EvseId, ShellRechargeEntityFeature

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a shell_recharge_ev sensor entry."""

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        name="toggle_session",
        schema={
            vol.Required("card"): str,
            vol.Required("toggle"): str,
        },
        func="toggle_session",
    )

    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    evse_id = ""

    if coordinator.data:
        if isinstance(coordinator, ShellRechargePublicDataUpdateCoordinator):
            for evse in coordinator.data.evses:
                evse_id = evse.uid
                sensor: SensorEntity | BinarySensorEntity = ShellRechargeSensor(
                    evse_id=evse_id, coordinator=coordinator
                )
                entities.append(sensor)
        else:
            for charger in coordinator.data.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    evse_id = evse.evseId
                    sensor = ShellRechargePrivateSensor(
                        evse_id=evse_id, coordinator=coordinator
                    )
                    entities.append(sensor)
            for card in coordinator.data.chargeTokens:
                sensor = ShellCardSensor(card_id=card.uuid, coordinator=coordinator)
                entities.append(sensor)

        async_add_entities(entities, True)


class ShellRechargePrivateSensor(
    CoordinatorEntity[ShellRechargeUserDataUpdateCoordinator],
    SensorEntity,
):
    """This sensor represent a private charger."""

    def __init__(
        self, evse_id: EvseId, coordinator: ShellRechargeUserDataUpdateCoordinator
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.evse_id = evse_id
        self.coordinator = coordinator
        self.charger = self._get_charger()
        self.evse = self._get_evse()
        self._attr_unique_id = f"{evse_id}-charger"
        self._attr_attribution = "shellrecharge.com"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        self._attr_has_entity_name = False
        self._attr_name = f"{self.charger.name} {self.charger.address.street} {self.charger.address.number} {self.charger.address.city}"
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, self._attr_name)},
            entry_type=None,
            manufacturer=self.charger.vendor,
            model=self.charger.model,
        )
        self._attr_options = list(
            typing.get_args(shellrecharge.usermodels.ChargePointDetailedStatus)
        )
        self._attr_supported_features = ShellRechargeEntityFeature.TOGGLE_SESSION
        self._read_coordinator_data()

    def _get_charger(self) -> DetailedChargePoint:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for charger in assets.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    if evse.evseId == self.evse_id:
                        return charger
        raise HomeAssistantError()

    def _get_evse(self) -> DetailedEvse:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for charger in assets.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    if evse.evseId == self.evse_id:
                        return evse
        raise HomeAssistantError()

    def _read_coordinator_data(self) -> None:
        """Read data frem shell recharge charger."""
        _LOGGER.debug(self.charger)

        try:
            if self.charger and self.evse:
                self._attr_native_value = self.evse.status
                self._attr_icon = "mdi:ev-plug-type2"
                connector = self.evse.connectors[0]
                extra_data = {
                    "connector_power_type": connector.electricCurrentType,
                    "connector_max_current": connector.maxCurrentInAmps,
                    "connector_max_power": connector.maxPowerInWatts,
                    "connector_phases": connector.numberOfPhases,
                    "evse_id": self.evse.evseId,
                    "evse_uuid": self.evse.id,
                    "city": self.charger.address.city,
                    "country": self.charger.address.country,
                    "number": self.charger.address.number,
                    "street": self.charger.address.street,
                    "zip": self.charger.address.zip,
                    "connectivity": self.charger.connectivity,
                    "longitude": self.charger.coordinates.longitude,
                    "latitude": self.charger.coordinates.latitude,
                    "uuid": self.charger.id,
                    "model": self.charger.model,
                    "name": self.charger.name,
                    "plug_and_charge_capable": self.charger.plugAndCharge.capable,
                    "serial": self.charger.serial,
                    "sharing": self.charger.sharing,
                    "vendor": self.charger.vendor,
                }
                if self.evse.statusDetails.rfid:
                    extra_data["connected_card_rfid"] = self.evse.statusDetails.rfid
                if self.evse.statusDetails.printedNumber:
                    extra_data[
                        "connected_card_number"
                    ] = self.evse.statusDetails.printedNumber
                self._attr_extra_state_attributes = extra_data

        except AttributeError as err:
            _LOGGER.error(err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()

    async def toggle_session(self, **kwargs: str) -> bool:
        """Handle the service call to toggle the charge point session."""
        toggle = kwargs.get("toggle", "")
        if toggle not in ["start", "stop"]:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_toggle",
                translation_placeholders={"toggle": toggle},
            )

        card = kwargs.get("card", "")
        if not card:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_card",
                translation_placeholders={"card": card},
            )
        registry = entity_registry.async_get(self.hass)
        card_entity = registry.async_get(card)
        if not card_entity:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_card",
                translation_placeholders={"card": card},
            )
        uuid = card_entity.unique_id

        # Solely doing it like this since I'm more confident in the uniqueness
        # of the card's uuid than its rfid.
        assets: DetailedAssets = self.coordinator.data
        rfid = next(
            iter([token.rfid for token in assets.chargeTokens if token.uuid == uuid]),
            None,
        )
        if not rfid:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_card",
                translation_placeholders={"card": card},
            )

        success = await self.coordinator.toggle_session(self.charger.id, rfid, toggle)
        if not success:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="session_toggle",
                translation_placeholders={
                    "action": toggle,
                    "charger": self.charger.id,
                    "card": rfid,
                },
            )
        return True


class ShellCardSensor(
    CoordinatorEntity[ShellRechargeUserDataUpdateCoordinator],
    BinarySensorEntity,
):
    """This sensor represent a charge card."""

    def __init__(
        self, card_id: str, coordinator: ShellRechargeUserDataUpdateCoordinator
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.card_id = card_id
        self.card = self._get_card()
        self._attr_unique_id = self.card.uuid
        self._attr_attribution = "shellrecharge.com"
        # self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        self._attr_has_entity_name = False
        self._attr_name = self.card.name
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, str(self._attr_name))},
            entry_type=None,
            manufacturer="Shell",
        )
        self._attr_is_on = True
        # self._attr_options = ["enabled"]
        # self._attr_native_value = "enabled"
        self._attr_icon = "mdi:account-credit-card"
        self._attr_supported_features = ShellRechargeEntityFeature.PAY_FOR_ELECTRICITY
        self._attr_extra_state_attributes = {
            "rfid": self.card.rfid,
            "printed_number": self.card.printedNumber,
        }

    def _get_card(self) -> shellrecharge.usermodels.ChargeToken:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for card in assets.chargeTokens:
                if card.uuid == self.card_id:
                    return card
        raise HomeAssistantError()


class ShellRechargeSensor(
    CoordinatorEntity[ShellRechargePublicDataUpdateCoordinator],
    SensorEntity,
):
    """Main feature of this integration. This sensor represents an EVSE and shows its realtime availability status."""

    def __init__(
        self,
        evse_id: EvseId,
        coordinator: ShellRechargePublicDataUpdateCoordinator,
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.evse_id = evse_id
        self.coordinator = coordinator
        self.location: Location = self.coordinator.data
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
            manufacturer=operator,
        )
        self._attr_options = list(typing.get_args(shellrecharge.models.Status))
        self._read_coordinator_data()

    def _get_evse(self) -> Any:
        if self.location:
            for evse in self.location.evses:
                if evse.uid == self.evse_id:
                    return evse
        return None

    def _choose_icon(self, connectors: list[shellrecharge.models.Connector]) -> str:
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

        try:
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
                    "tariff_startfee": connector.tariff.startFee,
                    "tariff_per_kwh": connector.tariff.perKWh,
                    "tariff_per_minute": connector.tariff.perMinute,
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
                    # "opening_hours": self.location.openingHours,
                    # "predicted_occupancies": self.location.predictedOccupancies,
                }
                self._attr_extra_state_attributes = extra_data
        except AttributeError as err:
            _LOGGER.error(err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()
