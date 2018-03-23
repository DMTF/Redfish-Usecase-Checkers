# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md
#
# Unit tests for account_management.py
#

from unittest import TestCase
from unittest import mock

import account_management


class AccountServiceTest(TestCase):

    @mock.patch('requests.models.Response', autospec=True)
    @mock.patch('account_management.redfishtoolTransport.RfTransport', autospec=True)
    @mock.patch('account_management.AccountService.RfAccountServiceMain', autospec=True)
    @mock.patch('account_management.SchemaValidation', autospec=True)
    def setUp(self, mock_validator, mock_account_service, mock_transport, mock_response):
        self.validator = mock_validator
        self.account = mock_account_service
        self.rft = mock_transport
        mock_transport.IdOptnCount = 1

        def run_validator_side_effect(json, schema):
            return 0, None

        def run_good_operation_side_effect(rft):
            mock_response.status_code = 200
            data = {"Members": [{"Id": 1, "UserName": "Administrator"}]}
            return 0, mock_response, True, data

        def run_bad_operation_side_effect(rft):
            mock_response.status_code = 405
            return 5, mock_response, False, None

        self.validator.validate_json.side_effect = run_validator_side_effect
        self.good_side_effect = run_good_operation_side_effect
        self.bad_side_effect = run_bad_operation_side_effect
        self.account.runOperation.side_effect = self.good_side_effect

    def run_good_setup_and_operation(self, args):
        self.account.runOperation.side_effect = self.good_side_effect
        account_management.setup_account_operation(args, self.rft, self.account)
        rc, r, j, d = account_management.run_account_operation(self.rft, self.account)
        self.assertEqual(self.account.runOperation.call_count, 1,
                         "account.runOperation call_count should be 1")
        self.assertEqual(rc, 0, "return code (rc) should be 0")
        self.assertEqual(r.status_code, 200, "response status_code should be 200")
        self.assertEqual(j, True, "json_data should be True")
        self.assertTrue("Members" in d, "data_type should contain 'Members' element")

    def run_bad_setup_and_operation(self, args):
        self.account.runOperation.side_effect = self.bad_side_effect
        account_management.setup_account_operation(args, self.rft, self.account)
        rc, r, j, d = account_management.run_account_operation(self.rft, self.account)
        self.assertEqual(self.account.runOperation.call_count, 1,
                         "account.runOperation call_count should be 1")
        self.assertEqual(rc, 5, "return code (rc) should be 5")
        self.assertEqual(r.status_code, 405, "response status_code should be 405")
        self.assertEqual(j, False, "json_data should be False")
        self.assertEqual(d, None, "data_type should be None")

    """
    Tests for functions setup_operation() and run_systems_operation()
    """
    def test_run_good_adduser(self):
        self.run_good_setup_and_operation(["AccountService", "adduser", "alice", "ksbt6529", "Admin"])

    def test_run_bad_adduser(self):
        self.run_bad_setup_and_operation(["AccountService", "adduser", "alice", "ksbt6529", "Admin"])

    def test_run_good_deleteuser(self):
        self.run_good_setup_and_operation(["AccountService", "deleteuser", "alice"])

    def test_run_bad_deleteuser(self):
        self.run_bad_setup_and_operation(["AccountService", "deleteuser", "alice"])

    def test_run_good_useradmin(self):
        self.run_good_setup_and_operation(["AccountService", "useradmin", "alice", "disable"])

    def test_run_bad_useradmin(self):
        self.run_bad_setup_and_operation(["AccountService", "useradmin", "alice", "disable"])

    """
    Tests for function validate_reset_command()
    """
    def test_validate_account_command(self):
        args = ["AccountService", "adduser", "alice", "ksbt6529", "Admin"]
        account_management.validate_account_command(self.rft, self.account, self.validator, args)
        self.assertEqual(self.account.runOperation.call_count, 1,
                         "account.runOperation call_count should be 1")
