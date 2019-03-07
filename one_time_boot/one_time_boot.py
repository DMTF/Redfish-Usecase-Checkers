
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md

import argparse
import sys
import redfish
import os
from time import sleep

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])) + '/..')

from usecase.results import Results


def push_result_item(target, success, msg, system='Sys'):
    print(msg)
    target.append((success, msg, system))


def perform_one_time_boot(systems, context, override_enable, typeboot_target, delay):
    """
    Walks a Redfish service for Systems to perform otb on
    """
    result_test = []
    service_root = context.get("/redfish/v1/", None)
    if "Systems" not in service_root.dict:
        print("Systems link not found on service")
        result_test.append((False, 'Systems link not found on service'))
        return result_test
    systems_url = service_root.dict["Systems"]["@odata.id"].rstrip('/')
    systems_list = context.get(service_root.dict["Systems"]["@odata.id"], None)
    if (systems_list.status not in [200, 204]):
        print('Attempting to grab Systems, but status code not valid', systems_list.status)
        result_test.append(
            (False, 'Attempted to grab Systems, but returned status code not valid {}'.format(systems_list.status), 'Root'))
        return result_test
    member_list = [x['@odata.id'].split('/')[-1]
                   for x in systems_list.dict["Members"]]

    if systems is None or not len(systems):
        if len(member_list) == 1:
            systems = [x for x in member_list]
            print('No system specified, defaulting to single system,', member_list)
        else:
            print('No system specified, must specify single system:', member_list)
            result_test.append(
                (False, 'User must specify single/multiple target systems', 'Root'))
            return result_test

    for system in systems:
        if system not in member_list:
            push_result_item(
                result_test, False, 'System {} not in members of service'.format(system), system)
        else:
            push_result_item(
                result_test,
                *handleBootToSystem(context, systems_url, system, override_enable, typeboot_target, delay),
                system)
    return result_test


def handleBootToSystem(context, systems_url, system, override_enable, typeboot_target, delay):
    sutUri = '{}/{}'.format(systems_url, system)
    sutResponse = context.get(sutUri, None)

    if(sutResponse.status in [400, 404]):
        return (False, 'System {} unable to GET'.format(system))

    decoded = sutResponse.dict
    allowedValue = checkAllowedValue(decoded, typeboot_target)

    patch_response = patchBootOverride(
        context, sutUri, override_enable, typeboot_target)
    status = patch_response.status

    # reget resource
    sutResponse = context.get(sutUri, None)
    decoded = sutResponse.dict
    currentOverride, currentType = decoded['Boot'][
        'BootSourceOverrideEnabled'], decoded['Boot']['BootSourceOverrideTarget']

    if (override_enable, typeboot_target) != (currentOverride, currentType):
        if status == 400 and typeboot_target != currentType and not allowedValue:
            currentMsg = 'Boot change patch not valid, successful Bad Response'
            return (True, currentMsg)
        else:
            currentMsg = 'Boot change patch failed'
            return (False, currentMsg)
    else:
        if typeboot_target == currentType and not allowedValue:
            currentMsg = 'Boot change patch failure, value is not allowed yet is patched'
            return (False, currentMsg)
        else:
            print('Boot change patch success')

    # commit restart action, requires GracefulRestart
    postBootAction(context, sutUri, "GracefulRestart")
    sleeptime = delay

    # loop until sleeptime ends, pass if status is correct
    # reget resource
    sutResponse = context.get(sutUri, None)
    decoded = sutResponse.dict
    newOverride, newType = decoded['Boot']['BootSourceOverrideEnabled'], decoded['Boot']['BootSourceOverrideTarget']
    print('Boot status change', newOverride, newType)
    while sleeptime > 0:
        sleep(min(sleeptime, 30))
        # reget resource
        sutResponse = context.get(sutUri, None)
        decoded = sutResponse.dict
        newOverride, newType = decoded['Boot']['BootSourceOverrideEnabled'], decoded['Boot']['BootSourceOverrideTarget']
        print('Boot status change', newOverride, newType)
        sleeptime = sleeptime - 30

    successSystem = checkBootPass(
        currentOverride, currentType, newOverride, newType)
    currentMsg = 'Boot status change {}'.format(
        'FAIL' if not successSystem else 'SUCCESS')

    return (successSystem, currentMsg)


def postBootAction(context, uri, typeBoot):
    """
    Post boot action to given system
    """
    payload = {"ResetType": typeBoot}
    return context.post(uri.rstrip('/') + '/Actions/ComputerSystem.Reset', body=payload)


def patchBootOverride(context, uri, enable, target):
    """
    Patch boot override details to given system

    """
    payload = {
        "Boot": {
            "BootSourceOverrideEnabled": enable,
            "BootSourceOverrideTarget": target
        }
    }
    return context.patch(uri, body=payload)


def checkBootPass(oldOverride, oldType, newOverride, newType):
    """
    return True if input corresponds with results
    """
    return (newOverride == oldOverride == 'Continuous' and newType == oldType) or\
        (newOverride == oldOverride == 'Disabled' and newType == oldType) or\
        (newOverride == oldOverride == 'Once' and newType == 'None')


def checkAllowedValue(json, value):
    sutBoot = json.get('Boot')
    sutAllowedValues = sutBoot.get(
        'BootSourceOverrideTarget@Redfish.AllowableValues')
    return value in sutAllowedValues if sutAllowedValues is not None else False


def main(argv):
    argget = argparse.ArgumentParser(
        description='Simple tool to execute a one-time-boot function against a single or multiple systems')
    argget.add_argument(
        'rhost', type=str, help='The address of the Redfish service (with scheme)')
    argget.add_argument('override_enable', type=str,
                        help='type of boot procedure')
    argget.add_argument('typeboot_target', type=str, help='what to boot into')
    argget.add_argument('--target_systems', type=str, nargs='+',
                        help='uri points to a single system rather than a whole service')
    argget.add_argument('--delay', type=int, default=120,
                        help='optional delay time in seconds')

    argget.add_argument("--user", "-u", type=str, required=True,
                        help="The user name for authentication")
    argget.add_argument("--password", "-p", type=str,
                        required=True, help="The password for authentication")
    argget.add_argument('--auth', type=str, default='session', help='type of auth (default Session)')

    argget.add_argument('--output_result', default=None, type=str,
                        help='output directory for test information results.json, if None, do not output')

    args = argget.parse_args()

    output_dir = args.output_result

    argsList = [argv[0]]
    for name, value in vars(args).items():
        if name == "password":
            argsList.append(name + "=" + "********")
        else:
            argsList.append(name + "=" + str(value))

    # Set up the Redfish object
    redfish_obj = redfish.redfish_client(
        base_url=args.rhost, username=args.user, password=args.password, default_prefix="/redfish/v1")
    redfish_obj.login(auth=args.auth)

    service_root = redfish_obj.get("/redfish/v1/", None)
    success = service_root.status in [200, 204]

    if success:
        otb_results = perform_one_time_boot(
            args.target_systems, redfish_obj, args.override_enable, args.typeboot_target, args.delay)

    # create results object
    # TODO: this needs to be moved to seperate testing file
    # TODO: another type of user testing error to be caught is enum for onetimeboot (None, Continuous, Once...)
    results = Results(
        "One Time Boot", service_root.dict if success else dict())
    results.add_cmd_line_args(argsList)
    if output_dir is not None:
        results.set_output_dir(output_dir)

    if not success:
        results.update_test_results(
            'ServiceRoot', 1, "ServiceRoot is not available")
        cntSuccess = -1
        print("ServiceRoot is not available")
    else:
        cntSuccess = 0
        for res in otb_results:
            if(res[0]):
                cntSuccess += 1
            results.update_test_results(
                'System Tested', 0 if res[0] else 1, res[1])
        if (args.output_result):
            print('{} out of {} systems passed'.format(
                cntSuccess, len(otb_results)))

    if (args.output_result):
        results.write_results()

    redfish_obj.logout()
    return 0 if cntSuccess == len(otb_results) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
