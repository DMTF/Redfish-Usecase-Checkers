# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md

import jsonschema


class SchemaValidation(object):

    def __init__(self, rft, service_root, raw_main, results):
        self.rft = rft
        self.service_root = service_root
        self.raw_main = raw_main
        self.results = results
        self.schema_dict = None
        # get /redfish/v1/JSONSchemas collection and store it as a dict
        if service_root is not None and "JsonSchemas" in service_root:
            json_schema_uri = service_root["JsonSchemas"]["@odata.id"]
            self.rft.printVerbose(1, "SchemaValidation:__init__: json_schema_uri = {}".format(json_schema_uri))
            schemas = self.call_raw_operation(json_schema_uri)
            if schemas is not None and "Members" in schemas:
                self.schema_dict = {elt["@odata.id"].rsplit("/", 1)[1]: elt["@odata.id"] for elt in schemas["Members"]}
                self.rft.printVerbose(1, "SchemaValidation:__init__: schema_dict = {}".format(self.schema_dict))
            else:
                self.rft.printErr("SchemaValidation:__init__: unable to read schema Members")
        else:
            self.rft.printErr("SchemaValidation:__init__: unable to get JsonSchemas from service root")

    def call_raw_operation(self, uri):
        """
        Use the redfishtool raw interface to perform a GET on the proved uri
        """
        saved_sub_command = self.rft.subcommand
        saved_sub_command_argv = self.rft.subcommandArgv
        args = ["raw", "GET", uri]
        self.rft.subcommand = args[0]
        self.rft.subcommandArgv = args
        self.raw_main.operation = args[1]
        self.raw_main.args = args[1:]
        self.raw_main.argnum = len(self.raw_main.args)
        data = None
        try:
            rc, r, j, d = self.raw_main.runOperation(self.rft)
            if j is True and d is not None:
                data = d
        finally:
            self.rft.subcommand = saved_sub_command
            self.rft.subcommandArgv = saved_sub_command_argv
            self.rft.printVerbose(1, "SchemaValidation:call_raw_operation: returning data = {}".format(data))
        return data

    def split_odata_type(self, json_data):
        """
        Get the @odata.type entry from the JSON payload, split into namespace and type and return as a tuple
        """
        ns = type_name = None
        if json_data is not None and "@odata.type" in json_data:
            odata_type = json_data["@odata.type"]
            ns, type_name = odata_type.rsplit('.', 1)
            ns = ns.strip('#')
            self.rft.printVerbose(2, "SchemaValidation:split_odata_type: odata = {}, namespace = {}, typename = {}"
                                  .format(odata_type, ns, type_name))
        else:
            self.rft.printVerbose(2, "SchemaValidation:split_odata_type: JSON payload empty or no @odata.type found")
        return ns, type_name

    def get_json_schema(self, json_data):
        """
        Fetch the JSON schema from the Redfish service. The schema to fetch is based on
        the @odata.type entry in the JSON payload
        """
        schema = None
        if self.schema_dict is None:
            return None
        ns, type_name = self.split_odata_type(json_data)
        if ns is None:
            self.rft.printErr("SchemaValidation:get_json_schema: No '@odata.type' found in JSON payload")
            return None
        data = uri = None
        if ns is not None and ns in self.schema_dict:
            uri = self.schema_dict[ns]
        elif type_name is not None and type_name in self.schema_dict:
            uri = self.schema_dict[type_name]
        if uri is not None:
            data = self.call_raw_operation(uri)
        if data is not None and "Location" in data:
            location = data["Location"]
            if len(location) > 0 and "Uri" in location[0]:
                uri = location[0]["Uri"]
                schema = self.call_raw_operation(uri)
            else:
                self.rft.printErr("SchemaValidation:get_json_schema: 'Uri' not found in Location[0]")
        else:
            self.rft.printErr("SchemaValidation:get_json_schema: 'Location' not found from uri {}".format(uri))
        return schema

    def validate_json(self, json_data, schema):
        """
        Validate the JSON response against the schema
        """
        if json_data is None:
            # JSON payload not required
            self.rft.printVerbose(1, "SchemaValidation:validate_json: No JSON payload to validate")
            return 0, None
        if schema is None:
            # Redfish schema not required
            self.rft.printVerbose(1, "SchemaValidation:validate_json: No JSON schema retrieved for validation")
            return 0, None
        # validate the json response against the schema
        try:
            self.rft.printVerbose(5, "SchemaValidation:validate_json: JSON to be validated: {}".format(json_data))
            self.rft.printVerbose(5, "SchemaValidation:validate_json: JSON schema for validation: {}".format(schema))
            jsonschema.validate(json_data, schema)
        except jsonschema.ValidationError as e:
            self.rft.printErr("SchemaValidation:validate_json: JSON schema validation error: {}".format(e.message))
            return 4, e.message
        except jsonschema.SchemaError as e:
            self.rft.printErr("SchemaValidation:validate_json: JSON schema error: {}".format(e.message))
            return 8, e.message
        else:
            self.rft.printVerbose(1, "SchemaValidation:validate_json: JSON schema validation successful")
            return 0, None
