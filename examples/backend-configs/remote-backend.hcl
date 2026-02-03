# Terraform Cloud Backend Configuration
#
# This file configures Terraform to store state in Terraform Cloud (or
# Terraform Enterprise). This enables team collaboration, remote execution,
# and provides state persistence across container executions.
#
# Usage:
#   dagger call deploy \
#       --backend-type=remote \
#       --backend-config-file=./remote-backend.hcl \
#       ... other parameters ...
#
# Required Environment Variable:
#   export TF_TOKEN_app_terraform_io="your-terraform-cloud-api-token"
#
# To create a token:
#   1. Log in to https://app.terraform.io
#   2. Go to User Settings > Tokens
#   3. Create a new API token
#
# See: https://developer.hashicorp.com/terraform/language/settings/backends/remote

# Terraform Cloud organization name
organization = "my-organization"

# Workspace name within the organization
# The workspace will be created automatically if it doesn't exist
workspaces {
  name = "unifi-cloudflare-glue"
}

# Optional: Hostname for Terraform Enterprise (defaults to app.terraform.io)
# hostname = "app.terraform.io"

# Optional: Workspace name prefix for environment-based workspaces
# Use 'prefix' instead of 'name' if you want to use Terraform Cloud's
# environment-based workspace naming (e.g., "myapp-production", "myapp-staging")
# workspaces {
#   prefix = "unifi-cloudflare-glue-"
# }

# Note: When using the remote backend, Terraform Cloud handles state locking
# automatically. No additional configuration is needed for locking.

# Security Note: Store your TF_TOKEN_app_terraform_io as a secret environment
# variable. Never commit it to version control.
