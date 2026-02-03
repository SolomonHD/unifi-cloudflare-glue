# Azure Blob Storage Backend Configuration for Terraform State
#
# This file configures Terraform to store state in an Azure Storage Account
# blob container. This enables team collaboration and provides state persistence
# across container executions.
#
# Usage:
#   dagger call deploy \
#       --backend-type=azurerm \
#       --backend-config-file=./azurerm-backend.hcl \
#       ... other parameters ...
#
# Required Environment Variables (set these in your shell):
#   export ARM_CLIENT_ID="your-service-principal-client-id"
#   export ARM_CLIENT_SECRET="your-service-principal-client-secret"
#   export ARM_SUBSCRIPTION_ID="your-subscription-id"
#   export ARM_TENANT_ID="your-tenant-id"
#
# Alternative: Use Azure CLI authentication (if running locally with az login):
#   export ARM_USE_MSI=true
#   export ARM_SUBSCRIPTION_ID="your-subscription-id"
#
# See: https://developer.hashicorp.com/terraform/language/settings/backends/azurerm

# Azure Storage Account name
# Must be globally unique, 3-24 characters, lowercase letters and numbers only
storage_account_name = "myterraformstate"

# Blob container name within the storage account
# Create this container beforehand in your Azure Storage Account
container_name = "terraform-state"

# Path to the state file within the container
# Use a descriptive path to organize state by project/environment
key = "unifi-cloudflare-glue/terraform.tfstate"

# Azure resource group containing the storage account
resource_group_name = "my-resource-group"

# Optional: Use Azure AD authentication instead of access keys
# When true, ARM_* environment variables are used for authentication
# use_azuread_auth = true

# Optional: Custom endpoint for Azure Stack or sovereign clouds
# endpoint = "https://custom.blob.core.windows.net"

# Optional: Skip SSL certificate validation (not recommended for production)
# skip_cert_verification = false
