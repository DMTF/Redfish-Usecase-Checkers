# Copyright Notice:
# Copyright 2017-2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Power Control Usecase Test

File : power_control.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for performing reset and power operations
"""

import argparse
import sys
import time

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

if __name__ == '__main__':

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "Usecase checker for power and reset operations" )
    argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
    argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
    argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service" )
    argget.add_argument( "--Secure", "-S", type = str, default = "Always", help = "When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)" )
    argget.add_argument( "--directory", "-d", type = str, default = None, help = "Output directory for results.json" )
    argget.add_argument( "--timeout", "-t", type = int, default = 10, help = "Length of each timeout after reset" )
    args = argget.parse_args()

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/" )
        results = Results( "Power Control", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Get the available systems
        test_systems = []
        system_col = redfish_obj.get( service_root.dict["Systems"]["@odata.id"] )
        for member in system_col.dict["Members"]:
            system = redfish_obj.get( member["@odata.id"] )
            test_systems.append( { "Id": system.dict["Id"], "URI": member["@odata.id"] } )

        # Check that the system list is not empty
        system_count = len( test_systems )
        print( "Found {} system instances".format( system_count ) )
        if system_count == 0:
            results.update_test_results( "System Count", 1, "No system instances were found." )
        else:
            results.update_test_results( "System Count", 0, None )

        # Perform a test on each system found
        for system in test_systems:
            # Check what types of resets are supported
            try:
                reset_types = None
                reset_uri, reset_params = redfish_utilities.get_system_reset_info( redfish_obj, system["Id"] )
            except Exception as err:
                results.update_test_results( "Reset Type Check", 1, "Could not get reset info for {} ({}).".format( system["Id"], err ) )
                continue

            for param in reset_params:
                if param["Name"] == "ResetType":
                    reset_types = param["AllowableValues"]
            if reset_types is None:
                results.update_test_results( "Reset Type Check", 1, "{} is not advertising any allowable resets.".format( system["Id"] ) )
                continue
            results.update_test_results( "Reset Type Check", 0, None )

            # Reset the system
            for reset_type in reset_types:
                if reset_type == "Nmi":
                    # NMI could fail depending on the state of the system; no real reason to test this at this time
                    continue
                print( "Resetting {} using {}".format( system["Id"], reset_type ) )
                try:
                    response = redfish_utilities.system_reset( redfish_obj, system["Id"], reset_type )
                    response = redfish_utilities.poll_task_monitor( redfish_obj, response )
                    redfish_utilities.verify_response( response )
                    results.update_test_results( "Reset Performed", 0, None )
                except Exception as err:
                    results.update_test_results( "Reset Performed", 1, "Failed to reset {} using {} ({})".format( system["Id"], reset_type, err ) )
                    continue

                # Allow some time before checking the power state
                # We also might skip the PowerState check and want to allow for the system to settle before performing another reset
                time.sleep( args.timeout )

                # Check the power state to ensure it's in the proper state
                exp_power_state = "On"
                if reset_type == "ForceOff" or reset_type == "GracefulShutdown":
                    exp_power_state = "Off"
                if reset_type == "PushPowerButton":
                    # Depending on the system design, pushing the button can have different outcomes with regards to the power state
                    continue
                print( "Monitoring power state for {}...".format( system["Id"] ) )
                power_state = None
                for i in range( 0, 10 ):
                    system_info = redfish_obj.get( system["URI"] )
                    power_state = system_info.dict.get( "PowerState" )
                    if power_state is None or power_state == exp_power_state:
                        break
                    time.sleep( 5 )
                if power_state is not None:
                    if power_state != exp_power_state:
                        results.update_test_results( "Power State Check", 1, "{} was not in the {} state after using {} as the reset type.".format( system["Id"], exp_power_state, reset_type ) )
                    else:
                        results.update_test_results( "Power State Check", 0, None )
                else:
                    results.update_test_results( "Power State Check", 0, "{} does not contain the PowerState property.".format( system["Id"] ), skipped = True )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
