# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md
#
# Unit tests for power_control.py
#

from unittest import TestCase
from unittest import mock

import power_control


class PowerControlTest(TestCase):

    @mock.patch('requests.models.Response', autospec=True)
    @mock.patch('power_control.redfishtoolTransport.RfTransport', autospec=True)
    @mock.patch('power_control.Systems.RfSystemsMain', autospec=True)
    @mock.patch('power_control.raw.RfRawMain', autospec=True)
    @mock.patch('power_control.SchemaValidation', autospec=True)
    def setUp(self, mock_validator, mock_raw_main, mock_systems, mock_transport, mock_response):
        self.validator = mock_validator
        self.raw = mock_raw_main
        self.sys = mock_systems
        self.rft = mock_transport
        mock_transport.IdOptnCount = 1
        valid_reset_types = ["On", "ForceOff", "GracefulShutdown", "ForceRestart",
                             "Nmi", "GracefulRestart", "ForceOn", "PushPowerButton"]

        def run_validator_side_effect(json, schema):
            return 0, None

        def run_raw_operation_side_effect(rft):
            mock_response.status_code = 200
            return 0, mock_response, False, None

        def run_operation_side_effect(rft):
            if len(rft.subcommandArgv) > 2 and rft.subcommandArgv[2] in valid_reset_types:
                mock_response.status_code = 204
                return 0, mock_response, False, None
            else:
                return 8, None, False, None

        self.validator.validate_json.side_effect = run_validator_side_effect
        self.raw.runOperation.side_effect = run_raw_operation_side_effect
        self.sys.runOperation.side_effect = run_operation_side_effect

    def run_good_reset(self, reset_type):
        args = ["Systems", "reset", reset_type]
        power_control.setup_systems_operation(args, self.rft, self.sys)
        rc, r, j, d = power_control.run_systems_operation(self.rft, self.sys)
        self.assertEqual(self.sys.runOperation.call_count, 1, "sys.runOperation call_count should be 1 for reset_type="
                         + reset_type)
        self.assertEqual(rc, 0, "return code (rc) should be 0 for reset_type=" + reset_type)
        self.assertEqual(r.status_code, 204, "response status_code should be 204 for reset_type=" + reset_type)
        self.assertEqual(j, False, "json_data should be False for reset_type=" + reset_type)
        self.assertEqual(d, None, "data_type should be None for reset_type=" + reset_type)

    def run_bad_reset(self, reset_type):
        args = ["Systems", "reset", reset_type]
        power_control.setup_systems_operation(args, self.rft, self.sys)
        rc, r, j, d = power_control.run_systems_operation(self.rft, self.sys)
        self.assertEqual(self.sys.runOperation.call_count, 1, "sys.runOperation call_count should be 1 for reset_type="
                         + reset_type)
        self.assertEqual(rc, 8, "return code (rc) should be 8 for reset_type=" + reset_type)

    """
    Tests for functions setup_operation() and run_systems_operation()
    Valid reset types are: "On", "ForceOff", "GracefulShutdown", "ForceRestart", "Nmi",
                           "GracefulRestart", "ForceOn", "PushPowerButton"]
    """
    def test_run_reset_on(self):
        self.run_good_reset("On")

    def test_run_reset_force_off(self):
        self.run_good_reset("ForceOff")

    def test_run_reset_graceful_shutdown(self):
        self.run_good_reset("GracefulShutdown")

    def test_run_reset_force_restart(self):
        self.run_good_reset("ForceRestart")

    def test_run_reset_nmi(self):
        self.run_good_reset("Nmi")

    def test_run_reset_graceful_restart(self):
        self.run_good_reset("GracefulRestart")

    def test_run_reset_force_on(self):
        self.run_good_reset("ForceOn")

    def test_run_reset_push_power_button(self):
        self.run_good_reset("PushPowerButton")

    def test_run_reset_off(self):
        self.run_bad_reset("Off")

    """
    Tests for function validate_power_state()
    """
    def test_validate_state_ppb_on_to_off(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "On", "Off")
        self.assertEqual(rc, 0, "return code (rc) should be 0 for PushPowerButton states On to Off")

    def test_validate_state_ppb_off_to_on(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "Off", "On")
        self.assertEqual(rc, 0, "return code (rc) should be 0 for PushPowerButton states Off to On")

    def test_validate_state_should_be_on_good(self):
        # power state should be on after issuing these commands
        for reset_type in ["On", "ForceRestart", "Nmi", "GracefulRestart", "ForceOn"]:
            rc = power_control.validate_power_state(self.rft, reset_type, "Off", "On")
            self.assertEqual(rc, 0, "return code (rc) should be 0 for " + reset_type + " states Off to On")

    def test_validate_state_should_be_off_good(self):
        # power state should be off after issuing these commands
        for reset_type in ["ForceOff", "GracefulShutdown"]:
            rc = power_control.validate_power_state(self.rft, reset_type, "On", "Off")
            self.assertEqual(rc, 0, "return code (rc) should be 0 for " + reset_type + " states On to Off")

    def test_validate_state_ppb_on_to_on(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "On", "On")
        self.assertEqual(rc, 1, "return code (rc) should be 1 for PushPowerButton states On to On")

    def test_validate_state_ppb_off_to_off(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "Off", "Off")
        self.assertEqual(rc, 1, "return code (rc) should be 1 for PushPowerButton states Off to Off")

    def test_validate_state_ppb_on_to_invalid(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "On", "Invalid")
        self.assertEqual(rc, 1, "return code (rc) should be 1 for PushPowerButton states On to Invalid")

    def test_validate_state_ppb_invalid_to_off(self):
        rc = power_control.validate_power_state(self.rft, "PushPowerButton", "Invalid", "Off")
        self.assertEqual(rc, 1, "return code (rc) should be 1 for PushPowerButton states Invalid to Off")

    def test_validate_state_should_be_on_bad(self):
        # power state should be on after issuing these commands
        for reset_type in ["On", "ForceRestart", "Nmi", "GracefulRestart", "ForceOn"]:
            rc = power_control.validate_power_state(self.rft, reset_type, "On", "Off")
            self.assertEqual(rc, 1, "return code (rc) should be 1 for " + reset_type + " states On to Off")

    def test_validate_state_should_be_off_bad(self):
        # power state should be off after issuing these commands
        for reset_type in ["ForceOff", "GracefulShutdown"]:
            rc = power_control.validate_power_state(self.rft, reset_type, "Off", "On")
            self.assertEqual(rc, 1, "return code (rc) should be 1 for " + reset_type + " states Off to On")

    """
    Tests for function get_power_state()
    """
    def test_get_power_state_empty1(self):
        state = power_control.get_power_state(False, None)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_empty2(self):
        state = power_control.get_power_state(True, None)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_empty3(self):
        state = power_control.get_power_state(True, {})
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_empty4(self):
        state = power_control.get_power_state(False, {})
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_json_data_false(self):
        data = {"SomeKey": "SomeValue", "PowerState": "On"}
        state = power_control.get_power_state(False, data)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for json_data False")

    def test_get_power_state_on(self):
        data = {"SomeKey": "SomeValue", "PowerState": "On"}
        state = power_control.get_power_state(True, data)
        self.assertEqual(state, "On", "returned state should be 'On'")

    def test_get_power_state_off(self):
        data = {"SomeKey": "SomeValue", "PowerState": "Off"}
        state = power_control.get_power_state(True, data)
        self.assertEqual(state, "Off", "returned state should be 'Off'")

    def test_get_power_state_other(self):
        data = {"SomeKey": "SomeValue", "PowerState": "SomeOtherState"}
        state = power_control.get_power_state(True, data)
        self.assertEqual(state, "SomeOtherState", "returned state should be 'SomeOtherState'")

    def test_get_power_state_on_nested(self):
        data = {"TopLevelKey": {"SomeKey": "SomeValue", "PowerState": "On"}}
        state = power_control.get_power_state(True, data)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for nested PowerState")

    """
    Tests for function validate_reset_command()
    """
    def test_validate_reset_command(self):
        reset_type = "GracefulShutdown"
        power_control.validate_reset_command(self.rft, self.sys, self.validator, reset_type)
        self.assertEqual(self.sys.runOperation.call_count, 1,
                         "sys.runOperation call_count should be 1 for reset_type=" + reset_type)
