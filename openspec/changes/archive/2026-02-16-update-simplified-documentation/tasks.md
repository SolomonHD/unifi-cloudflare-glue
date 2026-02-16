## 1. README.md Updates

- [x] 1.1 Review current README.md Quick Start section
- [x] 1.2 Replace separate deployment examples with unified `deploy` command example
- [x] 1.3 Add section for selective deployment with `--unifi-only` flag
- [x] 1.4 Add section for selective deployment with `--cloudflare-only` flag
- [x] 1.5 Remove all references to `deploy_unifi()` function
- [x] 1.6 Remove all references to `deploy_cloudflare()` function
- [x] 1.7 Add note about API simplification for users following external guides

## 2. docs/dagger-reference.md Updates

- [x] 2.1 Update `deploy` function documentation with unified parameters
- [x] 2.2 Update `plan` function documentation with unified parameters
- [x] 2.3 Update `destroy` function documentation with unified parameters
- [x] 2.4 Add `--unifi-only` flag documentation to all functions
- [x] 2.5 Add `--cloudflare-only` flag documentation to all functions
- [x] 2.6 Add mutual exclusion note for `--unifi-only` and `--cloudflare-only`
- [x] 2.7 Remove `deploy_unifi()` function documentation section
- [x] 2.8 Remove `deploy_cloudflare()` function documentation section
- [x] 2.9 Update function summary table to show unified functions only

## 3. docs/deployment-patterns.md Updates

- [x] 3.1 Update "Full Deployment" pattern to use unified `deploy` command
- [x] 3.2 Remove provider conflict warnings (now resolved)
- [x] 3.3 Remove workarounds for separate deployments
- [x] 3.4 Add "UniFi-Only Deployment" pattern with `--unifi-only` flag
- [x] 3.5 Add "Cloudflare-Only Deployment" pattern with `--cloudflare-only` flag
- [x] 3.6 Update explanation of how combined module simplifies workflow
- [x] 3.7 Add DNS loop prevention warning for Cloudflare-only deployments

## 4. Validation and Review

- [x] 4.1 Verify no references to `deploy_unifi` remain in documentation
- [x] 4.2 Verify no references to `deploy_cloudflare` remain in documentation
- [x] 4.3 Check all examples use correct `--source` parameter syntax
- [x] 4.4 Verify all three documentation files are internally consistent
- [x] 4.5 Review formatting and markdown syntax
- [x] 4.6 Create PR with documentation changes

## Additional Updates

- [x] Updated docs/security.md to use unified `deploy` command examples
- [x] Updated environment variable table in docs/security.md
- [x] Verified consistency across all documentation files
