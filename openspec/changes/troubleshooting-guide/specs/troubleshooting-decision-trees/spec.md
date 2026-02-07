## ADDED Requirements

### Requirement: Decision tree for deployment failures

The troubleshooting guide SHALL provide a decision tree for diagnosing deployment failures at each stage of the deployment pipeline.

#### Scenario: User experiences deployment failure
- **WHEN** a deployment fails at any stage
- **THEN** documentation provides a decision tree starting with "Deployment fails" and branching by stage (configuration generation, terraform init, terraform plan/apply, dagger module) with navigation to relevant error sections

### Requirement: Decision tree for authentication failures

The troubleshooting guide SHALL provide a decision tree for diagnosing authentication failures across all components.

#### Scenario: User experiences authentication failure
- **WHEN** authentication fails for any provider (UniFi, Cloudflare, state backend)
- **THEN** documentation provides a decision tree to identify which credential is failing and navigate to appropriate solution

### Requirement: Decision tree for state management issues

The troubleshooting guide SHALL provide a decision tree for diagnosing Terraform state management issues.

#### Scenario: User experiences state management issue
- **WHEN** Terraform state operations fail (init, lock, migrate)
- **THEN** documentation provides a decision tree to identify backend type, check connectivity, and resolve common state issues

### Requirement: Decision trees use ASCII-art format

All decision trees in the troubleshooting guide SHALL use ASCII-art format embedded in markdown code blocks for universal compatibility.

#### Scenario: User views decision tree in any markdown renderer
- **WHEN** user views the troubleshooting guide in GitHub, VSCode, or any markdown viewer
- **THEN** decision trees render correctly as ASCII-art without requiring external tools or images

### Requirement: Decision trees link to error reference sections

All decision trees SHALL include cross-references to relevant error reference sections for detailed solutions.

#### Scenario: User follows decision tree to solution
- **WHEN** user navigates through a decision tree to identify their issue
- **THEN** the terminal nodes of the tree link to specific error entries in the error reference section
