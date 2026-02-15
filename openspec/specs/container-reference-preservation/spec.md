## ADDED Requirements

### Requirement: Container references are preserved after terraform init
The system SHALL preserve the Dagger container reference after executing `terraform init` to ensure subsequent operations can access files created during initialization.

#### Scenario: deploy_unifi preserves container after init
- **WHEN** `deploy_unifi()` executes `terraform init`
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the new container reference SHALL be used for subsequent operations

#### Scenario: deploy_cloudflare preserves container after init
- **WHEN** `deploy_cloudflare()` executes `terraform init`
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the new container reference SHALL be used for subsequent operations

#### Scenario: destroy preserves container after Cloudflare init
- **WHEN** `destroy()` executes `terraform init` for Cloudflare phase
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the new container reference SHALL be used for subsequent operations

#### Scenario: destroy preserves container after UniFi init
- **WHEN** `destroy()` executes `terraform init` for UniFi phase
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the new container reference SHALL be used for subsequent operations

### Requirement: Container references are preserved after terraform apply
The system SHALL preserve the Dagger container reference after executing `terraform apply` to ensure files created during apply (such as `terraform.tfstate`) are accessible.

#### Scenario: deploy_unifi preserves container after apply
- **WHEN** `deploy_unifi()` executes `terraform apply -auto-approve`
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the state file SHALL be accessible from the preserved container

#### Scenario: deploy_cloudflare preserves container after apply
- **WHEN** `deploy_cloudflare()` executes `terraform apply -auto-approve`
- **THEN** the container variable SHALL be reassigned to capture the post-execution container reference
- **AND** the state file SHALL be accessible from the preserved container

### Requirement: Intermediate steps are properly awaited
The system SHALL properly await intermediate container execution steps even when their output is not directly needed.

#### Scenario: Copy to state directory is awaited
- **WHEN** copying module files to `/state` directory
- **THEN** the operation SHALL be awaited using `_ = await ctr.stdout()` pattern
- **AND** the workdir SHALL only be changed to `/state` after the copy completes

#### Scenario: Terraform init is awaited with preserved reference
- **WHEN** executing `terraform init`
- **THEN** the container reference SHALL be saved before awaiting
- **AND** the operation SHALL be awaited using the preserved reference

### Requirement: Files created during execution are accessible
The system SHALL ensure files created during container execution (like `terraform.tfstate`) remain accessible through the preserved container reference.

#### Scenario: State file is accessible after deploy_unifi
- **WHEN** `deploy_unifi()` completes successfully
- **THEN** the `terraform.tfstate` file SHALL be accessible from the preserved container
- **AND** the file path SHALL correctly resolve based on the working directory

#### Scenario: State file is accessible after deploy_cloudflare
- **WHEN** `deploy_cloudflare()` completes successfully
- **THEN** the `terraform.tfstate` file SHALL be accessible from the preserved container
- **AND** the file path SHALL correctly resolve based on the working directory

#### Scenario: State file is accessible after destroy
- **WHEN** `destroy()` completes successfully
- **THEN** the `terraform.tfstate` file SHALL be accessible from the preserved container
- **AND** the file path SHALL correctly resolve based on the working directory
