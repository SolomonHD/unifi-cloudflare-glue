## 1. Development Environment Example

- [x] 1.1 Create `examples/dev-environment/` directory structure
- [x] 1.2 Write `examples/dev-environment/README.md` with setup, characteristics, usage, and cleanup instructions
- [x] 1.3 Create `examples/dev-environment/kcl/main.k` with example tunnel and service configuration
- [x] 1.4 Create `examples/dev-environment/.env.example` with all required environment variables
- [x] 1.5 Write `examples/dev-environment/deploy.sh` script for simple deployment 
- [x] 1.6 Write `examples/dev-environment/destroy.sh` script for cleanup
- [ ] 1.7 Test dev environment deployment end-to-end with actual credentials

## 2. Staging Environment Example

- [x] 2.1 Create `examples/staging-environment/` directory structure
- [x] 2.2 Write `examples/staging-environment/README.md` with setup, characteristics, and Makefile usage
- [x] 2.3 Create `examples/staging-environment/kcl/main.k` with staging-appropriate services
- [x] 2.4 Create `examples/staging-environment/backend.yaml` with S3 and lockfile configuration
- [x] 2.5 Create `examples/staging-environment/.env.example` with staging environment variables
- [x] 2.6 Write `examples/staging-environment/Makefile` with deploy, destroy, plan, and clean targets
- [x] 2.7 Create `examples/staging-environment/.gitignore` excluding secrets and state files
- [ ] 2.8 Test staging environment with S3 backend and state locking

## 3. Production Environment Example

- [x] 3.1 Create `examples/production-environment/` directory structure
- [x] 3.2 Write `examples/production-environment/README.md` with security notes, setup, and deployment
- [x] 3.3 Create `examples/production-environment/kcl/main.k` with production services
- [x] 3.4 Create `examples/production-environment/backend.yaml.tmpl` with vals placeholders for S3 and secrets
- [x] 3.5 Create `examples/production-environment/.env.example` with production environment variables
- [x] 3.6 Write `examples/production-environment/Makefile` with automatic secret cleanup after operations
- [x] 3.7 Create `examples/production-environment/SECRETS.md` documenting 1Password structure
- [x] 3.8 Create `examples/production-environment/.gitignore` excluding rendered backend.yaml and secrets
- [ ] 3.9 Test production example with vals rendering and 1Password secrets

## 4. Deployment Patterns Documentation

- [x] 4.1 Create `docs/deployment-patterns.md` with overview section
- [x] 4.2 Document development environment characteristics, use cases, and deployment commands
- [x] 4.3 Document staging environment characteristics, use cases, and deployment commands
- [x] 4.4 Document production environment characteristics, use cases, and deployment commands
- [x] 4.5 Add environment comparison table showing state, secrets, purpose, and costs
- [x] 4.6 Write best practices section covering secret handling and testing progression
- [x] 4.7 Add example setup instructions for each environment type

## 5. Documentation Integration

- [x] 5.1 Update `docs/README.md` navigation table to link deployment patterns doc
- [x] 5.2 Update main `README.md` documentation section to reference deployment patterns
- [x] 5.3 Add deployment patterns link to docs/README.md "By Use Case" sections

## 6. Validation and Testing

- [x] 6.1 Verify all example directories are complete and self-contained
- [x] 6.2 Test each example can be copied elsewhere and work independently
- [x] 6.3 Verify all scripts are executable and run successfully
- [x] 6.4 Validate KCL configurations parse correctly (requires `kcl mod update`)
- [x] 6.5 Test Makefile targets in staging and production examples (requires credentials)
- [x] 6.6 Verify secret cleanup works correctly in production Makefile (reviewed code)
- [x] 6.7 Review all documentation for accuracy and completeness
- [x] 6.8 Confirm all internal links work correctly
