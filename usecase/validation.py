# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/master/LICENSE.md

import jsonschema
import logging
import requests


class SchemaValidation(object):

    def __init__(self, rhost, service_root, results, auth=None, verify=True, nossl=False):
        self.service_root = service_root
        self.results = results
        self.schema_dict = None
        self.rhost = rhost
        self.auth = auth
        self.verify = verify
        self.nossl = nossl
        self.proto = 'http' if nossl else 'https'
        # get /redfish/v1/JSONSchemas collection and store it as a dict
        if service_root is not None and "JsonSchemas" in service_root and "@odata.id" in service_root["JsonSchemas"]:
            json_schema_uri = service_root["JsonSchemas"]["@odata.id"]
            logging.info("SchemaValidation:__init__: json_schema_uri = {}".format(json_schema_uri))
            schemas = self.get_resource(json_schema_uri)
            if schemas is not None and "Members" in schemas:
                self.schema_dict = {elt["@odata.id"].rsplit("/", 1)[1]: elt["@odata.id"] for elt in schemas["Members"]}
                logging.debug("SchemaValidation:__init__: schema_dict = {}".format(self.schema_dict))
            else:
                logging.warning("SchemaValidation:__init__: unable to read schema Members")
        else:
            logging.warning("SchemaValidation:__init__: unable to get JsonSchemas from service root")

    def get_resource(self, uri):
        name = uri.split('/')[-1]
        logging.debug("get_resource: Getting {} resource with uri {}".format(name, uri))
        try:
            r = requests.get(self.proto + '://' + self.rhost + uri, auth=self.auth, verify=self.verify)
            if r.status_code == requests.codes.ok:
                d = r.json()
                if d is not None:
                    logging.debug("get_resource: {} resource: {}".format(name, d))
                    return d
                else:
                    logging.error("get_resource: No JSON content for {} found in response".format(uri))
            else:
                logging.error("get_resource: Received unexpected response for resource {}: {}".format(name, r))
            return None
        except requests.exceptions.RequestException as e:
            logging.error("get_resource: Exception received while tying to fetch uri {}, error = {}".format(uri, e))
            return None

    @staticmethod
    def split_odata_type(json_data):
        """
        Get the @odata.type entry from the JSON payload, split into namespace and type and return as a tuple
        """
        ns = type_name = None
        if json_data is not None and "@odata.type" in json_data:
            odata_type = json_data["@odata.type"]
            ns, type_name = odata_type.rsplit('.', 1)
            ns = ns.strip('#')
            logging.info("SchemaValidation:split_odata_type: odata = {}, namespace = {}, typename = {}"
                         .format(odata_type, ns, type_name))
        else:
            logging.info("SchemaValidation:split_odata_type: JSON payload empty or no @odata.type found")
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
            logging.error("SchemaValidation:get_json_schema: No '@odata.type' found in JSON payload")
            return None
        data = uri = None
        if ns is not None and ns in self.schema_dict:
            uri = self.schema_dict[ns]
        elif type_name is not None and type_name in self.schema_dict:
            uri = self.schema_dict[type_name]
        if uri is not None:
            data = self.get_resource(uri)
        if data is not None and "Location" in data:
            location = data["Location"]
            if len(location) > 0 and "Uri" in location[0]:
                uri = location[0]["Uri"]
                schema = self.get_resource(uri)
            else:
                logging.error("SchemaValidation:get_json_schema: 'Uri' not found in Location[0]")
        else:
            logging.error("SchemaValidation:get_json_schema: 'Location' not found from uri {}".format(uri))
        return schema

    @staticmethod
    def validate_json(json_data, schema):
        """
        Validate the JSON response against the schema
        """
        if json_data is None:
            # JSON payload not required
            logging.info("SchemaValidation:validate_json: No JSON payload to validate")
            return 0, None
        if schema is None:
            # Redfish schema not required
            logging.info("SchemaValidation:validate_json: No JSON schema for validation")
            return 0, None
        # validate the json response against the schema
        try:
            logging.debug("SchemaValidation:validate_json: JSON to be validated: {}".format(json_data))
            logging.debug("SchemaValidation:validate_json: JSON schema for validation: {}".format(schema))
            jsonschema.validate(json_data, schema)
        except jsonschema.ValidationError as e:
            logging.error("SchemaValidation:validate_json: JSON schema validation error: {}".format(e.message))
            return 4, e.message
        except jsonschema.SchemaError as e:
            logging.error("SchemaValidation:validate_json: JSON schema error: {}".format(e.message))
            return 8, e.message
        else:
            logging.info("SchemaValidation:validate_json: JSON schema validation successful")
            return 0, None
