# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md

import datetime
import json
import os
import sys


class Results(object):

    def __init__(self, tool_name, service_root):
        self.output_dir = os.getcwd()
        self.results_filename = "results.json"
        self.tool_name = tool_name
        self.return_code = 0
        self.results = {"ToolName": tool_name}
        self.results.update({"Timestamp": {"DateTime":
                            "{:%Y-%m-%dT%H:%M:%SZ}".format(datetime.datetime.now(datetime.timezone.utc))}})
        if service_root is not None:
            self.results.update({"ServiceRoot": service_root})
        else:
            self.results.update({"ServiceRoot": {}})

    def update_test_results(self, test_name, rc, msg):
        if "TestResults" not in self.results:
            self.results.update({"TestResults": {}})
        if test_name not in self.results["TestResults"]:
            self.results["TestResults"].update({test_name: {"pass": 0, "fail": 0}})
        if rc == 0:
            self.results["TestResults"][test_name]["pass"] += 1
        else:
            self.results["TestResults"][test_name]["fail"] += 1
            if "ErrorMessages" not in self.results["TestResults"]:
                self.results["TestResults"].update({"ErrorMessages": []})
            if msg is not None:
                self.results["TestResults"]["ErrorMessages"].append(msg)
            self.return_code = rc

    def add_cmd_line_args(self, opts, args):
        self.results.update({"CommandLineArgs": {"opts": opts, "args": args}})

    def set_output_dir(self, output_dir):
        self.output_dir = os.path.abspath(output_dir)
        try:
            if not os.path.isdir(self.output_dir):
                os.mkdir(self.output_dir)
        except OSError as e:
            print("Error creating output directory {}, error: {}".format(self.output_dir, e), file=sys.stderr)
            print("Will write results file to current working directory instead.", file=sys.stderr)
            self.output_dir = os.getcwd()

    def write_results(self):
        path = os.path.join(self.output_dir, self.results_filename)
        try:
            with open(path, 'w') as outfile:
                json.dump(self.results, outfile)
        except OSError as e:
            print("Error writing results file to {}, error: {}".format(path, e), file=sys.stderr)
            print("Printing results to STDOUT instead.", file=sys.stderr)
            print(json.dumps(self.results))

    def json_string(self):
        return json.dumps(self.results)

    def get_return_code(self):
        return self.return_code
