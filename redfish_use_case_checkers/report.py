# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

import html as html_mod
import json
from datetime import datetime

from redfish_use_case_checkers import redfish_logo
from redfish_use_case_checkers.system_under_test import SystemUnderTest

html_template = """
<html>
  <head>
    <title>Redfish Use Case Checkers Test Summary</title>
    <style>
      .pass {{background-color:#99EE99}}
      .fail {{background-color:#EE9999}}
      .warn {{background-color:#EEEE99}}
      .bluebg {{background-color:#BDD6EE}}
      .button {{padding: 12px; display: inline-block}}
      .center {{text-align:center;}}
      .left {{text-align:left;}}
      .log {{text-align:left; white-space:pre-wrap; word-wrap:break-word;
             font-size:smaller}}
      .title {{background-color:#DDDDDD; border: 1pt solid; font-height: 30px;
               padding: 8px}}
      .titlesub {{padding: 8px}}
      .titlerow {{border: 2pt solid}}
      .headingrow {{border: 2pt solid; text-align:left;
                    background-color:beige;}}
      .results {{transition: visibility 0s, opacity 0.5s linear; display: none;
                 opacity: 0}}
      .resultsShow {{display: block; opacity: 1}}
      body {{background-color:lightgrey; border: 1pt solid; text-align:center;
             margin-left:auto; margin-right:auto}}
      th {{text-align:center; background-color:beige; border: 1pt solid}}
      td {{text-align:left; background-color:white; border: 1pt solid;
           word-wrap:break-word;}}
      table {{width:90%; margin: 0px auto; table-layout:fixed;}}
      .titletable {{width:100%}}
    </style>
  </head>
  <table>
    <tr>
      <th>
        <h2>##### Redfish Use Case Checkers Test Report #####</h2>
        <h4><img align=\"center\" alt=\"DMTF Redfish Logo\" height=\"203\"
            width=\"288\" src=\"data:image/gif;base64,{}\"></h4>
        <h4><a href=\"https://github.com/DMTF/Redfish-Use-Case-Checkers\">
            https://github.com/DMTF/Redfish-Use-Case-Checkers</a></h4>
        Tool Version: {}<br/>
        {}<br/><br/>
        This tool is provided and maintained by the DMTF. For feedback, please
        open issues<br/> in the tool's Github repository:
        <a href=\"https://github.com/DMTF/Redfish-Use-Case-Checkers/issues\">
            https://github.com/DMTF/Redfish-Use-Case-Checkers/issues</a><br/>
      </th>
    </tr>
    <tr>
      <th>
        System: {}/redfish/v1/, User: {}, Password: {}<br/>
        Product: {}<br/>
        Manufacturer: {}, Model: {}, Firmware version: {}<br/>
      </th>
    </tr>
    <tr>
      <td>
        <center><b>Results Summary</b></center>
        <center>Pass: {}, Warning: {}, Fail: {}, Not tested: {}</center>
      </td>
    </tr>
    {}
  </table>
</html>
"""

section_header_html = """
  <table>
    <tr>
      <th class=\"titlerow bluebg\">
        <b>{}</b>
      </th>
    </tr>
  </table>
"""


def html_report(sut: SystemUnderTest, report_dir, time, tool_version):
    """
    Creates the HTML report for the system under test

    Args:
        sut: The system under test
        report_dir: The directory for the report
        time: The time the tests finished
        tool_version: The version of the tool

    Returns:
        The path to the HTML report
    """

    file = report_dir / datetime.strftime(time, "RedfishUseCaseCheckersReport_%m_%d_%Y_%H%M%S.html")
    html = ""
    for test_category in sut._results:
        html += section_header_html.format(test_category["Category"])
        for test in test_category["Tests"]:
            html += "<table>"
            html += '<th colspan="3" class="headingrow">{}: {}<br/>{}</th>'.format(
                test["Name"], test["Description"], test["Details"]
            )
            html += "<tr><td><b>{}</b></td><td><b>{}</b></td><td><b>{}</b></td></tr>".format(
                "Operation", "Result", "Message"
            )
            for result in test["Results"]:
                result_class = ""
                if result["Result"] == "PASS":
                    result_class = 'class="pass"'
                elif result["Result"] == "WARN":
                    result_class = 'class="warn"'
                elif result["Result"] == "FAIL":
                    result_class = 'class="fail"'
                operation = result["Operation"]
                if operation == "":
                    operation = "No testing performed"
                html += "<tr><td>{}</td><td {}>{}</td><td>{}</td></tr>".format(
                    operation, result_class, result["Result"], html_mod.escape(result["Message"])
                )
            html += "</table>"
    with open(str(file), "w", encoding="utf-8") as fd:
        fd.write(
            html_template.format(
                redfish_logo.logo,
                tool_version,
                time.strftime("%c"),
                sut.rhost,
                sut.username,
                "********",
                sut.product,
                sut.manufacturer,
                sut.model,
                sut.firmware_version,
                sut.pass_count,
                sut.warn_count,
                sut.fail_count,
                sut.skip_count,
                html,
            )
        )
    return file
