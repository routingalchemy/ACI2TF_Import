<h1 align="center">Road to IaC: ACI to Terraform Importer </h1>
<h3 align="center">ACI2TF</h3>

  <p align="center">
    A tool to get ACI objects from APIC data and create an import blocks file that Terraform can use
  </p>
</div>

# About the project

IaC and automation is good and has plenty of benefits.
Using it from day zero is much easier then from day X. Rarely anybody wants to code its infrastructure again just to move into IaC. 
Getting all the objects/resources into terraform is very time consuming and sometime impossible.
The info is there within the APIC but the problem is that is needs to be retrieved and put into the correct format.
To be able to do it two sets of code(IaC) needs to be written. Terraform needs to ```import``` the objects and have the `resource` definitions for those objects too.
This tool solves the first major step on the road the import part.

## Background info
### Cisco ACI API
The ACI object model represents the complete configuration and runtime state of every single software and hardware component in the entire infrastructure. The object model is made available through standard REST API interfaces, making it easy to access and manipulate the configuration and runtime state of the system.
[LINK](https://developer.cisco.com/docs/aci/#!introduction).


### Terraform Import 
"Terraform can import existing infrastructure resources. This functionality lets you bring existing resources under Terraform management. Terraform v1.5.0 and later supports import blocks. Unlike the terraform import command, you can use import blocks to import more than one resource at a time, and you can review imports as part of your normal plan and apply workflow. Learn more about import blocks."
[LINK](https://developer.hashicorp.com/terraform/language/import)

Experimental: While we do not expect to make backwards-incompatible changes to syntax, the `-generate-config-out` flag and how Terraform processes imports during the plan stage and generates configuration may change in future releases.

# The ACI Terraform Importer Script

The tool's main function is to create `import` blocks for the Cisco ACI (Stanalone or Multi-Pod) (Tenant and Fabric) resources that can be imported to terraform.

The Tenant objects are everything from the Tenant tab of the APIC GUI while the Fabric objects represents everything that are not on the **Tenant** tab (obviously) (Fabric policies, Access policies, System Settings, Virtual networking, etc... )


## Getting Started
Pre-requisites:
- Basic terraform knowledge
- Understand your ACI objects
- Access to the fabric APIC 

Clone and install requirements.
```
git clone https://github.com/routingalchemy/ACI2TF_Import 
cd ACI2TF_Import
pip install -r requirements.txt 
```

The 2 python files in the directory are:
 - `aci2tf_app.py` - main app
 - `resources.py` - additional data which holds information about the supported ACI objects and the terraform resource names in various formats that the app uses

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage
1. Define an instance and provide the login credentials `import_data = aci2tf_import("HOSTNAME/IP","USERNAME","PASSWORD")`
2. To import ACI objects. On the instance, call the `object_importer` method  like `import_data.object_importer()`. By default it imports **Tenant** objects from the the *Common* tenant. 
    - For importing a different tenant objects the `import_data.object_importer("tenant","NAME-OF-TENANT")` syntax should be used.
    - For importing the fabric objects `import_data.object_importer("fabric")` 

3. (Optionally) if you want a backup from the APIC data that is used during the script run, in the ```__init__``` method set the ```self.bakcup``` to ```True``` (a lot of data but can be handy later for writing or checking the resource blocks later)
4. (Optionally) you can import the ```default``` object from ACI  with setting the ```self.exclude_defaults``` to ```False```. Not mandatory, but if you are using them in your config  than it is quite important. (default objects are placed into a separate ```import_default.tf.bak``` by default :) )
4. Run the script
5. Check import blocks for required amendments(name labels)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Road to IaC (a possible way to do it)
1. Create the import blocks with the tool (it generates import.tf)
2. Check the resource names that was generated by the script and amend if not suits your needs (See Output and Caveat Sections for clarification)
3. From here there are 2 possibilities:

    - Run a ```terraform plan -generate-config-out=generated.tf``` (terraform 1.5 or higher is required for this feature(see section XYZ)) with the import block .tf file. This will generate your terraform resources (Experimental feature currently but based on my tests it works quite well)
    - Write your own resources based on your ACI configuration (a backup form the config that was used for the import block creation can help in that (see section Usage point 3))

4. Run a ```terraform plan``` and see how good is your terraform code. (Harmless as you don't apply any changes)
    - It is possible that there will be errors durng the run(s). The script/import is flawless, it just helps to do the harder part of the work. A little engineering might be needed to fix some resources.

Example import output:
```
Plan: 519 to import, 0 to add, 44 to change, 0 to destroy.
```
In this example:
- based on the import blocks and the code, terraform plan is to import ```519``` object. Looks promising. No need to do anything with these.
- the second most important bit is that ```0 to destroy```. It is a good sign. **(Don't apply anything if there are any destroys in the code!!!)** 
- ```44 to change``` is terraform wants to add the ```annotation = "orchestrator:terraform"``` to the resource. **(But, always check the plan for changes!)**
- ```0 to add``` it might be possible that during import terraform wants to add 1-2 resources. Usually it is harmless but as always **check the detailed plan for changes!**

5. If happy with the plan than apply the code and welcome to the world of IaC

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Examples
Create an instance with the login credentials (for example the cisco ACI sandbox) `import_data = aci2tf_import("sandboxapicdc.cisco.com", "admin", "!v3G@!4@Y")`

Print the list of available tenants `import_data.list_tenants()` (optional if needed/for testing the access)

Call the importer function with default values `import_data.object_importer()` Create import for the common tenant 

Create import for the CORP-DEV tenant `import_data.object_importer("tenant","CORP-DEV") `

Create import for the fabric objects `import_data.object_importer("fabric")`

*The following 3 lines would create import file for CORP-DEV tenant and the fabric configuration.*

Optionally you can run ```aci2tf_import.import_block_stats()``` which gathers basic stats on the imported elements
```
import_data = aci2tf_import("sandboxapicdc.cisco.com", "admin", "!v3G@!4@Y")
import_data.object_importer("tenant","CORP-DEV")
import_data.object_importer("fabric")
aci2tf_import.import_block_stats()
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Output (updated)
Import block naming standard is ```<TERRAFORM_RESOURCE_NAME>.<tenant or fabric>-OBJ<INCLEMENTING_NUMBER>-<ACI_OBJECT_ID with RN prefix>``` where
- ```<TERRAFORM_RESOURCE_NAME>``` is the terraform resource name where we want to import the object into
- ```<tenant or fabric>-OBJ<INCLEMENTING_NUMBER>-``` is an generic object identifier can be for example
    - ```tenant-OBJ00001``` a tenant object
    - ```fabric-OBJ00005``` a fabric object
- The ```<ACI_OBJECT_ID with RN prefix>``` is the objects RN(relative name) identifier":
    - ```lldpIfP_system_lldp_disabled``` as a fabric lldp object
    - ```epg_Web_EPG``` as a tenant EPG object

Import Block output examples
```
# Tenant:
# A BD Subnet 
import {
  to = aci_subnet.tenant-OBJ00028-subnet__10_1_102_1_24_
  id = "uni/tn-B/BD-L3_TEST/subnet-[10.1.102.1/24]"
}

# An EPG 
import {
  to = aci_application_epg.tenant-OBJ00027-epg_Web_EPG
  id = "uni/tn-Cloud/ap-Fantastic-APP/epg-Web-EPG"
}

#Fabric:
#A L3out domain profile
import {
  to = aci_l3_domain_profile.fabric-OBJ00161-l3dom_DOM_DR_L3Out
  id = "uni/l3dom-DOM_DR_L3Out"
}

#A vlan range 
import {
  to = aci_ranges.fabric-OBJ00148-from__vlan_10__to__vlan_19_
  id = "uni/infra/vlanns-[on-prem]-static/from-[vlan-10]-to-[vlan-19]"
}
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Caveats

- Multi-Site and NDO managed objects are not supported at the moment. 
- Although the terraform ACI provider supports it, the **cloud** objects are currently not implemented for import yet. 
- Terraform resource names are sometime not meaningful but unique. It needs a manual amendment to the desired format.
- Some objects are imported in Tenant and Fabric section too. (WIP)


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap
 
 - [ ] NDO object import
 - [ ] Offline import (from an APIC output file)
 - [ ] Cloud object import
 - [ ] Resource block generation (maybe)
 - [ ] Updater for the the resources.py file
 - [X] Filter option for ```default``` objects. 
 - [ ] More granular import options
 - [X] Impove terraform resource naming

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Notes

 - The project files are formatted with [Black](https://github.com/psf/black)
 - Terraform has to be at least version 1.5 (for import block support)
 - The tool supports objects/resources based on terraform's ACI provider [Version 2.14.0](https://registry.terraform.io/providers/CiscoDevNet/aci/2.14.0/docs)
 - Code has been tested on ACI 6.x only

<p align="right">(<a href="#readme-top">back to top</a>)</p>
