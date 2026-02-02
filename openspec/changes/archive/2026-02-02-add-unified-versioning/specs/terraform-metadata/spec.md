# Spec Delta: Terraform Module Version Metadata

## ADDED Requirements

### Requirement: Module Version Comments

Each Terraform module SHALL include version metadata as comments in its versions.tf file.

#### Scenario: unifi-dns module has version header
Given: The terraform/modules/unifi-dns directory exists
When: The versions.tf file is inspected
Then: The file begins with a comment block containing:
  - Module Version: 0.1.0
  - Part of: unifi-cloudflare-glue
  - Source reference showing GitHub URL with version tag

#### Scenario: cloudflare-tunnel module has version header
Given: The terraform/modules/cloudflare-tunnel directory exists
When: The versions.tf file is inspected
Then: The file begins with a comment block containing:
  - Module Version: 0.1.0
  - Part of: unifi-cloudflare-glue
  - Source reference showing GitHub URL with version tag

#### Scenario: Version header format is consistent
Given: Multiple Terraform modules exist
When: Each module's versions.tf is inspected
Then: All version headers follow the same comment format
And: All show the same version number matching the VERSION file
And: All reference the same parent project

### Requirement: Version Comment Structure

The version comment block SHALL provide useful information for module consumers.

#### Scenario: Version comment provides context
Given: A versions.tf file with version comments
When: A user views the file
Then: They can see:
  - The module version (matching VERSION file)
  - The parent project name
  - How to reference a specific version via GitHub source URL

#### Scenario: GitHub source reference is accurate
Given: The version comment includes a source URL
When: The URL is parsed
Then: It follows the format: `github.com/owner/repo//path/to/module?ref=vX.Y.Z`
And: The ref matches the VERSION file with `v` prefix
And: The path correctly points to the module directory

### Requirement: Version Metadata Maintenance

Version comments SHALL be updated as part of the release process.

#### Scenario: Version comments updated during release
Given: The VERSION file is updated to a new version
When: A release is prepared
Then: All Terraform module version comments are updated to match
And: The GitHub source reference is updated to the new version tag
And: All modules show the same version

#### Scenario: Version comments remain after terraform fmt
Given: Terraform modules have version comments
When: `terraform fmt` is run on the modules
Then: The version comment block is preserved
And: The format remains readable
And: Comments stay at the top of the versions.tf file
