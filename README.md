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

This checker logs into a specified service and traverses the systems collection.
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
