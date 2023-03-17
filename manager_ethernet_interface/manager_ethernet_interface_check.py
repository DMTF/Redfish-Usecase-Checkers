#! /usr/bin/python3
# Copyright Notice:
# Copyright 2021 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Manager Ethernet Interface Usecase Test

File : manager_ethernet_interface_check.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for verifying Ethernet interfaces of the managers
"""

import argparse
import sys
import time

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

def dummy_address_check( address ):
    """
    Determines if values contain dummy addresses

    Args:
        address: Dictionary, list, or string containing addresses

    Returns:
        True if any of the data contains a dummy address; False otherwise
    """

    dummy_addresses = [ "", "0.0.0.0", "::" ]

    if isinstance( address, dict ):
        # Go through each property and check the value
        for property in address:
            if dummy_address_check( address[property] ):
                return True
    elif isinstance( address, list ):
        # Go through each index and check the value
        for value in address:
            if dummy_address_check( value ):
                return True
    elif isinstance( address, str ):
        if address in dummy_addresses:
            return True

    return False

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
        results = Results( "Manager Ethernet Interface", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Get the available managers
        test_managers = redfish_utilities.get_manager_ids( redfish_obj )
        manager_count = len( test_managers )
        print( "Found {} manager instances".format( manager_count ) )
        if manager_count == 0:
            results.update_test_results( "Manager Count", 1, "No manager instances were found" )
        else:
            results.update_test_results( "Manager Count", 0, None )

        # Go through each manager and test each of its Ethernet interfaces
        for manager in test_managers:
            # Get the available Ethernet interfaces
            test_interfaces = redfish_utilities.get_manager_ethernet_interface_ids( redfish_obj, manager )
            interface_count = len( test_interfaces )
            print( "Found {} Ethernet interface instances in manager '{}'".format( interface_count, manager ) )
            if interface_count == 0:
                results.update_test_results( "Ethernet Interface Count", 1, "No Ethernet interface instances were found in manager '{}'".format( manager ) )
            else:
                results.update_test_results( "Ethernet Interface Count", 0, None )

            # Go through each Ethernet interface and test the response payloads
            for interface in test_interfaces:
                print( "Testing interface '{}'".format( interface ) )
                interface_resp = redfish_utilities.get_manager_ethernet_interface( redfish_obj, manager, interface )

                # Check VLAN properties
                if "VLAN" in interface_resp.dict:
                    property_check_list = [ "VLANEnable", "VLANId", "VLANPriority", "Tagged" ]
                    req_property_check_list = [ "VLANEnable", "VLANId" ]
                    for property in property_check_list:
                        # Check if the property is null
                        if property in interface_resp.dict["VLAN"]:
                            if interface_resp.dict["VLAN"][property] is None:
                                results.update_test_results( "Null Usage", 1, "'{}' contains null values in manager '{}' interface '{}'".format( property, manager, interface ) )
                            else:
                                results.update_test_results( "Null Usage", 0, None )

                        # Check if the property is expected
                        if property in req_property_check_list:
                            if property in interface_resp.dict["VLAN"]:
                                results.update_test_results( "Expected Properties", 0, None )
                            else:
                                results.update_test_results( "Expected Properties", 1, None, "VLAN does not contain {} in manager '{}' interface '{}'".format( property, manager, interface ) )

                # Check usage of name servers
                property_check_list = [ "NameServers", "StaticNameServers", "IPv4Addresses", "IPv4StaticAddresses", "IPv6Addresses", "IPv6StaticAddresses", "IPv6DefaultGateway", "IPv6StaticDefaultGateways" ]
                property_status_list = [ "NameServers", "IPv4Addresses", "IPv6Addresses" ]
                property_ip_list = [ "IPv4Addresses", "IPv4StaticAddresses", "IPv6Addresses", "IPv6StaticAddresses", "IPv6StaticDefaultGateways" ]
                for property in property_check_list:
                    if property in interface_resp.dict:
                        # Status properties have an additional check to ensure null is not used; the array grows and shrinks based on what's active
                        if property in property_status_list:
                            if None in interface_resp.dict[property]:
                                results.update_test_results( "Null Usage", 1, "'{}' contains null values in manager '{}' interface '{}'".format( property, manager, interface ) )
                            else:
                                results.update_test_results( "Null Usage", 0, None )

                        # Check that dummy addresses are not used
                        if dummy_address_check( interface_resp.dict[property] ):
                            results.update_test_results( "Dummy Value Usage", 1, "'{}' contains an empty string, 0.0.0.0, or :: rather than null in manager '{}' interface '{}'".format( property, manager, interface ) )
                        else:
                            results.update_test_results( "Dummy Value Usage", 0, None )

                        # Check for expected IPv4 properties
                        if property in property_ip_list:
                            for i, address in enumerate( interface_resp.dict[property] ):
                                # Skip null entries
                                if address is None:
                                    continue

                                # Check that there is only a Gateway for index 0
                                if "IPv4" in property:
                                    if "Gateway" in address and i != 0:
                                        results.update_test_results( "IPv4 Gateway", 1, "IPv4 gateway property found at non-first array index in manager '{}' interface '{}'".format( manager, interface ) )
                                    else:
                                        results.update_test_results( "IPv4 Gateway", 0, None )

                                # Check for presence of properties
                                if "IPv4" in property:
                                    ip_properties = [ "Gateway", "Address", "SubnetMask" ]
                                    if "Static" not in property:
                                        ip_properties.append( "AddressOrigin" )
                                else:
                                    ip_properties = [ "Address", "PrefixLength" ]
                                    if "Static" not in property:
                                        ip_properties.append( "AddressOrigin" )
                                        ip_properties.append( "AddressState" )
                                for ip_property in ip_properties:
                                    if ip_property == "Gateway" and i == 0:
                                        continue
                                    if ip_property not in address:
                                        results.update_test_results( "Expected Properties", 1, None, "{} index {} does not contain {} in manager '{}' interface '{}'".format( property, i, ip_property, manager, interface ) )
                                    else:
                                        results.update_test_results( "Expected Properties", 0, None )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
