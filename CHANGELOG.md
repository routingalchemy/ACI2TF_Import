# 0.1 initial version
-
# 0.2 update
1. Fixed python warning on "invalid escape sequence" (SyntaxWarning: invalid escape sequence '\['"['\[\] ]", "", str(resources.fabric_objects))
2. Terraform import block indentation "fixed"
3. Changed filename variable (self.file_name)
4. Exluded default objects are written to import_default.tf.bak (just in case needed)
5. Modified and updated stats output

# 0.3 update
1. Improved terraform resource names
2. removed depricated ```aci_vrf_snmp_context_community``` from resources


# 0.4 update
1. Replaced generated resource names to ACI object DNs
2. renamed ```resources.py``` to ```aci2tf_resources.py```
3. Moved some static variables from "self.variable" to the resoucefile
4. Excluded MSO managed objects (annotation:msc) 
5. Fixed the ```http_header``` variable and replaced the non-exsiting "Content" to "Content-Type"

# 0.5 update (current)
1. Updated code to run with CLI based execution 
2. Refactored object_importer function (using match/case instead of if/esle)
2. fixed exclude default objects