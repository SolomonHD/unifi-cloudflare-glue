## Why

Users need practical guidance for deploying infrastructure across different environments (development, staging, production). Currently, the project has basic examples but lacks environment-specific patterns showing appropriate state management, secret handling, and deployment strategies for each context. Without clear examples, users may apply production-grade security to dev environments (over-engineering) or use insecure patterns in production (under-engineering).

## What Changes

- Add three environment-specific example directories demonstrating deployment patterns:
  - `examples/dev-environment/` with ephemeral state for fast iteration
  - `examples/staging-environment/` with remote state for team collaboration  
  - `examples/production-environment/` with vals/1Password integration for secure secret management
- Create `docs/deployment-patterns.md` documenting when and how to use each environment pattern
- Each example includes complete KCL configuration, backend config, deployment scripts/Makefile, README, and .gitignore
- Add environment comparison table showing tradeoffs (state, secrets, cost, purpose)
- Link from main README and docs index to new deployment patterns documentation

## Capabilities

### New Capabilities
- `dev-environment-example`: Development environment with ephemeral state, no persistence, environment variable secrets, zero infrastructure costs
- `staging-environment-example`: Staging environment with remote state (S3), basic secret management, team collaboration support
- `production-environment-example`: Production environment with remote state, vals/1Password secret injection, full security best practices
- `deployment-patterns-documentation`: Comprehensive guide explaining environment characteristics, comparison table, best practices, and when to use each pattern

### Modified Capabilities
<!-- No existing capabilities are being modified at the requirements level -->

## Impact

**Files Created:**
- `examples/dev-environment/` (complete example directory)
- `examples/staging-environment/` (complete example directory)
- `examples/production-environment/` (complete example directory)
- `docs/deployment-patterns.md` (new documentation)

**Files Modified:**
- `docs/README.md` - Add link to deployment patterns
- `README.md` - Add reference to environment examples

**Dependencies:**
- Builds on existing docs structure (prompt 01)
- Leverages vals integration documentation (prompt 02)
- Uses backend configuration patterns (prompt 03)
  
**Benefits:**
- Users can quickly copy-paste appropriate patterns for their environment
- Reduces over-engineering in dev and under-engineering in production
- Clear cost tradeoffs help users make informed decisions
- Complete working examples accelerate onboarding
