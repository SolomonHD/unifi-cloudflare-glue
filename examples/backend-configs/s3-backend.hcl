# S3 Backend Configuration for Terraform State
# 
# This file configures Terraform to store state in an AWS S3 bucket with
# DynamoDB table for state locking. This enables team collaboration and
# provides state persistence across container executions.
#
# IMPORTANT: Two S3 Locking Options Available
# -----------------------------------------------------------------------------
# This example uses DynamoDB for state locking (traditional approach).
# Terraform 1.9+ also supports S3 native lockfile as an alternative:
#
#   • DynamoDB Locking (this file): Works with all Terraform versions
#     See: s3-backend-dynamodb.yaml for YAML format
#
#   • S3 Native Lockfile: Requires Terraform 1.9+, no DynamoDB needed
#     See: s3-backend-lockfile.yaml for YAML format
#
# For help choosing, see the Backend Configuration Guide:
# https://github.com/SolomonHD/unifi-cloudflare-glue/blob/main/docs/backend-configuration.md
# -----------------------------------------------------------------------------
#
# Usage:
#   dagger call deploy \
#       --backend-type=s3 \
#       --backend-config-file=./s3-backend.hcl \
#       ... other parameters ...
#
# Required Environment Variables (set these in your shell):
#   export AWS_ACCESS_KEY_ID="your-access-key-id"
#   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
#   export AWS_DEFAULT_REGION="us-east-1"
#
# Optional for AWS SSO/role assumption:
#   export AWS_SESSION_TOKEN="your-session-token"
#   export AWS_PROFILE="your-profile"

# S3 bucket where Terraform state will be stored
bucket = "my-terraform-state-bucket"

# Path within the bucket for this specific state file
# Use a descriptive path to organize state by project/environment
key = "unifi-cloudflare-glue/terraform.tfstate"

# AWS region where the S3 bucket and DynamoDB table are located
region = "us-east-1"

# Enable state file encryption at rest using S3 server-side encryption
encrypt = true

# DynamoDB table for state locking (prevents concurrent modifications)
# The table must exist with a primary key named "LockID"
# See: https://developer.hashicorp.com/terraform/language/settings/backends/s3#dynamodb_table
dynamodb_table = "terraform-state-lock"

# Optional: Custom endpoint for S3-compatible storage (e.g., MinIO)
# endpoint = "https://s3.custom-endpoint.com"

# Optional: Skip credentials validation (useful for local testing)
# skip_credentials_validation = false

# Optional: Skip region validation
# skip_region_validation = false

# Optional: Force path-style S3 URLs (for S3-compatible storage)
# force_path_style = false
