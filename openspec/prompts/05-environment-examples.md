# OpenSpec Prompt: Environment-Specific Deployment Examples

## Context

Users need guidance on deploying in different environments (development, staging, production) with appropriate state management, secret handling, and networking configuration for each context.

## Goal

Create environment-specific deployment examples that demonstrate best practices for dev, staging, and production deployments with complete configurations and deployment commands.

## Scope

### In Scope

1. Create environment-specific example directories:
   - `examples/dev-environment/` - Local development with ephemeral state
   - `examples/staging-environment/` - Team staging with remote state
   - `examples/production-environment/` - Production with vals/1Password secrets
2. Each environment includes:
   - Complete KCL configuration
   - Backend configuration (appropriate for environment)
   - Deployment scripts/Makefile
   - README with environment-specific guidance
   - .gitignore for sensitive files
3. Add [`docs/deployment-patterns.md`](../../docs/deployment-patterns.md) explaining environment differences
4. Link from main README to deployment patterns

### Out of Scope

- CI/CD pipeline examples (separate prompt)
- Multi-region deployments
- Disaster recovery procedures
- Monitoring/observability configuration

## Desired Behavior

### Environment Characteristics

#### Development Environment

- **State**: Ephemeral (container-only, no persistence)
- **Secrets**: Environment variables (no secret management)
- **Purpose**: Quick iteration, testing configurations
- **Networking**: Local UniFi controller, test domain
- **Cost**: Zero infrastructure costs

#### Staging Environment

- **State**: Remote backend (S3 with lockfile)
- **Secrets**: Environment variables or basic secret manager
- **Purpose**: Team collaboration, pre-production testing
- **Networking**: Shared UniFi controller, staging subdomain
- **Cost**: Minimal (S3 storage only)

#### Production Environment

- **State**: Remote backend (S3 with DynamoDB or lockfile)
- **Secrets**: vals with 1Password/Vault
- **Purpose**: Production workloads
- **Networking**: Production UniFi controller, production domain
- **Cost**: Full infrastructure costs

### Documentation Structure: docs/deployment-patterns.md

```markdown
# Deployment Patterns

## Overview

Different environments require different deployment strategies.

## Development Environment

### Characteristics
### When to Use
### Example Setup
### Deployment Commands

## Staging Environment

### Characteristics
### When to Use
### Example Setup
### Deployment Commands

## Production Environment

### Characteristics
### When to Use
### Example Setup
### Deployment Commands

## Environment Comparison

| Aspect | Dev | Staging | Production |
|--------|-----|---------|------------|
| State | Ephemeral | Remote | Remote |
| Secrets | Env vars | Env vars | vals/Vault |
| Purpose | Testing | Pre-prod | Production |
| Cost | $0 | Minimal | Full |

## Best Practices

- Never commit secrets
- Use appropriate state management
- Test in staging before production
- Document environment-specific variables
```

### Example Directory Structure

```
examples/
├── dev-environment/
│   ├── README.md
│   ├── kcl/
│   │   └── main.k
│   ├── .env.example
│   └── deploy.sh
├── staging-environment/
│   ├── README.md
│   ├── kcl/
│   │   └── main.k
│   ├── backend.yaml
│   ├── .env.example
│   ├── Makefile
│   └── .gitignore
└── production-environment/
    ├── README.md
    ├── kcl/
    │   └── main.k
    ├── backend.yaml.tmpl  # vals template
    ├── .env.example
    ├── Makefile
    └── .gitignore
```

### Example: Development Environment

#### examples/dev-environment/README.md

```markdown
# Development Environment Example

Quick iteration with ephemeral state, no infrastructure setup required.

## Setup

1. Copy environment file:
   ```bash
   cp .env.example .env
   vim .env  # Edit with your values
   ```

2. Source environment:
   ```bash
   source .env
   ```

3. Deploy:
   ```bash
   ./deploy.sh
   ```

## Characteristics

- **No state persistence** - State lost when container exits
- **Fast iteration** - No backend config required
- **Local testing** - Safe to experiment
- **No costs** - No remote infrastructure

## When to Use

- Testing configuration changes
- Developing new services
- Learning the tool
- Quick experiments

## Clean Up

```bash
./destroy.sh
```
```

### Example: Production Environment

#### examples/production-environment/README.md

````markdown
# Production Environment Example

Production deployment with remote state and vals secret injection.

## Setup

1. Install vals:
   ```bash
   brew install vals
   ```

2. Authenticate with 1Password:
   ```bash
   eval $(op signin)
   ```

3. Create 1Password items (see SECRETS.md)

4. Deploy:
   ```bash
   make deploy
   ```

## Characteristics

- **Remote state** - S3 with DynamoDB locking
- **Secret management** - vals with 1Password
- **Automated cleanup** - Secrets removed after deploy
- **Production-ready** - Full security best practices

## Makefile Targets

- `make deploy` - Deploy infrastructure
- `make destroy` - Destroy infrastructure
- `make plan` - Preview changes
- `make clean` - Clean up secrets

## Security Notes

- Rendered backend.yaml contains plaintext secrets
- Makefile automatically cleans up after operations
- Never commit backend.yaml to version control
- Rotate 1Password secrets regularly
````

## Constraints & Assumptions

### Constraints

- Examples must be complete and runnable
- Must follow security best practices
- Must be appropriate for stated environment
- Avoid over-engineering for simple environments

### Assumptions

- Dev users want fast iteration, not persistence
- Staging users need collaboration, basic security
- Production users need full security, compliance
- Users understand appropriate tradeoffs per environment

## Acceptance Criteria

- [ ] [`examples/dev-environment/`](../../examples/dev-environment/) created with complete example
- [ ] [`examples/staging-environment/`](../../examples/staging-environment/) created with complete example
- [ ] [`examples/production-environment/`](../../examples/production-environment/) created with complete example
- [ ] Each environment has working KCL configuration
- [ ] Each environment has appropriate backend config
- [ ] Each environment has deployment scripts/Makefile
- [ ] Each environment has comprehensive README
- [ ] [`docs/deployment-patterns.md`](../../docs/deployment-patterns.md) created with comparison
- [ ] Environment comparison table included
- [ ] Best practices documented
- [ ] Links added to main README and docs index
- [ ] All examples tested and verified working

## Expected Files/Areas Touched

- `docs/deployment-patterns.md` (new)
- `examples/dev-environment/` (new directory)
  - `README.md` (new)
  - `kcl/main.k` (new)
  - `.env.example` (new)
  - `deploy.sh` (new)
  - `destroy.sh` (new)
- `examples/staging-environment/` (new directory)
  - `README.md` (new)
  - `kcl/main.k` (new)
  - `backend.yaml` (new)
  - `.env.example` (new)
  - `Makefile` (new)
  - `.gitignore` (new)
- `examples/production-environment/` (new directory)
  - `README.md` (new)
  - `kcl/main.k` (new)
  - `backend.yaml.tmpl` (new)
  - `.env.example` (new)
  - `Makefile` (new)
  - `.gitignore` (new)
  - `SECRETS.md` (new - document 1Password structure)
- `docs/README.md` (update index)
- `README.md` (add link)

## Dependencies

- Prompt 01 (docs structure)
- Prompt 02 (vals integration for production example)
- Prompt 03 (backend configuration for staging/production)

## Notes

- Focus on practical, copy-paste examples
- Security appropriate to environment (don't over-engineer dev)
- Cost-conscious approach (minimize infrastructure for lower environments)
- Production example demonstrates best practices
