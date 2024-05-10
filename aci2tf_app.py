import requests
import json
import re
import sys
import os

import resources


class aci2tf_import:
    """Terraform import code generator for ACI object resources"""

    def __init__(self, hostname, username, password, verify=False):
        """Host resource definition"""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.verify = verify
        self.headers = {"Content": "application/json"}
        self.token = {}
        self.bakcup = False  #  save a local copy from the work data
        self.exclude_defaults = True  # exclude default objects from import (beta)
        self.apic_resource = ""
        self.file_name = ""

    def __apic_token_post(self):
        """Logging in and getting a token for further interaction with the APIC"""

        host = "https://{}/api/aaaLogin.json".format(self.hostname)
        data = {
            "aaaUser": {"attributes": {"name": self.username, "pwd": self.password}}
        }
        try:
            response = requests.post(
                host, headers=self.headers, data=json.dumps(data), verify=self.verify
            )
            response.raise_for_status()
            if response.status_code != 204:
                self.token = {
                    "APIC-cookie": response.json()["imdata"][0]["aaaLogin"][
                        "attributes"
                    ]["token"]
                }
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)

    def __api_get(self):
        """Get request for retrieving the resource data"""

        if self.token == {}:
            self.__apic_token_post()
        host = "https://{}{}".format(self.hostname, self.apic_resource)
        try:
            response = requests.get(
                host, cookies=self.token, headers=self.headers, verify=self.verify
            )
            response.raise_for_status()  # raises exception when not a 2xx response
            if response.status_code != 204:
                return response.json()
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)

    def __write_file(self, content):
        """File writer function"""

        with open(self.file_name, "t+a") as fp:
            if type(content) == dict:
                fp.write(json.dumps(content, indent=4))
            else:
                fp.write(content)

    def __tfimport_func(self, tf_rsc, aci_dn):
        """Terraform import statement creator"""

        import_statement = (
            """import {{\n  to = {tf_rsc}\n  id = "{aci_dn}"\n}}\n\n""".format(
                tf_rsc=tf_rsc, aci_dn=aci_dn
            )
        )
        self.__write_file(import_statement)

    def import_block_stats():
        """Stats output on the number of import blocks"""

        for flist in os.listdir():
            if flist.startswith("import_"):
                with open(flist, "r") as fp:
                    words = re.findall("import ", fp.read())
                    print(
                        "{} object imports were created in {}. Check result".format(
                            len(words), flist
                        )
                    )

    def list_tenants(self):  # WIP
        """Geting the list of available tenants from the APIC"""

        self.apic_resource = "/api/node/class/fvTenant.json"
        tenant_data = self.__api_get()
        for data in tenant_data["imdata"]:
            print(data["fvTenant"]["attributes"]["name"])
            # Need more details to print

    def object_importer(self, function="tenant", tenant="common"):
        """Retrieving the ACI cobjects"""

        if function == "fabric":
            query_obj, n = re.subn(
                r"['\[\] ]", "", str(resources.fabric_objects)
            )  # format list of infra object for reuse in the query
            self.apic_resource = "/api/node/mo/uni.json?query-target=subtree&target-subtree-class={}".format(
                query_obj
            )
            self.file_name = "infrastructure_data.json"
        elif function == "tenant":
            self.apic_resource = (
                "/api/node/mo/uni/tn-{}.json?query-target=subtree".format(tenant)
            )
            self.file_name = "tn-{}_data.json".format(tenant)
        else:
            print("Not a valid ACI policy element! EXIT")
            sys.exit(1)
        aci_data = self.__api_get()
        if self.bakcup == True:
            self.__write_file(aci_data)
        aci_obj_num = 0
        for imdata in aci_data["imdata"]:
            for object_key, object_value in imdata.items():
                if object_key in eval("resources.{}_objects".format(function)):
                    self.file_name = "import_{}.tf".format(function)
                    aci_obj_num += 1
                    if (
                        object_value["attributes"].get("name", None) == "default"
                        and self.exclude_defaults is True
                    ):
                        self.file_name = "import_default.tf.bak"
                    object_name = (
                        eval('resources.{}["rnprefix"]'.format(object_key))
                        + object_value["attributes"]["dn"].split(
                            eval('resources.{}["rnprefix"]'.format(object_key))
                        )[1]
                    )
                    terraforn_resource = eval(
                        'resources.{}["terraform_resource"]'.format(object_key)
                    )  # get the corresponding terrform resource
                    object_dn = object_value["attributes"]["dn"]
                    clean_object_name, _n = re.subn(
                        r"\W", "_", object_name
                    )  # replace anything from the object name that is not alphanumeric
                    self.__tfimport_func(
                        "{}.{}-OBJ{}-{}".format(
                            terraforn_resource,
                            function,
                            str(aci_obj_num).zfill(5),
                            clean_object_name,
                        ),
                        object_dn,
                    )


# Examples:
# import_data = aci2tf_import("sandboxapicdc.cisco.com", "admin", "!v3G@!4@Y")  # create an instance with the login credentials
# import_data.list_tenants() # print the list of available tenants
# import_data.object_importer() # create import for the common tenant (calls the importer function with default values)
# import_data.object_importer("tenant", "CORP-DEV")  # create import for the CORP-DEV tenant
# import_data.object_importer("fabric")  # create import for the fabric objects
# aci2tf_import.import_block_stats()  # basic stats on the number of import blocks
