# Copyright Notice:
# Copyright 2017-2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Account Management Usecase Test

File : account_management.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for account management
"""

import argparse
import datetime
import sys

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

def verify_user( context, user_name, role = None, enabled = None ):
    """
    Checks that a given user is in the user list with a certain role

    Args:
        context: The Redfish client object with an open session
        user_name: The name of the user to check
        role: The role for the user
        enabled: The enabled state for the user

    Returns:
        True if a match is found, false otherwise
    """
    user_list = redfish_utilities.get_users( context )
    for user in user_list:
        if user["UserName"] == user_name:
            if role is not None and user["RoleId"] != role:
                return False
            if enabled is not None and user["Enabled"] != enabled:
                return False
            return True

    return False

if __name__ == "__main__":

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "Usecase checker for account management" )
    argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
    argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
    argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service" )
    argget.add_argument( "--Secure", "-S", type = str, default = "Always", help = "When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)" )
    argget.add_argument( "--directory", "-d", type = str, default = None, help = "Output directory for results.json" )
    argget.add_argument( "--debug", action = "store_true", help = "Creates debug file showing HTTP traces and exceptions" )
    args = argget.parse_args()

    if args.debug:
        log_file = "account_management-{}.log".format( datetime.datetime.now().strftime( "%Y-%m-%d-%H%M%S" ) )
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logger = redfish.redfish_logger( log_file, log_format, logging.DEBUG )
        logger.info( "account_management Trace" )

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/" )
        results = Results( "Account Management", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        # Get the list of current users
        try:
            usernames = []
            user_list = redfish_utilities.get_users( redfish_obj )
            for user in user_list:
                usernames.append( user["UserName"] )
            user_count = len( user_list )
            if user_count == 0:
                results.update_test_results( "User Count", 1, "No users were found." )
            else:
                results.update_test_results( "User Count", 0, None )
        except Exception as err:
            results.update_test_results( "User Count", 1, "Failed to get user list ({}).".format( err ) )

        # Determine a user name for testing
        for x in range( 1000 ):
            test_username = "testuser" + str( x )
            if test_username not in usernames:
                break

        # Create a new user
        user_added = False
        last_error = ""
        test_passwords = [ "hUPgd9Z4", "7jIl3dn!kd0Fql", "m5Ljed3!n0olvdS*m0kmWER15!" ]
        print( "Creating new user '{}'".format( test_username ) )
        for x in range( 3 ):
            # Try different passwords in case there are password requirements that we cannot detect
            try:
                test_password = test_passwords[x]
                redfish_utilities.add_user( redfish_obj, test_username, test_password, "Administrator" )
                user_added = True
                break
            except Exception as err:
                last_error = err
        if user_added:
            results.update_test_results( "Add User", 0, None )
        else:
            results.update_test_results( "Add User", 1, "Failed to add user '{}' ({}).".format( test_username, last_error ) )

        # Only run the remaining tests if the user was added successfully
        if user_added:
            # Get the list of current users to verify the new user was added
            if verify_user( redfish_obj, test_username, role = "Administrator" ):
                results.update_test_results( "Add User", 0, None )
            else:
                results.update_test_results( "Add User", 1, "Failed to find user '{}' with the role 'Administrator'.".format( test_username ) )

            # Check if the user needs to be enabled
            try:
                if verify_user( redfish_obj, test_username, enabled = False ):
                    redfish_utilities.modify_user( redfish_obj, test_username, new_enabled = True )
                    if verify_user( redfish_obj, test_username, enabled = True ):
                        results.update_test_results( "Enable User", 0, None )
                    else:
                        results.update_test_results( "Enable User", 1, "User '{}' not enabled after successful PATCH.".format( test_username ) )
                else:
                    results.update_test_results( "Enable User", 0, "User '{}' already enabled by the service.".format( test_username ), skipped = True )
            except Exception as err:
                results.update_test_results( "Enable User", 1, "Failed to enable user '{}' ({}).".format( test_username, err ) )

            # Log in with the new user
            print( "Logging in as '{}'".format( test_username ) )
            test_obj = redfish.redfish_client( base_url = base_url, username = test_username, password = test_password )
            try:
                test_obj.login( auth = "session" )
                test_list = redfish_utilities.get_users( test_obj )
                results.update_test_results( "Credential Check", 0, None )
            except:
                results.update_test_results( "Credential Check", 1, "Failed to login with user '{}'.".format( test_username ) )
            finally:
                test_obj.logout()

            # Log in with the new user, but with bad credentials
            print( "Logging in as '{}', but with the wrong password".format( test_username ) )
            test_obj = redfish.redfish_client( base_url = base_url, username = test_username, password = test_password + "ExtraStuff" )
            try:
                test_obj.login( auth = "session" )
                test_list = redfish_utilities.get_users( test_obj )
                results.update_test_results( "Credential Check", 1, "Login with user '{}' when using invalid credentials.".format( test_username ) )
            except:
                results.update_test_results( "Credential Check", 0, None )
            finally:
                test_obj.logout()

            # Change the role of the user
            test_roles = [ "ReadOnly", "Operator", "Administrator" ]
            for role in test_roles:
                try:
                    print( "Setting user '{}' to role '{}'".format( test_username, role ) )
                    redfish_utilities.modify_user( redfish_obj, test_username, new_role = role )
                    results.update_test_results( "Change Role", 0, None )
                    if verify_user( redfish_obj, test_username, role = role ):
                        results.update_test_results( "Change Role", 0, None )
                    else:
                        results.update_test_results( "Change Role", 1, "Failed to find user '{}' with the role '{}'.".format( test_username, role ) )
                except Exception as err:
                    results.update_test_results( "Change Role", 1, "Failed to set user '{}' to '{}' ({}).".format( test_username, role, err ) )

            # Delete the user
            try:
                print( "Deleting user '{}'".format( test_username ) )
                redfish_utilities.delete_user( redfish_obj, test_username )
                results.update_test_results( "Delete User", 0, None )
                if verify_user( redfish_obj, test_username ):
                    results.update_test_results( "Delete User", 1, "User '{}' is still in the user list.".format( test_username ) )
                else:
                    results.update_test_results( "Delete User", 0, None )
            except Exception as err:
                results.update_test_results( "Delete User", 1, "Failed to delete user '{}' ({}).".format( test_username, err ) )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
