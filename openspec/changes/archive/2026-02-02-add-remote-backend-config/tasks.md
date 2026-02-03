# Implementation Tasks: add-remote-backend-config

## 1. Function Parameters

- [x] 1.1 Add `backend_type` parameter (str, default="local") to [`deploy_unifi`](../../src/main/main.py:196)
- [x] 1.2 Add `backend_config_file` parameter (Optional[File], default=None) to [`deploy_unifi`](../../src/main/main.py:196)
- [x] 1.3 Add `backend_type` parameter (str, default="local") to [`deploy_cloudflare`](../../src/main/main.py:347)
- [x] 1.4 Add `backend_config_file` parameter (Optional[File], default=None) to [`deploy_cloudflare`](../../src/main/main.py:347)
- [x] 1.5 Add `backend_type` parameter (str, default="local") to [`deploy`](../../src/main/main.py:426)
- [x] 1.6 Add `backend_config_file` parameter (Optional[File], default=None) to [`deploy`](../../src/main/main.py:426)
- [x] 1.7 Add `backend_type` parameter (str, default="local") to [`destroy`](../../src/main/main.py:570)
- [x] 1.8 Add `backend_config_file` parameter (Optional[File], default=None) to [`destroy`](../../src/main/main.py:570)
- [x] 1.9 Add proper type annotations using `Annotated[..., Doc(...)]` for all new parameters

## 2. Backend Configuration Validation

- [x] 2.1 Implement validation in [`deploy_unifi`](../../src/main/main.py:196) to ensure `backend_config_file` required when `backend_type != "local"`
- [x] 2.2 Implement validation in [`deploy_unifi`](../../src/main/main.py:196) to prevent `backend_config_file` when `backend_type == "local"`
- [x] 2.3 Implement same validation in [`deploy_cloudflare`](../../src/main/main.py:347)
- [x] 2.4 Implement same validation in [`deploy`](../../src/main/main.py:426)
- [x] 2.5 Implement same validation in [`destroy`](../../src/main/main.py:570)
- [x] 2.6 Provide clear error messages with usage examples for validation failures

## 3. Backend Block Generation

- [x] 3.1 In [`deploy_unifi`](../../src/main/main.py:196), generate `backend.tf` with empty backend block when `backend_type != "local"`
- [x] 3.2 Use `ctr.with_new_file("/module/backend.tf", backend_hcl)` to inject backend configuration
- [x] 3.3 Implement same backend block generation in [`deploy_cloudflare`](../../src/main/main.py:347)
- [x] 3.4 In [`deploy`](../../src/main/main.py:426), pass backend parameters to both `deploy_unifi` and `deploy_cloudflare` calls
- [x] 3.5 In [`destroy`](../../src/main/main.py:570), generate backend blocks for both Cloudflare and UniFi cleanup phases

## 4. Backend Config File Mounting

- [x] 4.1 In [`deploy_unifi`](../../src/main/main.py:196), mount backend config file at `/root/.terraform/backend.hcl` when provided
- [x] 4.2 Use `ctr.with_file("/root/.terraform/backend.hcl", backend_config_file)` for mounting
- [x] 4.3 Modify `terraform init` command to use `-backend-config=/root/.terraform/backend.hcl` when backend config file provided
- [x] 4.4 Implement same backend config file mounting in [`deploy_cloudflare`](../../src/main/main.py:347)
- [x] 4.5 Implement same backend config file mounting in [`destroy`](../../src/main/main.py:570) for both Cloudflare and UniFi phases

## 5. Error Handling

- [x] 5.1 Add try-except blocks around backend file operations with clear error messages
- [x] 5.2 Ensure Terraform init failures provide actionable error messages related to backend configuration
- [x] 5.3 Test error scenarios: missing backend config file, invalid backend type (handled by Terraform), file read failures

## 6. Documentation

- [x] 6.1 Add "State Management" section to [`README.md`](../../README.md) after "Versioning" section
- [x] 6.2 Document three state management modes: ephemeral local (default), remote backends
- [x] 6.3 Add S3 backend example with complete configuration and AWS credential guidance
- [x] 6.4 Add Azure Blob Storage backend example with ARM environment variable guidance
- [x] 6.5 Add GCS backend example with GOOGLE_APPLICATION_CREDENTIALS guidance
- [x] 6.6 Add Terraform Cloud backend example with token guidance
- [x] 6.7 Update function documentation in docstrings for all four modified functions
- [x] 6.8 Add usage examples showing backend configuration in function docstrings

## 7. Example Backend Configuration Files

- [x] 7.1 Create `examples/backend-configs/` directory
- [x] 7.2 Create `examples/backend-configs/s3-backend.hcl` with S3 configuration template
- [x] 7.3 Create `examples/backend-configs/azurerm-backend.hcl` with Azure configuration template
- [x] 7.4 Create `examples/backend-configs/gcs-backend.hcl` with GCS configuration template
- [x] 7.5 Create `examples/backend-configs/remote-backend.hcl` with Terraform Cloud configuration template
- [x] 7.6 Create `examples/backend-configs/README.md` with usage instructions and security notes
- [x] 7.7 Add comments in all HCL files explaining each parameter and credential sources

## 8. Changelog

- [x] 8.1 Add entry to [`CHANGELOG.md`](../../CHANGELOG.md) under "## [Unreleased]" > "### Added"
- [x] 8.2 Document new `backend_type` and `backend_config_file` parameters for all functions
- [x] 8.3 Include usage examples in changelog entry
- [x] 8.4 Note backward compatibility (default behavior unchanged)

## 9. Testing

- [ ] 9.1 Manually test [`deploy_cloudflare`](../../src/main/main.py:347) with S3 backend using real AWS credentials
- [ ] 9.2 Manually test [`deploy_unifi`](../../src/main/main.py:196) with S3 backend
- [ ] 9.3 Test validation errors: missing backend config file, backend config with local backend
- [ ] 9.4 Test [`destroy`](../../src/main/main.py:570) with matching backend configuration from deploy
- [ ] 9.5 Test backward compatibility: ensure existing usage without backend parameters still works
- [ ] 9.6 Verify generated `backend.tf` file contains correct backend block syntax
- [ ] 9.7 Verify `terraform init` uses `-backend-config` flag when backend config file provided

## 10. Optional Enhancements (Future)

- [ ] 10.1 Consider adding helper function `_configure_backend(ctr, backend_type, backend_config_file)` to reduce duplication
- [ ] 10.2 Add backend configuration examples for additional backends (Consul, HTTP, etc.)
- [ ] 10.3 Document state migration process from local to remote backend
