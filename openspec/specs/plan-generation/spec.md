# Spec: Plan Generation

## ADDED Requirements

### Requirement: Plan Function Signature

The Dagger module MUST provide a `plan()` function that accepts configuration and outputs Terraform plans without applying changes.

#### Scenario: Plan function accepts authentication parameters
**Given:** A user wants to generate plans for UniFi and Cloudflare infrastructure  
**When:** They call `dagger call plan` with authentication parameters  
**Then:** The function accepts:
- `--kcl-source` (KCL configuration directory)
- `--unifi-url` (UniFi controller URL)
- `--unifi-api-key` (Secret, recommended) OR
- `--unifi-username` and `--unifi-password` (Secrets, alternative)
- `--unifi-insecure` (boolean, optional, default: false)
- `--cloudflare-token` (Secret)
- `--cloudflare-account-id` (string)
- `--zone-name` (string)

#### Scenario: Plan function accepts state management parameters
**Given:** A user wants to use persistent state or remote backends  
**When:** They call `dagger call plan` with state parameters  
**Then:** The function accepts:
- `--state-dir` (optional Directory for persistent local state) OR
- `--backend-type` (string, default: "local") AND
- `--backend-config-file` (optional File for backend configuration)

#### Scenario: Plan function accepts version control parameters
**Given:** A user wants to pin container versions  
**When:** They call `dagger call plan` with version parameters  
**Then:** The function accepts:
- `--terraform-version` (string, default: "latest")
- `--kcl-version` (string, default: "latest")

#### Scenario: Plan function accepts cache control parameters
**Given:** A user wants to force fresh execution  
**When:** They call `dagger call plan` with cache parameters  
**Then:** The function accepts:
- `--no-cache` (boolean, default: false) OR
- `--cache-buster` (string, default: "")

### Requirement: Plan Generation Process

The `plan()` function MUST generate Terraform plans for both UniFi DNS and Cloudflare Tunnel modules without applying changes.

#### Scenario: Generate plans for both modules
**Given:** Valid KCL configuration and authentication credentials  
**When:** User calls `dagger call plan`  
**Then:** The function:
1. Generates UniFi configuration JSON via `_generate_unifi_config()`
2. Generates Cloudflare configuration JSON via `_generate_cloudflare_config()`
3. Prepares Terraform container for UniFi DNS module
4. Runs `terraform init` for UniFi module
5. Runs `terraform plan -out=unifi-plan.tfplan` for UniFi module
6. Prepares Terraform container for Cloudflare Tunnel module
7. Runs `terraform init` for Cloudflare module
8. Runs `terraform plan -out=cloudflare-plan.tfplan` for Cloudflare module

#### Scenario: Plan execution order matches deployment
**Given:** Both UniFi and Cloudflare plans need to be generated  
**When:** User calls `dagger call plan`  
**Then:** Plans are generated in sequence:
1. UniFi DNS plan first
2. Cloudflare Tunnel plan second  
(Matching the order of `deploy()` function)

### Requirement: Plan Output Formats

The `plan()` function MUST export three formats per module for different use cases.

#### Scenario: Export binary plan files
**Given:** Terraform has generated plan files  
**When:** Plan generation completes  
**Then:** The output directory contains:
- `unifi-plan.tfplan` (binary format, usable with `terraform apply`)
- `cloudflare-plan.tfplan` (binary format, usable with `terraform apply`)

#### Scenario: Export JSON plan files
**Given:** Terraform has generated plan files  
**When:** Plan generation completes  
**Then:** The function runs:
- `terraform show -json unifi-plan.tfplan > unifi-plan.json`
- `terraform show -json cloudflare-plan.tfplan > cloudflare-plan.json`  
And exports both JSON files

#### Scenario: Export human-readable plan files
**Given:** Terraform has generated plan files  
**When:** Plan generation completes  
**Then:** The function runs:
- `terraform show unifi-plan.tfplan > unifi-plan.txt`
- `terraform show cloudflare-plan.tfplan > cloudflare-plan.txt`  
And exports both text files

### Requirement: Plan Summary Generation

The `plan()` function MUST create an aggregated summary of resource changes across both modules.

#### Scenario: Generate plan summary file
**Given:** Terraform plans have been generated for both modules  
**When:** Plan generation completes  
**Then:** The function creates `plan-summary.txt` containing:
- Section for UniFi DNS module with resource counts (add/change/destroy)
- Section for Cloudflare Tunnel module with resource counts (add/change/destroy)
- Overall totals across both modules
- Metadata: timestamp (ISO 8601), Terraform version, KCL version, backend type

#### Scenario: Parse resource counts from plan output
**Given:** Terraform plan command has completed  
**When:** Generating the summary  
**Then:** The function:
1. Attempts to parse JSON output for accurate counts
2. Falls back to text output parsing if JSON parsing fails
3. Extracts "resources to add", "resources to change", "resources to destroy" counts
4. Calculates total changes per module

### Requirement: Output Directory Structure

The `plan()` function MUST return a `dagger.Directory` containing all plan artifacts in a well-organized structure.

#### Scenario: Return directory with all plan artifacts
**Given:** Plan generation has completed successfully  
**When:** User calls `export --path=./plans` on the returned directory  
**Then:** The exported directory contains:
```
plans/
├── unifi-plan.tfplan        # Binary plan (for terraform apply)
├── unifi-plan.json          # Structured JSON (for automation)
├── unifi-plan.txt           # Human-readable (for review)
├── cloudflare-plan.tfplan   # Binary plan
├── cloudflare-plan.json     # Structured JSON
├── cloudflare-plan.txt      # Human-readable
└── plan-summary.txt         # Aggregated summary
```

### Requirement: Container Reference Management

The `plan()` function MUST preserve container references after Terraform plan execution to enable file export.

#### Scenario: Preserve container reference after plan execution
**Given:** Terraform plan command is executed in a container  
**When:** The plan completes  
**Then:** The function:
1. Assigns the post-execution container back to the variable: `container = container.with_exec(["terraform", "plan", ...])`
2. Uses the updated container reference for subsequent file exports
3. Does NOT use the pre-execution container for file access

#### Scenario: Export plan files from correct container
**Given:** Terraform plan has completed and container reference is preserved  
**When:** Exporting plan artifacts  
**Then:** The function:
- Accesses `container.file("/module/plan.tfplan")` from the POST-execution container
- Accesses `container.file("/module/plan.json")` from the POST-execution container
- Accesses `container.file("/module/plan.txt")` from the POST-execution container

### Requirement: State Management Consistency

The `plan()` function MUST support the same state management options as `deploy()` and `destroy()` functions.

#### Scenario: Plan with persistent local state
**Given:** User has a `./terraform-state` directory with existing state  
**When:** They call `dagger call plan --state-dir=./terraform-state`  
**Then:** The function:
1. Mounts the state directory at `/state` in containers
2. Copies Terraform module files to `/state`
3. Runs Terraform operations from `/state`
4. Plan reflects current state from the mounted directory

#### Scenario: Plan with remote backend
**Given:** User has S3 backend configuration in `s3-backend.hcl`  
**When:** They call `dagger call plan --backend-type=s3 --backend-config-file=./s3-backend.hcl`  
**Then:** The function:
1. Generates `backend.tf` with S3 backend configuration
2. Runs `terraform init` with backend configuration
3. Plan reflects current state from the remote S3 backend

#### Scenario: Mutually exclusive state options
**Given:** User provides both state directory and remote backend  
**When:** They call `dagger call plan --state-dir=./state --backend-type=s3 --backend-config-file=./s3.hcl`  
**Then:** The function returns error: `"✗ Failed: Cannot use both --state-dir and remote backend (--backend-type)"`

### Requirement: Authentication Validation

The `plan()` function MUST validate authentication parameters with the same logic as `deploy()` function.

#### Scenario: UniFi authentication mutual exclusivity
**Given:** User provides both API key and username/password  
**When:** They call `dagger call plan --unifi-api-key=env:KEY --unifi-username=env:USER --unifi-password=env:PASS`  
**Then:** The function returns error indicating authentication method conflict

#### Scenario: UniFi authentication completeness (username/password)
**Given:** User provides username without password  
**When:** They call `dagger call plan --unifi-username=env:USER`  
**Then:** The function returns error: `"✗ Failed: Both --unifi-username and --unifi-password required when using username/password authentication"`

#### Scenario: Valid API key authentication
**Given:** User provides UniFi API key  
**When:** They call `dagger call plan --unifi-api-key=env:UNIFI_API_KEY --cloudflare-token=env:CF_TOKEN ...`  
**Then:** The function accepts authentication and proceeds with plan generation

### Requirement: Cache Control

The `plan()` function MUST support cache control to force fresh execution when needed.

#### Scenario: Force fresh execution with no-cache
**Given:** User wants to bypass Dagger cache  
**When:** They call `dagger call plan --no-cache`  
**Then:** The function:
1. Generates epoch timestamp: `str(int(time.time()))`
2. Injects as `CACHE_BUSTER` environment variable in containers
3. Forces re-execution of all cached operations

#### Scenario: Custom cache buster value
**Given:** User provides custom cache key  
**When:** They call `dagger call plan --cache-buster=manual-run-123`  
**Then:** The function injects `CACHE_BUSTER=manual-run-123` in containers

#### Scenario: Mutually exclusive cache control options
**Given:** User provides both no-cache and cache-buster  
**When:** They call `dagger call plan --no-cache --cache-buster=custom`  
**Then:** The function returns error: `"✗ Failed: Cannot use both --no-cache and --cache-buster"`

### Requirement: Error Handling

The `plan()` function MUST provide clear error messages for all failure scenarios.

#### Scenario: Terraform plan failure
**Given:** Terraform plan command fails (e.g., invalid configuration)  
**When:** The function runs `terraform plan`  
**Then:** The function:
1. Captures stderr output
2. Returns error message: `"✗ Failed: {module} Terraform plan failed: {error_details}"`
3. Does NOT proceed to next module

#### Scenario: KCL generation failure
**Given:** KCL configuration is invalid  
**When:** Calling `_generate_unifi_config()` or `_generate_cloudflare_config()`  
**Then:** The function returns error describing KCL validation failure

#### Scenario: Missing required parameters
**Given:** User omits required authentication parameter  
**When:** They call `dagger call plan --unifi-url=... --zone-name=...` (missing tokens)  
**Then:** Dagger returns error: `"required flag(s) not set"`

### Requirement: Documentation

The `plan()` function MUST be documented with comprehensive examples and usage guidance.

#### Scenario: Function docstring includes usage example
**Given:** User inspects the function  
**When:** They run `dagger call plan --help`  
**Then:** The help output shows:
- Function description
- All parameter descriptions
- Example usage with realistic values
- Note about exporting with `export --path=./plans`

#### Scenario: README includes plan function documentation
**Given:** User reads the README  
**When:** They navigate to the "Dagger Functions" section  
**Then:** The documentation includes:
- `plan` function description and purpose
- Example with persistent local state
- Example with remote backend
- Explanation of output formats
- Link to plan summary format

#### Scenario: Changelog documents new feature
**Given:** User reads the CHANGELOG  
**When:** They review the Unreleased section  
**Then:** The changelog includes:
- "Added Terraform plan function" entry
- Description of capabilities
- Example usage snippet
- Security note about plan file contents
