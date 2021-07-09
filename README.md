# Redfish Usecase Checkers

Copyright 2017-2021 DMTF.  All rights reserved.

## About

        Language: Python 3.x
        
This is a collection of tools to exercise and validate common use cases for DMTF Redfish.
For example:
* Issue system reset commands (`On`, `GracefulShutdown`, `GracefulRestart`, etc.)
* Issue PATCH requests for boot override modes, modifying BIOS/UEFI boot sequence
* Add/modify/delete user accounts


## Prerequisites

Install `jsonschema`, `redfish`, and `redfish_utilities`:

```
pip install jsonschema
pip install redfish
pip install redfish_utilities
```


## Test Details and Examples

Each tool may be execuated with the `-h` option to get verbose help on parameters.


### One Time Boot Checker

This checker logs into a specified service and traverses the systems collection.
It will perform the following operations on all systems:
* Reads the `Boot` object
* Sets the `BootSourceOverrideTarget` property to either `Pxe` or `Usb`, depending on what's allowed
* Performs a reset of the system
* Monitors the `BootSourceOverrideTarget` property after the reset to ensure it changes back to `None`

Example:
```
$ python3 one_time_boot_check.py -r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```


### Power/Thermal Info Checker

This checker logs into a specified service and traverses the chassis collection.
For each chassis found, it will ensure that it can collect at least one sensor reading from the `Power` and `Thermal` resources.
For each sensor reading found, it will ensure that the readings are consistent with the state of the sensor, as in there are no bogus readings for a device that isn't present.

Example:
```
$ python3 power_thermal_test.py -r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```


### Power Control Checker

This checker logs into a specified service and traverses the system collection.
It will perform the following operations on all systems:
* Reads the allowable `ResetType` parameter values
* Performs a reset using each of the allowable `ResetType` values

Example:
```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```


### Account Management Checker

This checker logs into a specified service and performs the following operations:
* Creates a new user
* Logs into the service with the new user
* Modifies the new user with different roles
* Deletes the new user

Example:
```
$ python3 account_management.py --r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```


### Query Parameter Checker

This checker logs into a specified service and performs the following operations:
* Inspects the `ProtocolFeatures` property to see what query parameters are supported
* Tests `$filter` on the role collection within the account service
* Tests `$select` on a role within the role collection within the account service
* Tests `$expand` on service root
* Tests `only` on various resources found on service root

Example:
```
$ python3 query_parameters_check.py --r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```


### Manager Ethernet Interface Checker

This checker logs into a specified service and traverses the Ethernet interface collection in each manager found in the manager collection.
It will perform the following operations on all Ethernet interfaces:
* Inspects array properties to ensure `null` is used to show empty slots that a client is allowed to configure
* Inspects string properties containing IP addresses to ensure invalid addresses, such as `0.0.0.0`, are not used
* Inspects IPv4 address properties to ensure `Gateway` is only present in the first array index
* Ensures the minimum number of expected properties for configuring VLANs and IP addresses are present

Example:
```
$ python3 manager_ethernet_interface_check.py --r 127.0.0.1:8000 -u <user> -p <pass> -S Always
```