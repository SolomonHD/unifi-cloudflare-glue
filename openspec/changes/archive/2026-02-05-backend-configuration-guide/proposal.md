## Why

Users are confused about Terraform backend locking options, specifically about S3 native lockfile support (Terraform 1.9+) versus traditional DynamoDB locking. Current documentation mentions DynamoDB but doesn't explain the newer S3 lockfile alternative or clarify that DynamoDB is not deprecated, leading to incorrect assumptions and suboptimal configuration choices.

## What Changes

- Create comprehensive backend configuration guide at [`docs/backend-configuration.md`](../../docs/backend-configuration.md)
- Add S3 lockfile vs DynamoDB comparison with decision tree
- Create two distinct S3 backend example files:
  - [`examples/backend-configs/s3-backend-lockfile.yaml`](../../examples/backend-configs/s3-backend-lockfile.yaml) (S3 native locking)
  - [`examples/backend-configs/s3-backend-dynamodb.yaml`](../../examples/backend-configs/s3-backend-dynamodb.yaml) (traditional DynamoDB)
- Add migration guide from DynamoDB to S3 lockfile
- Update [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md) with clear explanations
- Update existing backend examples with notes about both locking options
- Add links from main README to new documentation

## Capabilities

### New Capabilities

- `backend-locking-options-documentation`: Comprehensive documentation comparing S3 native lockfile (Terraform 1.9+) and DynamoDB locking, including advantages, limitations, decision tree, and migration guidance
- `s3-backend-examples`: Separate example configuration files demonstrating both S3 native lockfile and DynamoDB locking patterns with detailed inline comments and setup instructions

### Modified Capabilities

<!-- No existing capabilities being modified - this is new documentation -->

## Impact

**Documentation:**
- New: [`docs/backend-configuration.md`](../../docs/backend-configuration.md)
- Modified: [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md)
- Modified: [`README.md`](../../README.md) (add link to backend configuration guide)
- Modified: [`docs/README.md`](../../docs/README.md) (update docs index)

**Example Files:**
- New: [`examples/backend-configs/s3-backend-lockfile.yaml`](../../examples/backend-configs/s3-backend-lockfile.yaml)
- New: [`examples/backend-configs/s3-backend-dynamodb.yaml`](../../examples/backend-configs/s3-backend-dynamodb.yaml)
- Modified: [`examples/backend-configs/s3-backend.hcl`](../../examples/backend-configs/s3-backend.hcl) (add notes)
- Modified: [`examples/backend-configs/s3-backend.yaml`](../../examples/backend-configs/s3-backend.yaml) (add notes)

**No Code Changes:**
- Dagger module already supports both locking mechanisms
- Terraform modules already work with both approaches
- No breaking changes to existing configurations
