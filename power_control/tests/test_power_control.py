# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md
#
# Unit tests for power_control.py
#

from unittest import TestCase
from unittest import mock

import power_control


class PowerControlTest(TestCase):

    """
    Tests for function validate_power_state()
    """
    def test_validate_state_ppb_on_to_off(self):
        rc = power_control.validate_power_state("PushPowerButton", "On", "Off")
        self.assertEqual(rc, True, "return code (rc) should be True for PushPowerButton states On to Off")

    def test_validate_state_ppb_off_to_on(self):
        rc = power_control.validate_power_state("PushPowerButton", "Off", "On")
        self.assertEqual(rc, True, "return code (rc) should be True for PushPowerButton states Off to On")

    def test_validate_state_should_be_on_good(self):
        # power state should be on after issuing these commands
        for reset_type in ["On", "ForceRestart", "Nmi", "GracefulRestart", "ForceOn"]:
            rc = power_control.validate_power_state(reset_type, "Off", "On")
            self.assertEqual(rc, True, "return code (rc) should be True for " + reset_type + " states Off to On")

    def test_validate_state_should_be_off_good(self):
        # power state should be off after issuing these commands
        for reset_type in ["ForceOff", "GracefulShutdown"]:
            rc = power_control.validate_power_state(reset_type, "On", "Off")
            self.assertEqual(rc, True, "return code (rc) should be True for " + reset_type + " states On to Off")

    def test_validate_state_ppb_on_to_on(self):
        rc = power_control.validate_power_state("PushPowerButton", "On", "On")
        self.assertEqual(rc, False, "return code (rc) should be False for PushPowerButton states On to On")

    def test_validate_state_ppb_off_to_off(self):
        rc = power_control.validate_power_state("PushPowerButton", "Off", "Off")
        self.assertEqual(rc, False, "return code (rc) should be False for PushPowerButton states Off to Off")

    def test_validate_state_ppb_on_to_invalid(self):
        rc = power_control.validate_power_state("PushPowerButton", "On", "Invalid")
        self.assertEqual(rc, False, "return code (rc) should be False for PushPowerButton states On to Invalid")

    def test_validate_state_ppb_invalid_to_off(self):
        rc = power_control.validate_power_state("PushPowerButton", "Invalid", "Off")
        self.assertEqual(rc, False, "return code (rc) should be False for PushPowerButton states Invalid to Off")

    def test_validate_state_should_be_on_bad(self):
        # power state should be on after issuing these commands
        for reset_type in ["On", "ForceRestart", "Nmi", "GracefulRestart", "ForceOn"]:
            rc = power_control.validate_power_state(reset_type, "On", "Off")
            self.assertEqual(rc, False, "return code (rc) should be False for " + reset_type + " states On to Off")

    def test_validate_state_should_be_off_bad(self):
        # power state should be off after issuing these commands
        for reset_type in ["ForceOff", "GracefulShutdown"]:
            rc = power_control.validate_power_state(reset_type, "Off", "On")
            self.assertEqual(rc, False, "return code (rc) should be False for " + reset_type + " states Off to On")

    """
    Tests for function get_power_state()
    """
    def test_get_power_state_empty2(self):
        state = power_control.get_power_state(None)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_empty3(self):
        state = power_control.get_power_state({})
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for empty data")

    def test_get_power_state_on(self):
        data = {"SomeKey": "SomeValue", "PowerState": "On"}
        state = power_control.get_power_state(data)
        self.assertEqual(state, "On", "returned state should be 'On'")

    def test_get_power_state_off(self):
        data = {"SomeKey": "SomeValue", "PowerState": "Off"}
        state = power_control.get_power_state(data)
        self.assertEqual(state, "Off", "returned state should be 'Off'")

    def test_get_power_state_other(self):
        data = {"SomeKey": "SomeValue", "PowerState": "SomeOtherState"}
        state = power_control.get_power_state(data)
        self.assertEqual(state, "SomeOtherState", "returned state should be 'SomeOtherState'")

    def test_get_power_state_on_nested(self):
        data = {"TopLevelKey": {"SomeKey": "SomeValue", "PowerState": "On"}}
        state = power_control.get_power_state(data)
        self.assertEqual(state, "<n/a>", "returned state should be <n/a> for nested PowerState")

