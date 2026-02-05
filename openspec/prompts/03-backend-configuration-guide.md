# OpenSpec Prompt: Backend Configuration Documentation (S3 Lockfile vs DynamoDB)

## Context

The current documentation mentions S3 backend with DynamoDB locking, but doesn't explain that Terraform 1.9+ introduced native S3 lockfile support as an alternative. Users are confused about which locking mechanism to use and may incorrectly believe DynamoDB is deprecated.

## Goal

Create comprehensive backend configuration documentation that clearly explains both S3 native lockfile (Terraform 1.9+) and traditional DynamoDB locking options, showing when to use each approach and how to configure them.

## Scope

### In Scope

1. Create [`docs/backend-configuration.md`](../../docs/backend-configuration.md) with complete backend guide
2. Document S3 lockfile vs DynamoDB locking comparison
3. Update S3 backend examples to show both options:
   - `s3-backend-lockfile.yaml` (new S3 native locking)
   - `s3-backend-dynamodb.yaml` (traditional DynamoDB locking)
4. Add migration guide from DynamoDB to S3 lockfile
5. Update existing backend examples in [`examples/backend-configs/`](../../examples/backend-configs/)
6. Add decision tree for choosing locking mechanism
7. Clarify that DynamoDB is NOT deprecated

### Out of Scope

- Implementation changes to Dagger module (already supports both)
- Other backend types beyond S3 (Azure, GCS already documented elsewhere)
- State migration tooling
- Terraform version management

## Desired Behavior

### Documentation Structure: docs/backend-configuration.md

```markdown
# Backend Configuration Guide

## Overview

Terraform backend configuration for state management.

## S3 Backend Locking Options

### Option 1: S3 Native Lockfile (Terraform 1.9+)

**Recommended for:** New deployments, simplified infrastructure

```yaml
bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
use_lockfile: true  # S3 native locking
```

**Advantages:**
- No DynamoDB table required
- Lower cost (no DynamoDB charges)
- Automatic stale lock cleanup
- Simpler setup

**Limitations:**
- Requires Terraform 1.9+
- Not backward compatible with older Terraform

### Option 2: DynamoDB State Locking (Traditional)

**Recommended for:** Multi-version Terraform environments, existing deployments

```yaml
bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock  # Traditional locking
```

**Advantages:**
- Works with all Terraform versions
- Battle-tested in production
- Better for multi-team coordination
- More granular lock management

**Limitations:**
- Requires DynamoDB table setup
- Additional AWS costs (~$0.25/month)
- Manual stale lock cleanup

## Decision Tree

```
Do you need Terraform < 1.9 support?
├─ YES → Use DynamoDB locking
└─ NO → Do you need multi-team advanced lock management?
    ├─ YES → Use DynamoDB locking
    └─ NO → Use S3 native lockfile (simpler, cheaper)
```

## Migration from DynamoDB to S3 Lockfile

Step-by-step migration guide

## All Backend Types

- S3 (AWS)
- Azure Blob Storage
- Google Cloud Storage
- Terraform Cloud

## Security Best Practices

Encryption, credentials, least privilege
```

### Example Files to Create/Update

#### examples/backend-configs/s3-backend-lockfile.yaml

```yaml
# S3 Backend with Native Lockfile (Terraform 1.9+)
#
# This configuration uses S3's native lockfile support introduced in Terraform 1.9.
# No DynamoDB table required.
#
# Requirements:
#   - Terraform >= 1.9.0
#   - S3 bucket with versioning enabled (recommended)
#
# Usage:
#   dagger call deploy \
#       --backend-type=s3 \
#       --backend-config-file=./s3-backend-lockfile.yaml \
#       ...

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
use_lockfile: true  # Enable S3 native locking (Terraform 1.9+)

# Optional: Enable versioning for state history
# versioning: true
```

#### examples/backend-configs/s3-backend-dynamodb.yaml

```yaml
# S3 Backend with DynamoDB Locking (Traditional)
#
# This configuration uses the traditional DynamoDB table for state locking.
# Compatible with all Terraform versions.
#
# Requirements:
#   - S3 bucket for state storage
#   - DynamoDB table with primary key "LockID" (string type)
#
# DynamoDB table creation:
#   aws dynamodb create-table \
#       --table-name terraform-state-lock \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST \
#       --region us-east-1
#
# Usage:
#   dagger call deploy \
#       --backend-type=s3 \
#       --backend-config-file=./s3-backend-dynamodb.yaml \
#       ...

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock  # Traditional DynamoDB locking
```

### Update examples/backend-configs/README.md

Add section explaining the two S3 locking options with link to [`docs/backend-configuration.md`](../../docs/backend-configuration.md).

## Constraints & Assumptions

### Constraints

- Must be technically accurate about Terraform version requirements
- Must clearly state DynamoDB is NOT deprecated
- Must provide objective comparison without bias
- All examples must be tested and working

### Assumptions

- Users understand Terraform backend basics
- Users can make informed decisions given clear comparison
- Users may need to support mixed Terraform versions
- Cost is a consideration for some users

## Acceptance Criteria

- [ ] [`docs/backend-configuration.md`](../../docs/backend-configuration.md) created with comprehensive guide
- [ ] S3 lockfile vs DynamoDB comparison clearly documented
- [ ] Decision tree provided for choosing locking mechanism
- [ ] [`examples/backend-configs/s3-backend-lockfile.yaml`](../../examples/backend-configs/s3-backend-lockfile.yaml) created
- [ ] [`examples/backend-configs/s3-backend-dynamodb.yaml`](../../examples/backend-configs/s3-backend-dynamodb.yaml) created  
- [ ] [`examples/backend-configs/s3-backend.hcl`](../../examples/backend-configs/s3-backend.hcl) updated with notes about both options
- [ ] [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md) updated with clear explanation
- [ ] Migration guide from DynamoDB to S3 lockfile included
- [ ] Clarification that DynamoDB is NOT deprecated
- [ ] Links added to main README and docs index
- [ ] All code examples tested and verified

## Expected Files/Areas Touched

- `docs/backend-configuration.md` (new)
- `examples/backend-configs/s3-backend-lockfile.yaml` (new)
- `examples/backend-configs/s3-backend-dynamodb.yaml` (new)
- `examples/backend-configs/s3-backend.hcl` (update with notes)
- `examples/backend-configs/s3-backend.yaml` (update with notes)
- `examples/backend-configs/README.md` (update S3 section)
- `docs/README.md` (update index)
- `README.md` (update references to S3/DynamoDB)

## Dependencies

- Prompt 01 (docs structure must exist)

## Notes

- **Critical**: DynamoDB locking is NOT deprecated - both options are valid
- S3 lockfile is an alternative for Terraform 1.9+, not a replacement
- Users with existing DynamoDB setups should not feel pressured to migrate
- Decision tree should be objective and consider multiple factors
- Cost comparison should be accurate (~$0.25/month for DynamoDB with low usage)
