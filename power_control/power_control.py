# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md

import sys
import argparse
import redfish
import traceback
from time import sleep


def push_result_item(target, success, msg, system='Sys'):
    print(msg)
    target.append((success, msg, system))


def get_power_state(json_data):
    """
    Retrieve "PowerState" value from data if present
    """
    if json_data is not None and "PowerState" in json_data:
        return json_data["PowerState"]
    else:
        return "<n/a>"


def validate_power_state(reset_type, before, after):
    """
    Verify the power state is correct after issuing the given reset command
    """
    state_after = {"On": "On", "ForceOff": "Off", "GracefulShutdown": "Off", "ForceRestart": "On",
                   "Nmi": "On", "GracefulRestart": "On", "ForceOn": "On", "PushPowerButton": "On"}
    if before == "On":
        state_after["PushPowerButton"] = "Off"
    if after == state_after.get(reset_type):
        return True
    else:
        return False


def perform_power_control(systems, context, reset_type, delay):
    """
    Walks a Redfish service for Systems to perform otb on
    """
    result_test = []
    service_root = context.get("/redfish/v1/", None)
    if "Systems" not in service_root.dict:
        currentMsg = "Systems link not found on service"
        result_test.append((False, currentMsg, 'Root'))
        return result_test

    systems_url = service_root.dict["Systems"]["@odata.id"].rstrip('/')
    systems_list = context.get(service_root.dict["Systems"]["@odata.id"], None)
    if (systems_list.status not in [200, 204]):
        currentMsg = 'Attempted to grab Systems, but returned status code not valid {}'.format(systems_list.status)
        print(currentMsg)
        result_test.append((False, currentMsg, 'Root'))
        return result_test

    member_list = [x['@odata.id'].split('/')[-1]
                   for x in systems_list.dict["Members"]]
    if systems is None or not len(systems):
        if len(member_list) == 1:
            systems = [x for x in member_list]
            print('No system specified, defaulting to single system,', member_list)
        else:
            print('No system specified, must specify single system:', member_list)
            result_test.append((False, 'User must specify single/multiple target systems', 'Root'))
            return result_test

    if 'All' in systems:
        systems = member_list

    for system in systems:
        if system not in member_list:
            push_result_item(
                result_test,
                False,
                'System {} not in members of service'.format(system),
                system)
        else:
            push_result_item(
                result_test,
                *handlePowControlToSystem(context, systems_url, system, reset_type, delay),
                system)
    return result_test


def handlePowControlToSystem(context, systems_url, system, reset_type="GracefulRestart", delay=30):
    sutUri = '{}/{}'.format(systems_url, system)
    sutResponse = context.get(sutUri, None)

    if(sutResponse.status in [400, 404]):
        return (False, 'System {} unable to GET'.format(system))

    decoded = sutResponse.dict

    currentValue = get_power_state(decoded)

    # commit restart action, requires GracefulRestart
    postBootAction(context, sutUri, reset_type)
    sleeptime = delay

    # loop until sleeptime ends, pass if status is correct
    # reget resource
    # TODO: replace with 202 task if available
    sutResponse = context.get(sutUri, None)
    decoded = sutResponse.dict
    newValue = get_power_state(decoded)
    print('Boot status change', currentValue, newValue)
    while sleeptime > 0:
        sleep(min(sleeptime, 30))
        # reget resource
        sutResponse = context.get(sutUri, None)
        newValue = get_power_state(decoded)
        print('Boot status change', currentValue, newValue)
        sleeptime = sleeptime - 30

    successSystem = validate_power_state(reset_type, currentValue, newValue)
    currentMsg = 'Boot status change {}'.format(
        'FAIL' if not successSystem else 'SUCCESS')

    return (successSystem, currentMsg)


def postBootAction(context, uri, typeBoot):
    """
    Post boot action to given system
    """
    payload = {"ResetType": typeBoot}
    return context.post(uri.rstrip('/') + '/Actions/ComputerSystem.Reset', body=payload)


def main_arg_setup():
    argget = argparse.ArgumentParser(
        description='Simple tool to execute a one-time-boot function against a single or multiple systems')
    argget.add_argument('rhost', type=str,
            help='The address of the Redfish service (with scheme)')
    argget.add_argument('--shutdown_type', type=str, default='GracefulRestart',
            help='type of shutdown')
    argget.add_argument('--target_systems', type=str, nargs='+',
            help='A list of systems to target i.e System1 System2 System3')
    argget.add_argument('--delay', type=int, default=120,
            help='optional delay time in seconds to determine success')

    argget.add_argument("--Secure", "-S", type=str, default="Always",
            help="When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)")
    argget.add_argument("--user", "-u", type=str,
            required=True,
            help="The user name for authentication")
    argget.add_argument("--password", "-p", type=str,
            required=True,
            help="The password for authentication")
    argget.add_argument('--auth', type=str, default='session',
            help='type of auth of either Session, Basic, None (default Session)')
    return argget


def main(argv):
    argget = main_arg_setup()
    args = argget.parse_args()

    # Set up the Redfish object
    if ('://' in args.rhost):
        print('Argument rhost should not contain scheme http/https')

    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost

    print('Contacting {}'.format(base_url))

    try:
        redfish_obj = redfish.redfish_client(
            base_url=base_url, username=args.user, password=args.password, default_prefix="/redfish/v1")
        redfish_obj.login(auth=args.auth)
    except Exception as e:
        print('Exception has occurred when creating redfish object')
        print(traceback.format_exc(2))
        return 1

    service_root = redfish_obj.get("/redfish/v1/", None)
    success = service_root.status in [200, 204]

    pc_results = []

    if success:
        pc_results = perform_power_control(
            args.target_systems, redfish_obj, args.shutdown_type, args.delay)

    # TODO: another type of user testing error to be caught is enum for onetimeboot (None, Continuous, Once...)

    if not success:
        cntSuccess = -1
        print("ServiceRoot is not available")
    else:
        cntSuccess = 0
        for res in pc_results:
            if(res[0]):
                cntSuccess += 1
        print('{} out of {} systems successful action'.format(
            cntSuccess, len(pc_results)))

    redfish_obj.logout()
    return 0 if cntSuccess == len(pc_results) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))

if __name__ == "__main__":
    main(sys.argv)
