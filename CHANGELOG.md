# Sinamawin - Changelog

## Unreleased

### Added

- New module (Tools->ARP) to find out the MAC addresses of the network adapter to which it is connected.
- The availability of a new version is checked and the user is informed.
- If a new network adapter is detected when the information is refreshed, it is highlighted in a different color.
- The application theme can now be changed.
- It is now possible to export all network adapter information to a CSV file.

### Fixed

- (Issue #4) When more than one IP was assigned to an interface, the "Manual" did not prevail.
- The network adapters were not getting updated in the ARP module.

## 0.2.0 (May 2024)

### Added

- Save and manage profiles and apply them to the adapter of your choice.

### Fixed

- Error setting IP due to inconsistent parameters PolicyStore PersistentStore and Dhcp Enabled. PolicyStore is now configured as ActiveStore (workaround).

## 0.1.0 (April 2024)

First version:

- View all network adapters in the computer.
- Copy all the information of each network adapter (index,name, description, status, MAC address, IP address, subnet mask, default gateway, prefix origin, suffix origin, preferred and alternate DNS server).
- Enable/disable the network adapter.
- Change the configuration of network adapters.
- Set DHCP configuration for a network adapter.
