#! /usr/bin/python3
# Copyright Notice:
# Copyright 2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
One Time Boot Usecase Test

File : one_time_boot_check.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for performing a one time boot
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
    argget = argparse.ArgumentParser( description = "Usecase checker for one time boot" )
    argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
    argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
    argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service" )
    argget.add_argument( "--Secure", "-S", type = str, default = "Always", help = "When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)" )
    argget.add_argument( "--directory", "-d", type = str, default = None, help = "Output directory for results.json" )
    args = argget.parse_args()

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/" )
        results = Results( "One Time Boot", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Get the available systems
        test_systems = []
        system_col = redfish_obj.get( service_root.dict["Systems"]["@odata.id"] )
        for member in system_col.dict["Members"]:
            system = redfish_obj.get( member["@odata.id"] )
            test_systems.append( system.dict["Id"] )

        # Check that the system list is not empty
        system_count = len( test_systems )
        print( "Found {} system instances".format( system_count ) )
        if system_count == 0:
            results.update_test_results( "System Count", 1, "No system instances were found" )
        else:
            results.update_test_results( "System Count", 0, None )

        # Perform a test on each system found
        for system in test_systems:
            # See if PXE or USB are allowable
            test_path = None
            boot_obj = redfish_utilities.get_system_boot( redfish_obj, system )
            if "BootSourceOverrideTarget@Redfish.AllowableValues" in boot_obj:
                if "Pxe" in boot_obj["BootSourceOverrideTarget@Redfish.AllowableValues"]:
                    test_path = "Pxe"
                elif "Usb" in boot_obj["BootSourceOverrideTarget@Redfish.AllowableValues"]:
                    test_path = "Usb"
            else:
                test_path = "Pxe"
            if test_path is None:
                print( "{} does not support PXE or USB boot override".format( system ) )
                results.update_test_results( "Boot Check", 0, "{} does not allow for PXE or USB boot override.".format( system ), skipped = True )
                results.update_test_results( "Continuous Boot Set", 0, "{} does not allow for PXE or USB boot override.".format( system ), skipped = True )
                results.update_test_results( "Boot Set", 0, "{} does not allow for PXE or USB boot override.".format( system ), skipped = True )
                results.update_test_results( "Boot Verify", 0, "{} does not allow for PXE or USB boot override.".format( system ), skipped = True )
                continue
            results.update_test_results( "Boot Check", 0, None )

            # Check that Continuous is allowed to be applied to the boot override settings
            print( "Setting {} to boot continuously from {}".format( system, test_path ) )
            try:
                redfish_utilities.set_system_boot( redfish_obj, system_id = system, ov_target = test_path, ov_enabled = "Continuous" )
                boot_obj = redfish_utilities.get_system_boot( redfish_obj, system )
                if boot_obj["BootSourceOverrideTarget"] != test_path and boot_obj["BootSourceOverrideEnabled"] != "Continuous":
                    raise ValueError( "Boot object was not modified after PATCH" )
                else:
                    results.update_test_results( "Continuous Boot Set", 0, None )
            except Exception as err:
                results.update_test_results( "Continuous Boot Set", 1, "Failed to set {} to continuously boot from {} ({}).".format( system, test_path, err ) )

            # Set the boot object and verify the setting was applied
            print( "Setting {} to boot from {}".format( system, test_path ) )
            try:
                redfish_utilities.set_system_boot( redfish_obj, system_id = system, ov_target = test_path, ov_enabled = "Once" )
                boot_obj = redfish_utilities.get_system_boot( redfish_obj, system )
                if boot_obj["BootSourceOverrideTarget"] != test_path and boot_obj["BootSourceOverrideEnabled"] != "Once":
                    raise ValueError( "Boot object was not modified after PATCH" )
                else:
                    results.update_test_results( "Boot Set", 0, None )

                    # Reset the system
                    print( "Resetting {}".format( system ) )
                    try:
                        response = redfish_utilities.system_reset( redfish_obj, system )
                        response = redfish_utilities.poll_task_monitor( redfish_obj, response )
                        redfish_utilities.verify_response( response )

                        # Monitor the system to go back to None
                        print( "Monitoring boot progress for {}...".format( system ) )
                        for i in range( 0, 300 ):
                            time.sleep( 1 )
                            boot_obj = redfish_utilities.get_system_boot( redfish_obj, system )
                            if boot_obj["BootSourceOverrideEnabled"] == "Disabled":
                                break
                        if boot_obj["BootSourceOverrideEnabled"] == "Disabled":
                            print( "{} booted from {}!".format( system, test_path ) )
                            results.update_test_results( "Boot Verify", 0, None )
                        else:
                            raise ValueError( "{} did not reset back to 'Disabled'".format( system ) )
                    except Exception as err:
                        results.update_test_results( "Boot Verify", 1, "{} failed to boot from {}.".format( system, test_path ) )
            except Exception as err:
                results.update_test_results( "Boot Set", 1, "Failed to set {} to boot from {} ({}).".format( system, test_path, err ) )
                results.update_test_results( "Boot Verify", 0, "Boot setting not applied.", skipped = True )

            # Cleanup (should be clean already if everything passed)
            try:
                redfish_utilities.set_system_boot( redfish_obj, system_id = system, ov_target = "None", ov_enabled = "Disabled" )
            except:
                pass

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
