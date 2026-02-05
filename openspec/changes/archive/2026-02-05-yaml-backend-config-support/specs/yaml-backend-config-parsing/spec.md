## ADDED Requirements

### Requirement: YAML format detection
The system SHALL automatically detect whether a backend configuration file is in YAML or HCL format based on content parsing.

#### Scenario: YAML file provided
- **WHEN** user provides a backend config file in YAML format
- **THEN** system detects it as YAML and proceeds with YAML parsing

#### Scenario: HCL file provided
- **WHEN** user provides a backend config file in HCL format
- **THEN** system detects YAML parsing failure and treats file as HCL

### Requirement: String value conversion
The system SHALL convert YAML string values to properly quoted Terraform HCL strings.

#### Scenario: Simple string value
- **WHEN** YAML contains `bucket: "my-terraform-state"`
- **THEN** system generates `bucket = "my-terraform-state"` in HCL

#### Scenario: Unquoted string value
- **WHEN** YAML contains `bucket: my-terraform-state`
- **THEN** system generates `bucket = "my-terraform-state"` in HCL

#### Scenario: String with special characters
- **WHEN** YAML contains `kms_key_id: "arn:aws:kms:us-east-1:123:key/abc"`
- **THEN** system generates `kms_key_id = "arn:aws:kms:us-east-1:123:key/abc"` in HCL

### Requirement: Numeric value conversion
The system SHALL convert YAML numeric values to unquoted numeric literals in Terraform HCL.

#### Scenario: Integer value
- **WHEN** YAML contains `max_retries: 5`
- **THEN** system generates `max_retries = 5` in HCL (without quotes)

#### Scenario: Float value
- **WHEN** YAML contains `timeout: 30.5`
- **THEN** system generates `timeout = 30.5` in HCL (without quotes)

### Requirement: Boolean value conversion
The system SHALL convert YAML boolean values to Terraform HCL boolean literals.

#### Scenario: True boolean value
- **WHEN** YAML contains `encrypt: true`
- **THEN** system generates `encrypt = true` in HCL (lowercase, unquoted)

#### Scenario: False boolean value
- **WHEN** YAML contains `skip_region_validation: false`
- **THEN** system generates `skip_region_validation = false` in HCL (lowercase, unquoted)

### Requirement: List value conversion
The system SHALL convert YAML lists to Terraform HCL list syntax with proper quoting.

#### Scenario: String list
- **WHEN** YAML contains `allowed_account_ids: ["123456789", "987654321"]`
- **THEN** system generates `allowed_account_ids = ["123456789", "987654321"]` in HCL

#### Scenario: Mixed-type list
- **WHEN** YAML contains a list with strings, numbers, and booleans
- **THEN** system generates HCL list with properly typed elements (strings quoted, numbers/booleans unquoted)

### Requirement: Object value conversion
The system SHALL convert YAML nested objects to Terraform HCL object syntax.

#### Scenario: Simple nested object
- **WHEN** YAML contains:
  ```yaml
  assume_role:
    role_arn: "arn:aws:iam::123:role/TerraformRole"
    session_name: "terraform-session"
  ```
- **THEN** system generates:
  ```hcl
  assume_role = {
    role_arn     = "arn:aws:iam::123:role/TerraformRole"
    session_name = "terraform-session"
  }
  ```

#### Scenario: Deeply nested object
- **WHEN** YAML contains objects nested multiple levels deep
- **THEN** system preserves nesting structure in HCL with proper indentation

### Requirement: Alignment and formatting
The system SHALL generate properly aligned and formatted Terraform HCL output.

#### Scenario: Multiple keys with varying lengths
- **WHEN** YAML contains keys of different lengths
- **THEN** system aligns values using consistent spacing for readability

#### Scenario: Terraform backend format compatibility
- **WHEN** system generates HCL output
- **THEN** output MUST be valid Terraform backend configuration syntax acceptable to `terraform init -backend-config=<file>`

### Requirement: Backward compatibility
The system SHALL maintain support for existing HCL backend configuration files without modification.

#### Scenario: HCL file passed unchanged
- **WHEN** user provides traditional HCL backend config file
- **THEN** system uses file directly without conversion

#### Scenario: No breaking changes to API
- **WHEN** existing code calls Dagger functions with HCL files
- **THEN** behavior remains identical to previous versions

### Requirement: Error handling
The system SHALL provide clear error messages when YAML structure is invalid or unsupported.

#### Scenario: Invalid YAML syntax
- **WHEN** backend config file contains malformed YAML
- **THEN** system returns error with description of YAML parsing failure

#### Scenario: Unsupported YAML features
- **WHEN** YAML file uses features incompatible with Terraform backends (anchors, custom tags)
- **THEN** system gracefully degrades or provides warning about unsupported features
