import requests
import json
import re
import sys

import aci2tf_resources


class aci2tf_import:
    """Terraform import code generator for ACI object resources"""

    def __init__(self, hostname, username, password, verify=False):
        """Host resource definition"""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.token = {}
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
                host, headers=aci2tf_resources.http_headers, data=json.dumps(data), verify=aci2tf_resources.https_cert_verify
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
                host, cookies=self.token, headers=aci2tf_resources.http_headers, verify=aci2tf_resources.https_cert_verify
            )
            response.raise_for_status()  # raises exception when not a 2xx response
            if response.status_code != 204:
                return response.json()
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)

    def __write_file(self, filename, content):
        """File writer function"""

        with open(filename, "t+a") as fp:
            if type(content) == dict:
                fp.write(json.dumps(content, indent=4))
            else:
                fp.write(content)

    def __tfimport_func(self, tf_rsc, aci_dn):
        """Terraform import statement creator"""

        import_statement = (
            """import {{\n\tto = {tf_rsc}\n\tid = "{aci_dn}"\n}}\n\n""".format(
                tf_rsc=tf_rsc, aci_dn=aci_dn
            )
        )
        self.__write_file("import.tf", import_statement)

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
                "['\[\] ]", "", str(aci2tf_resources.fabric_objects)
            )  # format list of infra object for reuse in the query
            self.apic_resource = "/api/node/mo/uni.json?query-target=subtree&target-subtree-class={}".format(
                query_obj
            )
            filename = "infrastructure_data.json"
        elif function == "tenant":
            self.apic_resource = (
                "/api/node/mo/uni/tn-{}.json?query-target=subtree".format(tenant)
            )
            filename = "tn-{}_data.json".format(tenant)
        else:
            print("Not a valid ACI policy element! EXIT")
            sys.exit(1)
        aci_data = self.__api_get()
        if aci2tf_resources.backup_work_data == True:
            self.__write_file(filename, aci_data)
        aci_obj_num = 0
        for imdata in aci_data["imdata"]:
            object_key = list(imdata.keys())[0]
            if imdata[object_key]["attributes"].get("annotation", None) == "orchestrator:msc":
                break # exclude MSO/NDO managed objects from importing
            if object_key in eval("aci2tf_resources.{}_objects".format(function)):
                tfobject_name, _n = re.subn(
                    r"\W", "_", imdata[object_key]["attributes"]["dn"].lstrip("uni/").lower()
                )  # replace anything from the object name that is not alphanumeric  
                aci_obj_num += 1
                terraforn_resource = eval(
                    'aci2tf_resources.{}["terraform_resource"]'.format(object_key))
                if (
                        imdata[object_key]["attributes"].get("name", None) == "default"
                        and aci2tf_resources.exclude_default_objects is True
                        ):
                        self.file_name = "import_default.tf.bak"
                self.file_name = "import_{}.tf".format(function)
                self.__tfimport_func("{}.{}".format(terraforn_resource,
                    tfobject_name),
                    imdata[object_key]["attributes"]["dn"],
                    )
        print(
            "{} object imports were created. Check import.tf for result".format(
                aci_obj_num
            )
        )


# import_data = aci2tf_import("sandboxapicdc.cisco.com", "admin", "!v3G@!4@Y") # create an instance with the login credentials
# import_data.list_tenants() # print the list of available tenants
# import_data.object_importer() # create import for the common tenant (calls the importer function with default values)
# import_data.object_importer("tenant","CORP-DEV") # create import for the CORP-DEV tenant
# import_data.object_importer("fabric") # create import for the fabric objects