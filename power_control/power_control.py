# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md

import getopt
import logging
import sys

# noinspection PyUnresolvedReferences
import toolspath
from redfishtool import ServiceRoot
from redfishtool import Systems
from redfishtool import redfishtoolTransport
from usecase.results import Results
from usecase.validation import SchemaValidation


def run_systems_operation(rft, systems):
    """
    Send Systems operation to target host
    """
    return systems.runOperation(rft)


def setup_systems_operation(args, rft, systems):
    """
    Setup the args for the operation in the rft and systems instances
    """
    rft.subcommand = args[0]
    rft.subcommandArgv = args
    rft.printVerbose(5, "power_control:setup_systems_operation: args: {}".format(args))
    if len(args) < 2:
        if rft.IdOptnCount == 0:
            systems.operation = "collection"
        else:
            systems.operation = "get"
        systems.args = None
    else:
        systems.operation = args[1]
        systems.args = args[1:]  # now args points to the 1st argument
        systems.argnum = len(systems.args)


def setup_and_run_systems_operation(args, rft, systems, reset_type):
    """
    Setup the operation, run it, print the results and return the power state
    """
    setup_systems_operation(args, rft, systems)
    rc, r, j, d = run_systems_operation(rft, systems)
    if len(args) == 1:
        command = "get"
    else:
        command = reset_type
    rft.printVerbose(1, "power_control:setup_and_run_systems_operation: command = {}, rc = {}, response = {}"
                        ", power_state = {}".format(command, rc, r, get_power_state(j, d)))
    return rc, r, j, d


def get_power_state(json_data, data):
    """
    Retrieve "PowerState" value from data if present
    """
    if json_data is True and data is not None and "PowerState" in data:
        return data["PowerState"]
    else:
        return "<n/a>"


def validate_power_state(rft, reset_type, before, after):
    """
    Verify the power state is correct after issuing the given reset command
    """
    state_after = {"On": "On", "ForceOff": "Off", "GracefulShutdown": "Off", "ForceRestart": "On",
                   "Nmi": "On", "GracefulRestart": "On", "ForceOn": "On", "PushPowerButton": "On"}
    if before == "On":
        state_after["PushPowerButton"] = "Off"
    if after == state_after[reset_type]:
        rft.printVerbose(1, "power_control:validate_power_state: Reset command {} successful".format(reset_type))
        return 0
    else:
        rft.printVerbose(1, "power_control:validate_power_state: Power state after command {} was {}, expected {}"
                         .format(reset_type, after, state_after[reset_type]))
        return 1


def validate_reset_command(rft, systems, validator, reset_type):
    """
    Issue command to perform the reset action and schema validate the response data (if any)
    """
    args = ["Systems", "reset", reset_type]
    rc, r, j, d = setup_and_run_systems_operation(args, rft, systems, reset_type)
    msg = None
    if rc != 0:
        msg = "Error issuing reset command '{}', return code = {}".format(reset_type, rc)
    if rc == 0 and j is True and d is not None:
        schema = validator.get_json_schema(d)
        rc, msg = validator.validate_json(d, schema)
    return rc, msg


def get_service_root(rft, root):
    """
    Get Service Root information
    """
    rc, r, j, d = root.getServiceRoot(rft)
    rft.printVerbose(1, "power_control:get_service_root: rc = {}, response = {}, json_data = {}, data = {}"
                     .format(rc, r, j, d))
    return d


def display_usage(pgm_name):
    """
    Display the program usage statement
    """
    print("Usage: {} [-v] [-d <output_dir>] [-u <user>] [-p <password>] -r <rhost> [-S <Secure>] [-I <Id>] <reset_type>"
          .format(pgm_name))


def log_results(results):
    """
    Log the results of the power control validation run
    """
    results.write_results()


def main(argv):
    """
    main
    """
    rft = redfishtoolTransport.RfTransport()
    systems = Systems.RfSystemsMain()
    root = ServiceRoot.RfServiceRoot()
    output_dir = None

    try:
        opts, args = getopt.gnu_getopt(argv[1:], "vu:p:r:d:I:S:", ["verbose", "user=", "password=", "rhost=",
                                                                   "directory=", "Id=", "Secure="])
    except getopt.GetoptError:
        rft.printErr("Error parsing options")
        display_usage(argv[0])
        sys.exit(1)

    for index, (opt, arg) in enumerate(opts):
        if opt in ("-v", "--verbose"):
            rft.verbose = min((rft.verbose + 1), 5)
        elif opt in ("-d", "--directory"):
            output_dir = arg
        elif opt in ("-r", "--rhost"):
            rft.rhost = arg
        elif opt in ("-u", "--user"):
            rft.user = arg
        elif opt in ("-p", "--password"):
            rft.password = arg
            # mask password, which will be logged in Results
            opts[index] = (opt, "********")
        elif opt in ("-I", "--Id"):
            rft.Id = rft.matchValue = arg
            rft.gotIdOptn = rft.gotMatchOptn = rft.firstOptn = True
            rft.IdOptnCount += 1
            rft.matchProp = "Id"
        elif opt in ("-S", "--Secure"):  # Specify when to use HTTPS
            rft.secure = arg
            if rft.secure not in rft.secureValidValues:
                rft.printErr("Invalid --Secure option: {}".format(rft.secure))
                rft.printErr("     Valid values: {}".format(rft.secureValidValues), noprog=True)
                sys.exit(1)

    if not args or len(args) > 1:
        rft.printErr("Must supply exactly one reset_type argument")
        display_usage(argv[0])
        sys.exit(1)

    reset_type = args[0]

    # Set up logging
    log_level = logging.WARNING
    if 0 < rft.verbose < 3:
        log_level = logging.INFO
    elif rft.verbose >= 3:
        log_level = logging.DEBUG
    logging.basicConfig(stream=sys.stderr, level=log_level)

    service_root = get_service_root(rft, root)
    results = Results("Power Control Checker", service_root)
    if output_dir is not None:
        results.set_output_dir(output_dir)
    args_list = [argv[0]] + [v for opt in opts for v in opt] + args
    results.add_cmd_line_args(args_list)
    auth = (rft.user, rft.password)
    nossl = True if rft.secure == "Never" else False
    validator = SchemaValidation(rft.rhost, service_root, results, auth=auth, verify=False, nossl=nossl)
    rc, msg = validate_reset_command(rft, systems, validator, reset_type)
    results.update_test_results(reset_type, rc, msg)

    log_results(results)
    exit(results.get_return_code())


if __name__ == "__main__":
    main(sys.argv)
