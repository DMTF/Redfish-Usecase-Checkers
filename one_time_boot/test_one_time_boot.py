
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md
#
# Unit tests for one_time_boot.py
#

from unittest import TestCase
from unittest import mock

import one_time_boot as otb

class OneTimeBootTest(TestCase):

    """
    Tests for functions setup_operation() and run_systems_operation()
    """
    def test_check_boot(self):
        oldOParams = ['Disabled','Disabled','Once','Once','Continuous','Continuous']
        newOParams = ['Disabled','Disabled','Once','Once','Continuous','Continuous']
        oldTParams = ['None', 'Pxe','SdCard', 'Pxe', 'SdCard', 'Pxe']
        newTParams = ['None', 'Pxe','None', 'None', 'SdCard', 'Pxe']

        for args in zip(oldOParams, oldTParams, newOParams, newTParams):
            self.assertTrue(otb.checkBootPass(*args),'check boot not correct  ' + str(args))
        
