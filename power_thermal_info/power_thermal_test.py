#! /usr/bin/python3
# Copyright Notice:
# Copyright 2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Power-Thermal Usecase Test

File : power_thermal_test.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for retrieving power and thermal info
"""

import argparse
import datetime
import logging
import sys

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

if __name__ == '__main__':

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "Usecase checker for power/thermal info" )
    argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
    argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
    argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service" )
    argget.add_argument( "--Secure", "-S", type = str, default = "Always", help = "When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)" )
    argget.add_argument( "--directory", "-d", type = str, default = None, help = "Output directory for results.json" )
    argget.add_argument( "--debug", action = "store_true", help = "Creates debug file showing HTTP traces and exceptions" )
    args = argget.parse_args()

    if args.debug:
        log_file = "power_thermal_test-{}.log".format( datetime.datetime.now().strftime( "%Y-%m-%d-%H%M%S" ) )
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logger = redfish.redfish_logger( log_file, log_format, logging.DEBUG )
        logger.info( "power_thermal_test Trace" )

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/" )
        results = Results( "Power/Thermal Info", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Fetch the sensors
        sensors = None
        try:
            sensors = redfish_utilities.get_sensors( redfish_obj )
        except Exception as err:
            results.update_test_results( "Chassis Count", 1, "Failed to collect sensor information ({}).".format( err ) )

    # Exit early if nothing could be returned
    if sensors is None:
        results.write_results()
        sys.exit( results.get_return_code() )

    # Print the data received
    redfish_utilities.print_sensors( sensors )

    # Test 1: Check that the chassis list is not empty
    chassis_count = len( sensors )
    print( "Found {} chassis instances".format( chassis_count ) )
    if chassis_count == 0:
        results.update_test_results( "Chassis Count", 1, "No chassis instances were found." )
    else:
        results.update_test_results( "Chassis Count", 0, None )

    # Test 2: Check that each chassis has at least one sensor
    for chassis in sensors:
        sensor_count = len( chassis["Readings"] )
        print( "Found {} sensors in Chassis '{}'".format( sensor_count, chassis["ChassisName"] ) )
        if sensor_count == 0:
            results.update_test_results( "Sensor Count", 1, "No sensors were found in Chassis '{}'.".format( chassis["ChassisName"] ) )
        else:
            results.update_test_results( "Sensor Count", 0, None )

    # Test 3: Check that all sensors not "Enabled" don't have a bogus reading
    print( "Testing sensor readings..." )
    for chassis in sensors:
        for reading in chassis["Readings"]:
            if reading["State"] is not None and reading["Reading"] is not None:
                # Both State and Reading are populated; perform the test
                if reading["State"] != "Enabled" and reading["Reading"] != reading["State"]:
                    # When State is not Enabled, Reading is supposed to be a copy of State
                    # The only time this is not true is if there is a bogus reading, such as reporting "0V" when a device is absent
                    results.update_test_results( "Sensor State", 1, "Sensor '{}' in chassis '{}' contains reading '{}', but is in state '{}'.".format(
                        reading["Name"], chassis["ChassisName"], reading["Reading"], reading["State"] ) )
                else:
                    results.update_test_results( "Sensor State", 0, None )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
