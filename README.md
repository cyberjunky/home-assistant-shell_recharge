# Shell Recharge

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![Sponsor][sponsor-shield]][sponsor]

_Integration to integrate with [shell_recharge][shell_recharge]._

**This integration will set up the following platforms.**

| Platform | Description                                               |
| -------- | --------------------------------------------------------- |
| `sensor` | Contains detailed information for EV charger at location. |

## Installation

### HACS - Recommended

- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'Shell Recharge EV'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home-Assistant.

### Manual

- Copy directory `custom_components/shell_recharge` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Configuration

To find the serial numbers, find charger(s) to monitor here https://ui-map.shellrecharge.com/ and use the Serial number under details.

## Screenshots

## Debugging

Add the relevant lines below to the `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.shell_recharge: debug
```

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[shell_recharge]: https://github.com/cyberjunky/home-assistant-shell_recharge
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/home-assistant-shell_recharge/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40cyberjunky-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/cyberjunky/home-assistant-shell_recharge.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/home-assistant-shell_recharge/releases
[sponsor-shield]: https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86
[sponsor]: https://github.com/sponsors/cyberjunky
