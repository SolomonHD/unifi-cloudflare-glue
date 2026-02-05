## ADDED Requirements

### Requirement: SHALL provide S3 lockfile example file

The repository SHALL include a complete, working example file demonstrating S3 native lockfile configuration for Terraform 1.9+.

#### Scenario: User finds s3-backend-lockfile.yaml example
- **WHEN** user browses [`examples/backend-configs/`](../../../../examples/backend-configs/)
- **THEN** file `s3-backend-lockfile.yaml` exists with complete configuration

#### Scenario: User reads inline comments in lockfile example
- **WHEN** user opens `s3-backend-lockfile.yaml`
- **THEN** file includes header comment explaining this is for Terraform 1.9+ with native locking

#### Scenario: User identifies use_lockfile parameter
- **WHEN** user reviews `s3-backend-lockfile.yaml` configuration
- **THEN** file contains `use_lockfile: true` parameter with comment explaining S3 native locking

#### Scenario: User finds complete backend parameters
- **WHEN** user uses `s3-backend-lockfile.yaml` as template
- **THEN** file contains: `bucket`, `key`, `region`, `encrypt`, and `use_lockfile` parameters

#### Scenario: User finds usage instructions
- **WHEN** user reads `s3-backend-lockfile.yaml` header
- **THEN** file includes Dagger command example showing `--backend-type=s3` and `--backend-config-file` usage

### Requirement: SHALL provide DynamoDB locking example file

The repository SHALL include a complete, working example file demonstrating traditional DynamoDB locking configuration.

#### Scenario: User finds s3-backend-dynamodb.yaml example
- **WHEN** user browses [`examples/backend-configs/`](../../../../examples/backend-configs/)
- **THEN** file `s3-backend-dynamodb.yaml` exists with complete configuration

#### Scenario: User reads inline comments in DynamoDB example
- **WHEN** user opens `s3-backend-dynamodb.yaml`
- **THEN** file includes header comment explaining this uses traditional DynamoDB table locking

#### Scenario: User finds DynamoDB table creation command
- **WHEN** user opens `s3-backend-dynamodb.yaml`
- **THEN** file includes complete AWS CLI command for creating DynamoDB table with correct schema

#### Scenario: User identifies dynamodb_table parameter
- **WHEN** user reviews `s3-backend-dynamodb.yaml` configuration
- **THEN** file contains `dynamodb_table` parameter with comment explaining traditional locking

#### Scenario: User verifies compatibility note
- **WHEN** user reads `s3-backend-dynamodb.yaml` header
- **THEN** file states "Compatible with all Terraform versions"

### Requirement: SHALL update existing s3-backend.hcl with notes

The existing [`s3-backend.hcl`](../../../../examples/backend-configs/s3-backend.hcl) file SHALL be updated to include comments explaining both locking options.

#### Scenario: User reads updated HCL file
- **WHEN** user opens `s3-backend.hcl`
- **THEN** file contains comment referencing both `s3-backend-lockfile.yaml` and `s3-backend-dynamodb.yaml` alternatives

#### Scenario: User sees locking option note
- **WHEN** user views S3 backend configuration in HCL format
- **THEN** file includes note that YAML examples demonstrate both S3 lockfile and DynamoDB options

### Requirement: SHALL update existing s3-backend.yaml with notes

The existing [`s3-backend.yaml`](../../../../examples/backend-configs/s3-backend.yaml) file SHALL be updated to reference the specific locking option examples.

#### Scenario: User reads updated YAML file
- **WHEN** user opens `s3-backend.yaml`
- **THEN** file contains comment directing users to specific lockfile vs DynamoDB examples

#### Scenario: User understands current configuration
- **WHEN** user reviews `s3-backend.yaml`
- **THEN** file clearly indicates which locking mechanism (if any) it currently uses

### Requirement: SHALL update backend-configs README with locking explanation

The [`examples/backend-configs/README.md`](../../../../examples/backend-configs/README.md) SHALL be updated to explain the two S3 locking options with links to detailed documentation.

#### Scenario: User reads S3 backend section in README
- **WHEN** user opens [`examples/backend-configs/README.md`](../../../../examples/backend-configs/README.md)
- **THEN** README has dedicated section explaining S3 locking options

#### Scenario: User finds comparison of locking options
- **WHEN** user reads S3 backend README section
- **THEN** README includes brief comparison table showing S3 lockfile vs DynamoDB key differences

#### Scenario: User navigates to detailed guide
- **WHEN** user needs comprehensive backend configuration guidance
- **THEN** README includes link to [`docs/backend-configuration.md`](../../../../docs/backend-configuration.md)

#### Scenario: User identifies file purposes
- **WHEN** user browses backend-configs directory
- **THEN** README explains when to use `s3-backend-lockfile.yaml` vs `s3-backend-dynamodb.yaml`
