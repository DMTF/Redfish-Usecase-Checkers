
Copyright 2017-2019 Distributed Management Task Force, Inc. All rights reserved.

# Redfish-Usecase-Checkers

        Language: Python 3.x
        
This is a collection of tools to exercise and validate common use cases for DMTF Redfish.
For example:
* Issue system reset commands (On, GracefulShutdown, GracefulRestart, etc.)
* Issue PATCH requests for BootOverride modes, modifying BIOS/UEFI boot sequence
* Add/modify/delete Account users and roles


## Prerequisites

Install `jsonschema`, `redfishtool`, `redfish`, and `redfish_utilities`:

```
pip install jsonschema
pip install redfishtool
pip install redfish
pip install redfish_utilities
```


## Example Usage

Each tool may be ran with -h, for verbose help on parameters.


### One time boot checker examples

Sets all systems found at `127.0.0.1:8000` the boot override set to either PXE or USB, and resets the system to see the boot override is performed.

```
$ python3 one_time_boot_check.py -r 127.0.0.1:8000 -u <user> -p <pass>
```


### Power/thermal info checker examples

Finds all chassis instances at `127.0.0.1:8000` and collects their respective power and thermal information.

```
$ python3 power_thermal_test.py -r 127.0.0.1:8000 -u <user> -p <pass>
```


### Power control checker examples

Performs all possible resets of systems found at `127.0.0.1:8000`:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <pass>
```


### Account management checker examples


Issue command to add user `alice` on host `127.0.0.1` with security enabled:
```
$ python3 account_management.py -r 127.0.0.1 -u root -p <pwd_for_root> -S Always adduser alice <pwd_for_alice>
```

Issue command to fetch the account for user `alice`:
```
$ python3 account_management.py -r 127.0.0.1 -u root -p <pwd_for_root> -S Always Accounts -mUserName:alice
```

Issue command to disable the account for user `alice`:
```
$ python3 account_management.py -r 127.0.0.1 -u root -p <pwd_for_root> -S Always useradmin alice disable
```

Issue command to delete the account for user `alice`:
```
$ python3 account_management.py -r 127.0.0.1 -u root -p <pwd_for_root> -S Always deleteuser alice
```

Issue command to set username for account with Id=3 to `bob`:
```
$ python3 account_management.py -r 127.0.0.1 -u root -p <pwd_for_root> -S Always setusername 3 bob
```
