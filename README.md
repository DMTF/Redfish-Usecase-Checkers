
Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.

# Redfish-Usecase-Checkers

        Language: Python 3.x
        
This is a collection of tools to exercise and validate common use cases for DMTF Redfish. For example:

* Issue system reset commands (On, GracefulShutdown, GracefulRestart, etc.)
* Issue PATCH request for BootOverride modes, modifying BIOS/UEFI boot sequence
* Add/modify/delete Account users and roles
* If the command returns a JSON payload, it is validated against the service schema

Some of the checker tools leverage modules from [DMTF/Redfishtool](https://github.com/DMTF/Redfishtool).

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

Issue patch request and issue POST action to resetting host `127.0.0.1:8000`, with mode Once and target Pxe, with user and pass

```
$ python3 one_time_boot.py 127.0.0.1:8000 Once Pxe -u <user> -p <pass>
```

Issue patch request and issue POST action to resetting specific system `sysNumber1` on `127.0.0.1:8000`, with mode Once and target Pxe...

```
$ python3 one_time_boot.py 127.0.0.1:8000 Once Pxe -u <user> -p <pass> --target_systems sysNumber1
```

### Power control checker examples

Issue reset command `GracefulRestart` to system with Id `437XR1138R2` on host `127.0.0.1:8000` with no https security:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Never -I 437XR1138R2 GracefulRestart
```

Issue reset command `On` to the first system in the Systems collection on host `127.0.0.1:8000` with https security always enabled:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Always -F On
```

Issue reset command `On` to the only system in the Systems collection on host `127.0.0.1:8000` with https security always enabled:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Always -1 On
```

Issue reset command `Nmi` to system at link `/redfish/v1/Systems/System.Embedded.1` on host `127.0.0.1:8000` with https security always enabled:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Always -L /redfish/v1/Systems/System.Embedded.1 Nmi
```

Issue reset command `ForceOff` to system with AssatTag value `12345` on host `127.0.0.1:8000` with https security always enabled:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Always -M AssetTag:12345 ForceOff
```

Issue reset command `GracefulShutdown` to all systems in the Systems collection on host `127.0.0.1:8000` with https security always enabled:

```
$ python3 power_control.py -r 127.0.0.1:8000 -u <user> -p <password> -S Always --all GracefulShutdown
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
