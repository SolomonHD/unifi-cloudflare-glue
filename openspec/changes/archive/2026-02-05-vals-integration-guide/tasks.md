## 1. Create Main Documentation

- [x] 1.1 Create docs/vals-integration.md with overview and introduction section
- [x] 1.2 Add prerequisites section documenting vals installation and CLI tools
- [x] 1.3 Write comprehensive 1Password integration section with complete workflow
- [x] 1.4 Add AWS Secrets Manager integration section with authentication and usage
- [x] 1.5 Add Azure Key Vault integration section with authentication and usage
- [x] 1.6 Add GCP Secret Manager integration section with authentication and usage
- [x] 1.7 Add HashiCorp Vault integration section with authentication and usage
- [x] 1.8 Write security best practices section covering gitignore, cleanup, rotation, and least privilege
- [x] 1.9 Add troubleshooting section with common vals errors and solutions

## 2. Create Template Files

- [x] 2.1 Create examples/backend-configs/s3-backend-1password.yaml.tmpl with header comments and vals refs
- [x] 2.2 Create examples/backend-configs/azurerm-backend-1password.yaml.tmpl with header comments and vals refs
- [x] 2.3 Create examples/backend-configs/s3-backend-aws-secrets.yaml.tmpl with header comments and vals refs
- [x] 2.4 Create examples/backend-configs/azurerm-backend-azure-kv.yaml.tmpl with header comments and vals refs
- [x] 2.5 Create examples/backend-configs/gcs-backend-gcp-secrets.yaml.tmpl with header comments and vals refs
- [x] 2.6 Verify all template files use consistent header comment format
- [x] 2.7 Verify all vals ref syntax examples are correct for each backend

## 3. Create Automation Example

- [x] 3.1 Create examples/backend-configs/Makefile.example with deploy target
- [x] 3.2 Add destroy target to Makefile.example
- [x] 3.3 Add clean-secrets target to Makefile.example
- [x] 3.4 Add inline comments explaining each workflow step
- [x] 3.5 Demonstrate mixing file-based backend config with environment variable secrets
- [x] 3.6 Show 1Password CLI integration for inline account ID injection
- [x] 3.7 Ensure automatic cleanup through target dependencies

## 4. Update Documentation Index

- [x] 4.1 Update examples/backend-configs/README.md to reference vals templates
- [x] 4.2 Add section to examples/backend-configs/README.md listing all template files
- [x] 4.3 Update docs/README.md to include link to vals-integration.md
- [x] 4.4 Update main README.md to link to vals integration guide
- [x] 4.5 Add vals integration guide to table of contents or features section

## 5. Update Version Control Configuration

- [x] 5.1 Update .gitignore to exclude rendered backend.yaml files
- [x] 5.2 Verify .gitignore allows .yaml.tmpl template files
- [x] 5.3 Add pattern to exclude any *.yaml in examples/backend-configs/ directory

## 6. Validation and Testing

- [x] 6.1 Test s3-backend-1password.yaml.tmpl with actual 1Password credentials
- [x] 6.2 Test azurerm-backend-1password.yaml.tmpl with actual 1Password credentials
- [x] 6.3 Verify vals eval command generates valid YAML output
- [x] 6.4 Test Makefile.example deploy workflow with rendered secrets
- [x] 6.5 Verify automatic cleanup removes rendered files after deployment
- [x] 6.6 Test error scenarios to ensure cleanup occurs even on failure
- [x] 6.7 Verify all documentation links are correct and point to existing files
- [x] 6.8 Proofread all documentation for accuracy and clarity
