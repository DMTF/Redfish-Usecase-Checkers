#! /usr/bin/python3
# Copyright Notice:
# Copyright 2021 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Query Parameters Usecase Test

File : query_parameters_check.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for query parameters
"""

import argparse
import sys
import time

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

def filter_test( redfish_obj, service_root, results ):
    """
    Tests the $filter query parameter

    Args:
        redfish_obj: The Redfish client object with an open session
        service_root: The service root response
        results: The results output
    """

    # Ensure there's an account service and at least one role available
    if "AccountService" not in service_root.dict:
        results.update_test_results( "Filter Check", 0, "Account service not found for testing.", skipped = True )
        return
    account_service = redfish_obj.get( service_root.dict["AccountService"]["@odata.id"] )
    if "Roles" not in account_service.dict:
        results.update_test_results( "Filter Check", 0, "Role collection not found for testing.", skipped = True )
        return
    role_collection_uri = account_service.dict["Roles"]["@odata.id"]
    role_collection = redfish_obj.get( role_collection_uri )
    role_count = len( role_collection.dict["Members"] )
    if role_count == 0:
        results.update_test_results( "Filter Check", 0, "Role collection is empty.", skipped = True )
        return

    # Get the first and last roles to be used for building $filter parameters
    role_first = redfish_obj.get( role_collection.dict["Members"][0]["@odata.id"] )
    role_first_uri = role_first.dict["@odata.id"]
    role_last = redfish_obj.get( role_collection.dict["Members"][-1]["@odata.id"] )
    first_and_last = 2
    if role_first == role_last:
        first_and_last = 1

    # Perform various $filter requests on the collection and check the members returned
    filter_checks = [
        {
            "Description": "Match exactly one",
            "Query": { "$filter": "Id eq '" + role_first.dict["Id"] + "'" },
            "ExpectedLength": 1
        },
        {
            "Description": "Match exactly everything except one",
            "Query": { "$filter": "not (Id eq '" + role_first.dict["Id"] + "')" },
            "ExpectedLength": role_count - 1
        },
        {
            "Description": "Match first or last",
            "Query": { "$filter": "Id eq '" + role_first.dict["Id"] + "'" + " or Id eq '" + role_last.dict["Id"] + "'" },
            "ExpectedLength": first_and_last
        }
    ]
    for check in filter_checks:
        query_str = "$filter=" + check["Query"]["$filter"]
        print( "Performing $filter={} on {}".format( query_str, role_collection_uri ) )
        filter_list = redfish_obj.get( role_collection_uri, args = check["Query"] )
        redfish_utilities.verify_response( filter_list )
        filter_count = len( filter_list.dict["Members"] )
        if filter_count != check["ExpectedLength"]:
            results.update_test_results( "Filter Check", 1, "Query ({}) expected to return {} member(s); received {}.".format( query_str, check["ExpectedLength"], filter_count ) )
        else:
            results.update_test_results( "Filter Check", 0, None )

    # Perform a $filter query on an individual role and ensure the request is rejected
    query = { "$filter": "Id eq '" + role_first.dict["Id"] + "'" }
    query_str = "$filter=" + query["$filter"]
    print( "Performing {} on {}".format( query_str, role_first_uri ) )
    filter_response = redfish_obj.get( role_first_uri, args = query )
    try:
        redfish_utilities.verify_response( filter_response )
        results.update_test_results( "Filter Check", 1, "Query ({}) expected to result in an error, but succeeded.".format( query_str ) )
    except:
        results.update_test_results( "Filter Check", 0, None )

def select_test( redfish_obj, service_root, results ):
    """
    Tests the $select query parameter

    Args:
        redfish_obj: The Redfish client object with an open session
        service_root: The service root response
        results: The results output
    """

    # Ensure there's an account service and at least one role available
    if "AccountService" not in service_root.dict:
        results.update_test_results( "Select Check", 0, "Account service not found for testing.", skipped = True )
        return
    account_service = redfish_obj.get( service_root.dict["AccountService"]["@odata.id"] )
    if "Roles" not in account_service.dict:
        results.update_test_results( "Select Check", 0, "Role collection not found for testing.", skipped = True )
        return
    role_collection = redfish_obj.get( account_service.dict["Roles"]["@odata.id"] )
    role_count = len( role_collection.dict["Members"] )
    if role_count == 0:
        results.update_test_results( "Select Check", 0, "Role collection is empty.", skipped = True )
        return

    # Get the first role to be used for $select testing
    role_first = redfish_obj.get( role_collection.dict["Members"][0]["@odata.id"] )
    role_first_uri = role_first.dict["@odata.id"]

    # Perform the query
    query = { "$select": "Name,AssignedPrivileges" }
    query_str = "$select=" + query["$select"]
    print( "Performing {} on {}".format( query_str, role_first_uri ) )
    select_response = redfish_obj.get( role_first_uri, args = query )
    redfish_utilities.verify_response( select_response )

    # Check the response for the expected properties
    required_properties = [ "@odata.id", "@odata.type", "Name", "AssignedPrivileges" ]
    optional_properties = [ "@odata.context", "@odata.etag" ]
    select_dict = select_response.dict
    for required in required_properties:
        if required not in select_dict:
            results.update_test_results( "Select Check", 1, "Query ({}) response expected to contain property {}.".format( query_str, required ) )
            return
        if select_dict[required] != role_first.dict[required]:
            results.update_test_results( "Select Check", 1, "Query ({}) response contains different property value for {}.".format( query_str, required ) )
            return
        select_dict.pop( required )
    for optional in optional_properties:
        if optional in select_dict and optional in role_first.dict:
            if select_dict[optional] != role_first.dict[optional]:
                results.update_test_results( "Select Check", 1, "Query ({}) response contains different property value for {}.".format( query_str, optional ) )
                return
            select_dict.pop( optional )
        elif optional not in select_dict and optional in role_first.dict:
            results.update_test_results( "Select Check", 1, "Query ({}) response expected to contain property {}.".format( query_str, optional ) )
            return
    for extra in select_dict:
        results.update_test_results( "Select Check", 1, "Query ({}) response contains extra property {}.".format( query_str, extra ) )
        return

    results.update_test_results( "Select Check", 0, None )

def verify_expand( results, query, name, value, is_expanded ):
    """
    Verifies an object is expanded properly

    Args:
        results: The results output
        query: The query string used
        name: The name of the property
        value: The value of the property
        is_expanded: If expansion is expected
    """

    query_str = "$expand=" + query["$expand"]
    if "@odata.id" in value:
        if len( value ) == 1:
            if is_expanded:
                results.update_test_results( "Expand Check", 1, "Query ({}) expected to expand resource {}.".format( query_str, name ) )
            else:
                results.update_test_results( "Expand Check", 0, None )
        else:
            if is_expanded:
                results.update_test_results( "Expand Check", 0, None )
            else:
                results.update_test_results( "Expand Check", 1, "Query ({}) expected to not expand subordinate resource {}.".format( query_str, name) )

def expand_test( redfish_obj, service_root, results ):
    """
    Tests the $expand query parameter

    Args:
        redfish_obj: The Redfish client object with an open session
        service_root: The service root response
        results: The results output
    """

    expand_checks = [
        { "Term": "ExpandAll", "Query": { "$expand": "*" }, "Sub": True, "Links": True, "Levels": False },
        { "Term": "NoLinks", "Query": { "$expand": "." }, "Sub": True, "Links": False, "Levels": False },
        { "Term": "Links", "Query": { "$expand": "~" }, "Sub": False, "Links": True, "Levels": False },
        { "Term": "ExpandAll", "Query": { "$expand": "*($levels=1)" }, "Sub": True, "Links": True, "Levels": True },
        { "Term": "NoLinks", "Query": { "$expand": ".($levels=1)" }, "Sub": True, "Links": False, "Levels": True },
        { "Term": "Links", "Query": { "$expand": "~($levels=1)" }, "Sub": False, "Links": True, "Levels": True }
    ]

    # Go through each of the different expand types
    check_uri = "/redfish/v1/"
    for check in expand_checks:
        if not service_root.dict["ProtocolFeaturesSupported"]["ExpandQuery"].get( check["Term"], False ):
            results.update_test_results( "Expand Check", 0, "{} not supported.".format( check["Term"] ), skipped = True )
            continue

        if not service_root.dict["ProtocolFeaturesSupported"]["ExpandQuery"].get( "Levels", False ) and check["Levels"]:
            results.update_test_results( "Expand Check", 0, "Levels not supported on $expand".format( check["Term"] ), skipped = True )
            continue

        # Perform the query on service root
        print( "Performing $expand={} on {}".format( check["Query"]["$expand"], check_uri ) )
        expand_response = redfish_obj.get( check_uri, args = check["Query"] )
        redfish_utilities.verify_response( expand_response )

        # Check the response to ensure things are expanded properly
        for property in expand_response.dict:
            if property == "Links":
                # Links object; scan it for expansion
                for link_property in expand_response.dict[property]:
                    if isinstance( expand_response.dict[property][link_property], dict ):
                        verify_expand( results, check["Query"], link_property, expand_response.dict[property][link_property], check["Links"] )
                    elif isinstance( expand_response.dict[property][link_property], list ):
                        for link_item in expand_response.dict[property][link_property]:
                            verify_expand( results, check["Query"], link_property, link_item, check["Links"] )
            elif isinstance( expand_response.dict[property], dict ):
                # Non-Links object; check if this is a reference object and if it was expanded properly
                verify_expand( results, check["Query"], property, expand_response.dict[property], check["Sub"] )

def only_test( redfish_obj, service_root, results ):
    """
    Tests the only query parameter

    Args:
        redfish_obj: The Redfish client object with an open session
        service_root: The service root response
        results: The results output
    """

    # List of service root properties to inspect; True indicates if the reference is to a collection
    only_checks = {
        "AccountService": False,
        "SessionService": False,
        "Chassis": True,
        "Systems": True,
        "Managers": True
    }

    # Go through each of the service root properties and test the only query
    query = { "only": None }
    query_str = "only"
    for check in only_checks:
        if check not in service_root.dict:
            results.update_test_results( "Only Check", 0, "{} not found for testing.".format( check ), skipped = True )
            continue

        check_uri = service_root.dict[check]["@odata.id"]
        if only_checks[check]:
            # Testing a collection
            print( "Performing {} on {}".format( query_str, check_uri ) )
            only_response = redfish_obj.get( check_uri, args = query )
            redfish_utilities.verify_response( only_response )
            resource_response = redfish_obj.get( check_uri )
            redfish_utilities.verify_response( resource_response )
            if len( resource_response.dict["Members"] ) == 1:
                # Collection has exactly one member; query response is supposed to be the one member
                if only_response.dict["@odata.id"] == resource_response.dict["Members"][0]["@odata.id"]:
                    results.update_test_results( "Only Check", 0, None )
                else:
                    results.update_test_results( "Only Check", 1, "Query ({}) response for {} expected the only collection member.".format( query_str, check_uri ) )
            else:
                # Collection does not have exactly one member; query response is supposed to be the collection itself
                if only_response.dict["@odata.id"] != resource_response.dict["@odata.id"] or "Members" not in only_response.dict:
                    results.update_test_results( "Only Check", 1, "Query ({}) response for {} expected the collection itself.".format( query_str, check_uri ) )
                else:
                    results.update_test_results( "Only Check", 0, None )
        else:
            # Testing a singular resource; this is supposed to produce an error for the client
            print( "Performing {} on {}".format( query_str, check_uri ) )
            only_response = redfish_obj.get( check_uri, args = query )
            try:
                redfish_utilities.verify_response( only_response )
                results.update_test_results( "Only Check", 1, "Query ({}) expected to result in an error for {}, but succeeded.".format( query_str, check_uri ) )
            except:
                results.update_test_results( "Only Check", 0, None )

if __name__ == '__main__':

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "Usecase checker for query parameters" )
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
        results = Results( "Query Parameters", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        if "ProtocolFeaturesSupported" in service_root.dict:
            if service_root.dict["ProtocolFeaturesSupported"].get( "FilterQuery", False ):
                try:
                    filter_test( redfish_obj, service_root, results )
                except Exception as err:
                    results.update_test_results( "Filter Check", 1, "Failed to perform $filter test ({}).".format( err ) )
            else:
                results.update_test_results( "Filter Check", 0, "Service does not support $filter.", skipped = True )

            if service_root.dict["ProtocolFeaturesSupported"].get( "SelectQuery", False ):
                try:
                    select_test( redfish_obj, service_root, results )
                except Exception as err:
                    results.update_test_results( "Select Check", 1, "Failed to perform $select test ({}).".format( err ) )
            else:
                results.update_test_results( "Select Check", 0, "Service does not support $select.", skipped = True )

            if "ExpandQuery" in service_root.dict["ProtocolFeaturesSupported"]:
                try:
                    expand_test( redfish_obj, service_root, results )
                except Exception as err:
                    results.update_test_results( "Expand Check", 1, "Failed to perform $expand test ({}).".format( err ) )
            else:
                results.update_test_results( "Expand Check", 0, "Service does not support $expand.", skipped = True )

            if service_root.dict["ProtocolFeaturesSupported"].get( "OnlyMemberQuery", False ):
                try:
                    only_test( redfish_obj, service_root, results )
                except Exception as err:
                    results.update_test_results( "Only Check", 1, "Failed to perform $select test ({}).".format( err ) )
            else:
                results.update_test_results( "Only Check", 0, "Service does not support $select.", skipped = True )
        else:
            print( "Service does not report supported protocol features" )
            results.update_test_results( "Filter Check", 0, "Service does not report supported protocol features.", skipped = True )
            results.update_test_results( "Select Check", 0, "Service does not report supported protocol features.", skipped = True )
            results.update_test_results( "Expand Check", 0, "Service does not report supported protocol features.", skipped = True )
            results.update_test_results( "Only Check", 0, "Service does not report supported protocol features.", skipped = True )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
