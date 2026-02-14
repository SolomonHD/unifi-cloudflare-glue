## Why

Users encounter errors during installation, configuration, and deployment but lack a systematic troubleshooting resource. A comprehensive guide with decision trees and solutions for common issues will reduce support burden and improve user experience. This addresses the placeholder content currently in `docs/troubleshooting.md`.

## What Changes

- Expand `docs/troubleshooting.md` from placeholder to comprehensive troubleshooting guide
- Document common errors for each component:
  - Dagger module errors (module not found, secret parameters, container execution)
  - Terraform errors (backend initialization, state locks, provider authentication)
  - KCL validation errors (MAC format, DNS loops, schema validation)
  - UniFi Controller errors (TLS certificates, API authentication, connectivity)
  - Cloudflare API errors (zone not found, permissions, rate limits)
- Add decision trees for systematic debugging
- Include diagnostics commands for each component
- Add FAQ section with 10+ common questions
- Link from main README and related documentation

## Capabilities

### New Capabilities

- `error-reference`: Comprehensive catalog of error messages organized by component, each with symptoms, causes, solutions, and prevention tips
- `diagnostics-commands`: Documented diagnostic commands for verifying system health across Dagger, Terraform, KCL, UniFi, and Cloudflare
- `troubleshooting-decision-trees`: Flowchart-style decision trees for systematic debugging of deployment failures, authentication issues, and state management problems

### Modified Capabilities

- `documentation`: Update to include links to the new troubleshooting guide from relevant sections

## Impact

- **Files Modified**:
  - `docs/troubleshooting.md` (major expansion)
  - `docs/README.md` (update index)
  - `README.md` (add troubleshooting link)
- **User Experience**: Self-service troubleshooting reduces support requests
- **Documentation**: Links from other docs to relevant troubleshooting sections
