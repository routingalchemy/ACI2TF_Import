# 0.1 initial version
-
# 0.2 update
1. Fixed python warning on "invalid escape sequence" (SyntaxWarning: invalid escape sequence '\['"['\[\] ]", "", str(resources.fabric_objects))
2. Terraform import block indentation "fixed"
3. Changed filename variable (self.file_name)
4. Exluded default objects are written to import_default.tf.bak (just in case needed)
5. Modified and updated stats output

# 0.3 update (current)
1. Improved terraform resource names
2. removed depricated ```aci_vrf_snmp_context_community``` from resources
