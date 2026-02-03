# Google Cloud Storage Backend Configuration for Terraform State
#
# This file configures Terraform to store state in a Google Cloud Storage (GCS)
# bucket. This enables team collaboration and provides state persistence across
# container executions.
#
# Usage:
#   dagger call deploy \
#       --backend-type=gcs \
#       --backend-config-file=./gcs-backend.hcl \
#       ... other parameters ...
#
# Required Environment Variables (choose one authentication method):
#
# Option 1: Service Account Key File (recommended for CI/CD)
#   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
#
# Option 2: Application Default Credentials (for local development)
#   Run: gcloud auth application-default login
#
# Option 3: Access Token
#   export GOOGLE_OAUTH_ACCESS_TOKEN="your-oauth-access-token"
#
# See: https://developer.hashicorp.com/terraform/language/settings/backends/gcs

# GCS bucket name
# Must be globally unique across all of Google Cloud
bucket = "my-terraform-state-bucket"

# Path to the state file within the bucket
# Use a descriptive path to organize state by project/environment
prefix = "unifi-cloudflare-glue/terraform"

# Optional: Custom GCS endpoint (for GCS-compatible storage like MinIO)
# endpoint = "https://storage.googleapis.com"

# Optional: Skip authentication validation (useful for local testing)
# skip_credentials_validation = false

# Optional: Enable state file encryption using customer-managed encryption keys (CMEK)
# kms_encryption_key = "projects/my-project/locations/us/keyRings/my-keyring/cryptoKeys/my-key"

# Optional: Impersonate a service account
# impersonate_service_account = "terraform@my-project.iam.gserviceaccount.com"

# Optional: Impersonate with delegation chain
# impersonate_service_account_delegates = [
#   "service-account1@my-project.iam.gserviceaccount.com",
#   "service-account2@my-project.iam.gserviceaccount.com"
# ]

# Optional: Storage class for the state file
# storage_class = "STANDARD"  # Options: STANDARD, NEARLINE, COLDLINE, ARCHIVE

# Note: GCS backend automatically uses Object Versioning for state locking
# Ensure your bucket has Object Versioning enabled
