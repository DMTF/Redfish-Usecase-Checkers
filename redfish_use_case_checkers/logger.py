# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Redfish Use Case Checkers Logger

File : logger.py

Brief : This file contains the definitions and functionalities for handling
        the debug log.
"""

import logging

logger = None
delimiter = "=================================================="


def log_use_case_category_header(category_name):
    """
    Logs the use case category header

    Args:
        category_name: The name of the category
    """
    logger.info(delimiter)
    logger.info(delimiter)
    logger.info("{} Use Cases (Start)".format(category_name))
    logger.info(delimiter)
    logger.info(delimiter)
    print("Performing {} use cases...".format(category_name))


def log_use_case_category_footer(category_name):
    """
    Logs the use case category footer

    Args:
        category_name: The name of the category
    """
    logger.info(delimiter)
    logger.info(delimiter)
    logger.info("{} Use Cases (End)".format(category_name))
    logger.info(delimiter)
    logger.info(delimiter)
    print()


def log_use_case_test_header(category_name, test_name):
    """
    Logs the use case test header

    Args:
        category_name: The name of the category
        test_name: The name of the test
    """
    logger.info(delimiter)
    logger.info("{}: {} Test (Start)".format(category_name, test_name))
    logger.info(delimiter)
    print("-- Running the {} test...".format(test_name))


def log_use_case_test_footer(category_name, test_name):
    """
    Logs the use case test footer

    Args:
        category_name: The name of the category
        test_name: The name of the test
    """
    logger.info(delimiter)
    logger.info("{}: {} Test (End)".format(category_name, test_name))
    logger.info(delimiter)
