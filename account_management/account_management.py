# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md

import getopt
import re
import sys

# noinspection PyUnresolvedReferences
import toolspath
from redfishtool import AccountService
from redfishtool import ServiceRoot
from redfishtool import raw
from redfishtool import redfishtoolTransport
from usecase.results import Results
from usecase.validation import SchemaValidation


def run_account_operation(rft, account):
    """
    Send AccountService operation to remote host
    """
    return account.runOperation(rft)


def setup_account_operation(args, rft, account):
    """
    Setup the args for the operation in the rft and account_service instances
    """
    rft.subcommand = args[0]
    rft.subcommandArgv = args
    rft.printVerbose(5, "account_management:setup_account_operation: args: {}".format(args))
    # if no args, this is an AccountService 'get' command
    if len(args) < 2:
        account.operation = "get"
        account.args = None
    else:
        account.operation = args[1]
        account.args = args[1:]  # now args points to the 1st argument
        account.argnum = len(account.args)


def setup_and_run_account_operation(args, rft, account):
    """
    Setup the operation, run it, print the results and return the results
    """
    setup_account_operation(args, rft, account)
    rc, r, j, d = run_account_operation(rft, account)
    rft.printVerbose(1, "account_management:setup_and_run_account_operation: " +
                     "rc = {}, response = {}, json_data = {}, data = {}"
                     .format(rc, r, j, d))
    return rc, r, j, d


def validate_account_command(rft, account, validator, args):
    """
    Perform the account operation and validate the returned payload against the schema
    """
    rc, r, j, d = setup_and_run_account_operation(args, rft, account)
    msg = None
    if rc != 0:
        msg = "Error issuing '{}' command, return code = {}".format(args[1], rc)
    if rc == 0 and j is True and d is not None:
        schema = validator.get_json_schema(d)
        rc, msg = validator.validate_json(d, schema)
    return rc, msg


def get_service_root(rft, root):
    """
    Get Service Root information
    """
    rc, r, j, d = root.getServiceRoot(rft)
    rft.printVerbose(1, "account_management:get_service_root: rc = {}, response = {}, json_data = {}, data = {}"
                     .format(rc, r, j, d))
    return d


def display_usage(pgm_name):
    print("Usage: {} [-v] [-d <output_dir>] [-u <user>] [-p <password>] -r <rhost> [-S <Secure>]".format(pgm_name))
    print("       [-i <id>] [-m <prop>:<value>] [<op> [<op_args> ...]]")


def log_results(results):
    """
    Log the results of the account management validation run
    """
    results.write_results()


def main(argv):
    """
    main
    """
    rft = redfishtoolTransport.RfTransport()
    account = AccountService.RfAccountServiceMain()
    root = ServiceRoot.RfServiceRoot()
    raw_main = raw.RfRawMain()
    output_dir = None

    try:
        opts, args = getopt.gnu_getopt(argv[1:], "vu:p:r:d:i:m:S:", ["verbose", "user=", "password=", "rhost=",
                                                                     "directory=", "id=", "match=", "Secure="])
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
            # mask password in 'opts', which will be logged in Results
            opts[index] = (opt, "********")
        elif opt in ("-i", "--id"):
            rft.IdLevel2 = rft.matchLevel2Value = arg
            rft.gotIdLevel2Optn = rft.gotMatchLevel2Optn = True
            rft.IdLevel2OptnCount += 1
            rft.matchLevel2Prop = "Id"
        elif opt in ("-m", "--match"):
            # arg is of the form: "<prop>:<value>"
            match_prop_pattern = "^(.+):(.+)$"
            match_prop_match = re.search(match_prop_pattern, arg)
            if match_prop_match:
                rft.matchLevel2Prop = match_prop_match.group(1)
                rft.matchLevel2Value = match_prop_match.group(2)
                rft.IdLevel2OptnCount += 1
                rft.gotMatchLevel2Optn = True
            else:
                rft.printErr("Invalid level2 --match= option format: {}".format(arg))
                rft.printErr("     Expect --match=<prop>:<value> Ex -m ProcessorType:CPU, --match=ProcessorType:CPU",
                             noprog=True)
                sys.exit(1)
        elif opt in ("-S", "--Secure"):  # Specify when to use HTTPS
            rft.secure = arg
            if rft.secure not in rft.secureValidValues:
                rft.printErr("Invalid --Secure option: {}".format(rft.secure))
                rft.printErr("     Valid values: {}".format(rft.secureValidValues), noprog=True)
                sys.exit(1)

    # check for invalid Level-2 collection member reference options
    if rft.IdLevel2OptnCount > 1:
        rft.printErr("Syntax error: invalid mix of options -i and -m used to specify a 2nd-level collection member.")
        rft.printErr("    Valid combinations: -i | -m ", noprog=True)
        display_usage(argv[0])
        sys.exit(1)

    if not args:
        # if no args, use the default scenario (add, get, modify, delete user)
        user = "alice73t"
        scenario_list = [["AccountService", "adduser", user, "hUPgd9Z4"],
                         ["AccountService", "useradmin", user, "disable"],
                         ["AccountService", "deleteuser", user],
                         ["AccountService", "Accounts"]]
    else:
        scenario_list = [["AccountService"] + args]

    service_root = get_service_root(rft, root)
    results = Results("Account Management Checker", service_root)
    if output_dir is not None:
        results.set_output_dir(output_dir)
    args_list = [v for opt in opts for v in opt] + args
    results.add_cmd_line_args(args_list)
    validator = SchemaValidation(rft, service_root, raw_main, results)
    for scenario in scenario_list:
        rc, msg = validate_account_command(rft, account, validator, scenario)
        results.update_test_results(scenario[1], rc, msg)

    log_results(results)
    exit(results.get_return_code())


if __name__ == "__main__":
    main(sys.argv)
