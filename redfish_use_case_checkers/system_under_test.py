# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

import redfish
import redfish_utilities

from redfish_use_case_checkers import logger


class SystemUnderTest(object):
    def __init__(self, rhost, username, password, relaxed):
        """
        Constructor for new system under test

        Args:
            rhost: The address of the Redfish service (with scheme)
            username: The username for authentication
            password: The password for authentication
            relaxed: Whether or not to apply relaxed testing criteria
        """
        self._rhost = rhost
        self._username = username
        self._relaxed = relaxed
        self._redfish_obj = redfish.redfish_client(
            base_url=rhost, username=username, password=password, timeout=15, max_retry=3
        )
        self._redfish_obj.login(auth="session")
        self._service_root = self._redfish_obj.root_resp.dict
        self._results = []
        self._pass_count = 0
        self._warn_count = 0
        self._fail_count = 0
        self._skip_count = 0

        # Find the manager to populate service info
        self._product = None
        self._product = self._service_root.get("Product", "N/A")
        self._fw_version = None
        self._model = None
        self._manufacturer = None
        if "Managers" in self._service_root:
            try:
                manager_ids = redfish_utilities.get_manager_ids(self._redfish_obj)
                if len(manager_ids) > 0:
                    manager = redfish_utilities.get_manager(self._redfish_obj, manager_ids[0])
                    self._fw_version = manager.dict.get("FirmwareVersion", "N/A")
                    self._model = manager.dict.get("Model", "N/A")
                    self._manufacturer = manager.dict.get("Manufacturer", "N/A")
            except:
                pass

    @property
    def rhost(self):
        """
        Accesses the address of the Redfish service

        Returns:
            The address of the Redfish service
        """
        return self._rhost

    @property
    def username(self):
        """
        Accesses the username for authentication

        Returns:
            The username for authentication
        """
        return self._username

    @property
    def firmware_version(self):
        """
        Accesses the firmware version of the service

        Returns:
            The firmware version of the service
        """
        return self._fw_version

    @property
    def model(self):
        """
        Accesses the model of the service

        Returns:
            The model of the service
        """
        return self._model

    @property
    def product(self):
        """
        Accesses the product of the service

        Returns:
            The product of the service
        """
        return self._product

    @property
    def manufacturer(self):
        """
        Accesses the manufacturer of the service

        Returns:
            The manufacturer of the service
        """
        return self._manufacturer

    @property
    def session(self):
        """
        Accesses the Redfish session

        Returns:
            The Redfish client object
        """
        return self._redfish_obj

    @property
    def service_root(self):
        """
        Accesses the service root data

        Returns:
            The service root data as a dictionary
        """
        return self._service_root

    @property
    def pass_count(self):
        """
        Accesses the pass count

        Returns:
            The pass count
        """
        return self._pass_count

    @property
    def warn_count(self):
        """
        Accesses the warning count

        Returns:
            The warning count
        """
        return self._warn_count

    @property
    def fail_count(self):
        """
        Accesses the fail count

        Returns:
            The fail count
        """
        return self._fail_count

    @property
    def skip_count(self):
        """
        Accesses the skip count

        Returns:
            The skip count
        """
        return self._skip_count

    def logout(self):
        """
        Logs out of the Redfish service
        """
        self._redfish_obj.logout()

    def add_results_category(self, category, tests):
        """
        Adds a new category to the results

        Args:
            category: The name of the category
            tests: An array of test names and descriptions within the category
        """
        new_category = {"Category": category, "Tests": []}
        for test in tests:
            new_category["Tests"].append({"Name": test[0], "Description": test[1], "Details": test[2], "Results": []})
        self._results.append(new_category)

    def add_test_result(self, category_name, test_name, operation, result, msg=""):
        """
        Adds a new test result to the results

        Args:
            category_name: The name of the category
            test_name: The name of the test
            operation: The operation performed for the test
            result: The result of the test
            msg: A message for the test
        """
        for category in self._results:
            if category["Category"] == category_name:
                for test in category["Tests"]:
                    if test["Name"] == test_name:
                        test["Results"].append({"Operation": operation, "Result": result, "Message": msg})
                        if result == "PASS":
                            self._pass_count += 1
                        elif result == "WARN" or (result == "FAILWARN" and self._relaxed is True):
                            logger.logger.warn("Warning occurred during the {} test...".format(test_name))
                            test["Results"][-1]["Result"] = "WARN"
                            logger.logger.warn(msg)
                            self._warn_count += 1
                        elif result == "FAIL" or result == "FAILWARN":
                            logger.logger.error("Failing the {} test...".format(test_name))
                            test["Results"][-1]["Result"] = "FAIL"
                            logger.logger.error(msg)
                            self._fail_count += 1
                        elif result == "SKIP":
                            logger.logger.info("Skipping the {} test...".format(test_name))
                            logger.logger.info(msg)
                            self._skip_count += 1
