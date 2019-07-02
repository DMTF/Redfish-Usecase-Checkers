#! /usr/bin/python3
# Copyright Notice:
# Copyright 2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md

"""
Power-Thermal Usecase Test

File : power_thermal_test.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for retrieving power and thermal info
"""

import argparse
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
    args = argget.parse_args()

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/", None )
        results = Results( "Power/Thermal Info", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Fetch the sensors
        sensors = redfish_utilities.get_sensors( redfish_obj )

    # Print the data received
    redfish_utilities.print_sensors( sensors )

    # Test 1: Check that the chassis list is not empty
    chassis_count = len( sensors )
    print( "Found {} chassis instances".format( chassis_count ) )
    if chassis_count == 0:
        results.update_test_results( "Chassis Count", 1, "No chassis instances were found" )
    else:
        results.update_test_results( "Chassis Count", 0, None )

    # Test 2: Check that each chassis has at least one sensor
    for chassis in sensors:
        sensor_count = len( chassis["Readings"] )
        print( "Found {} sensors in Chassis '{}'".format( sensor_count, chassis["ChassisName"] ) )
        if sensor_count == 0:
            results.update_test_results( "Sensor Count", 1, "No sensors were found in Chassis '{}'".format( chassis["ChassisName"] ) )
        else:
            results.update_test_results( "Sensor Count", 0, None )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
