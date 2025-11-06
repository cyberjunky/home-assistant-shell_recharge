# Shell Recharge

The Shell Recharge integration allows you to expose data from EV chargers on shellrecharge.com to Home Assistant.

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

**This integration will set up the following platforms.**

| Platform | Description                                                    |
| -------- | -------------------------------------------------------------- |
| `sensor` | Contains detailed information for each EV charger at location. |

## Installation

### HACS - Recommended

- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'Shell Recharge' in HACS.
- Click the Download button at the bottom of the page of the found integration.
- Restart Home Assistant.
- Under Services -> Devices & services click the Add Integration button, search for Shell Recharge.
- Configure the integration using the instructions below.

### Manual - Without HACS

- Copy the directory `custom_components/shell_recharge` to your `<config dir>/custom_components` directory.
- Restart Home Assistant.
- Configure the integration using the instructions below.

## Configuration

Find the EV charger(s) you want to monitor here: https://ui-map.shellrecharge.com look for the Serial number under details section.
Then use Add device within Home Assistant and enter the Serial number in the form.

NOTE: Sometimes added chargepoints get unavailable, most of the time this is because of serial number has changed, simply delete and re-add them with new serial.

Example:

<img width="299" alt="image" src="https://github.com/user-attachments/assets/4a6ecb02-2853-4455-90ec-8d4f41eb8b61" />

## Screenshots

| Chargers Overview                              | AC Charger Details                             | DC Charger Details                                |
| ---------------------------------------------- | ---------------------------------------------- | ------------------------------------------------- |
| ![Chargers Overview](screenshots/overview.png) | ![AC Charger Details](screenshots/details.png) | ![DC Charger Details](screenshots/details_dc.png) |

## Automation

Example flow to get notified when a charger status changes to available

```
automation:
  - alias: "Chargers Available"
    triggers:
      - trigger: state
        entity_id:
          - sensor.some_charger_1
          - sensor.some_charger_2
        from: "Occupied"
        to: "Available"
    actions:
      - action: notify.your
        data_template:
          message: >-
            Charger {{ trigger.to_state.attributes.friendly_name }} is {{ trigger.to_state.state }} from now.
```

TIP: Check this nice article by Olaf Weijers on Tweakers.net for more cool automations (Dutch)
[Laad je auto slim op met Home Assistant](https://tweakers.net/reviews/12918/laad-je-auto-slim-op-met-home-assistant-zo-vind-je-altijd-een-vrije-plek.html)

## Debugging

Add the relevant lines below to the `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.shell_recharge: debug
```

<!---->

## Contributions are welcome

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/home-assistant-shell_recharge/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40cyberjunky-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/home-assistant-shell_recharge/releases
[sponsor-shield]: https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86
[sponsor]: https://github.com/sponsors/cyberjunky
