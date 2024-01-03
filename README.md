# Shell Recharge EV

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![Sponsor][sponsor-shield]][sponsor]

_Integration to integrate with [shell_recharge_ev][shell_recharge_ev]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show if charger is available `True` or occupied `False`.
`sensor` | Contains useful information for charger.

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'Shell Recharge EV'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home-Assistant.

### Manual
- Copy directory `custom_components/shell_recharge_ev` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Configuration

Configuration is done in the UI

## Screenshots


## Debugging

Add the relevant lines below to the `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.shell_recharge_ev: debug
```

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[shell_recharge_ev]: https://github.com/cyberjunky/home-assistant-shell_recharge_ev
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/home-assistant-shell_recharge_ev.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/home-assistant-shell_recharge_ev/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/home-assistant-shell_recharge_ev.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40cyberjunky-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/cyberjunky/home-assistant-shell_recharge_ev.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/home-assistant-shell_recharge_ev/releases
[sponsor-shield]: https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86
[sponsor]: https://github.com/sponsors/cyberjunky