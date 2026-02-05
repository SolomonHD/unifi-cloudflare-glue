# vals Integration Guide

This guide provides comprehensive documentation for using [vals](https://github.com/helmfile/vals) to securely inject secrets from multiple secret management backends into your Terraform backend configuration files.

## Overview

[vals](https://github.com/helmfile/vals) is a tool for configuration management that enables you to reference secrets from various secret management backends using a unified `ref+<backend>://` syntax. By using vals with YAML backend templates, you can:

- Store secrets securely in your preferred secret management system (1Password, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, HashiCorp Vault)
- Keep backend configuration templates in version control without exposing credentials
- Share configuration patterns across teams without sharing actual secrets
- Support multiple environments (dev, staging, production) with different secret sources

## Prerequisites

Before using vals with your backend configurations, you need to install and configure the necessary tools:

### 1. Install vals

**macOS (using Homebrew):**
```bash
brew install vals
```

**Linux:**
```bash
# Download the latest release
curl -L -o vals.tar.gz https://github.com/helmfile/vals/releases/latest/download/vals_Linux_x86_64.tar.gz
tar -xzf vals.tar.gz
sudo mv vals /usr/local/bin/
```

**Verify installation:**
```bash
vals version
```

### 2. Install Secret Backend CLI Tools

Depending on which secret backend you plan to use, install the corresponding CLI:

| Backend | CLI Tool | Installation |
|---------|----------|--------------|
| 1Password | `op` | [1Password CLI](https://developer.1password.com/docs/cli/get-started/) |
| AWS Secrets Manager | `aws` | [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Azure Key Vault | `az` | [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) |
| GCP Secret Manager | `gcloud` | [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) |
| HashiCorp Vault | `vault` | [Vault CLI](https://developer.hashicorp.com/vault/tutorials/getting-started/getting-started-install) |

### 3. Authenticate with Your Secret Backend

Each backend requires authentication before vals can access secrets:

- **1Password**: Sign in with `op signin`
- **AWS**: Configure credentials with `aws configure` or use IAM roles
- **Azure**: Login with `az login`
- **GCP**: Authenticate with `gcloud auth application-default login`
- **Vault**: Set `VAULT_ADDR` and `VAULT_TOKEN` environment variables

## 1Password Integration

1Password is recommended for personal and small team infrastructure management due to its excellent CLI and user experience.

### Setup and Authentication

1. **Install 1Password CLI:**
   ```bash
   # macOS
   brew install 1password-cli
   
   # Linux
   curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
     sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg
   ```

2. **Sign in to your 1Password account:**
   ```bash
   eval $(op signin)
   ```
   
   Or use biometric unlock if configured:
   ```bash
   eval $(op signin --biometric)
   ```

3. **Verify authentication:**
   ```bash
   op vault list
   ```

### Creating Secret Items

Structure your secrets in 1Password for easy reference:

1. **Create a vault** for your infrastructure (e.g., "Terraform State"):
   ```bash
   op vault create "Terraform State"
   ```

2. **Create an item** for your backend credentials:
   ```bash
   op item create \
     --vault="Terraform State" \
     --category="Server" \
     --title="AWS Terraform Backend" \
     --tags="terraform,backend"
   ```

3. **Add fields** to your item:
   ```bash
   # Add access key
   op item edit "AWS Terraform Backend" \
     --vault="Terraform State" \
     "access_key=AKIA..."
   
   # Add secret key (as a password field for security)
   op item edit "AWS Terraform Backend" \
     --vault="Terraform State" \
     "secret_key[password]=wJalrXUtnFEMI..."
   ```

4. **Verify your item:**
   ```bash
   op item get "AWS Terraform Backend" --vault="Terraform State"
   ```

### Template File Structure

Create a YAML template file with vals references to 1Password:

```yaml
# backend.yaml.tmpl
# Render with: vals eval -f backend.yaml.tmpl > backend.yaml

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
access_key: ref+op://Terraform State/AWS Terraform Backend/access_key
secret_key: ref+op://Terraform State/AWS Terraform Backend/secret_key
```

**Reference format:**
```
ref+op://<vault-name>/<item-name>/<field-name>
```

### Rendering and Deployment

1. **Render the template with vals:**
   ```bash
   vals eval -f backend.yaml.tmpl > backend.yaml
   ```

2. **Verify the output** (contains actual secrets - do not commit):
   ```bash
   cat backend.yaml
   ```

3. **Deploy using the rendered backend:**
   ```bash
   dagger call deploy \
       --backend-type=s3 \
       --backend-config-file=./backend.yaml \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=$(op read op://Terraform\ State/Cloudflare\ Account/account_id) \
       --zone-name=example.com
   ```

### Cleanup

**Immediately remove rendered files after use:**
```bash
rm backend.yaml
```

Or use the Makefile automation (see [Automation Example](#automation-example)) for guaranteed cleanup.

## AWS Secrets Manager Integration

AWS Secrets Manager is ideal for AWS-centric environments and integrates seamlessly with IAM roles.

### Setup and Authentication

1. **Install AWS CLI:**
   ```bash
   # macOS
   brew install awscli
   
   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. **Configure credentials:**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, region, and output format
   ```

3. **Verify authentication:**
   ```bash
   aws sts get-caller-identity
   ```

### Creating Secrets

Create secrets in AWS Secrets Manager:

```bash
# Create a secret for Terraform backend credentials
aws secretsmanager create-secret \
  --name terraform-aws-credentials \
  --description "AWS credentials for Terraform state backend" \
  --secret-string '{"access_key":"AKIA...","secret_key":"wJalrXUtnFEMI..."}'
```

Or create individual secrets:

```bash
# Create separate secrets
aws secretsmanager create-secret \
  --name terraform-aws-access-key \
  --secret-string "AKIA..."

aws secretsmanager create-secret \
  --name terraform-aws-secret-key \
  --secret-string "wJalrXUtnFEMI..."
```

### Template File

```yaml
# s3-backend-aws.yaml.tmpl
# Render with: vals eval -f s3-backend-aws.yaml.tmpl > s3-backend-aws.yaml

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
access_key: ref+awssecretsmanager://terraform-aws-access-key
secret_key: ref+awssecretsmanager://terraform-aws-secret-key
```

**Reference formats:**
```yaml
# Single secret (entire value)
value: ref+awssecretsmanager://secret-name

# Specific key from JSON secret
value: ref+awssecretsmanager://secret-name#key

# With AWS profile
value: ref+awssecretsmanager://secret-name?profile=production

# Specific region
value: ref+awssecretsmanager://secret-name?region=us-west-2
```

### Usage

```bash
# Render
evals eval -f s3-backend-aws.yaml.tmpl > s3-backend-aws.yaml

# Deploy
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend-aws.yaml \
    ...

# Cleanup
rm s3-backend-aws.yaml
```

## Azure Key Vault Integration

Azure Key Vault integrates natively with Azure services and supports both service principals and managed identities.

### Setup and Authentication

1. **Install Azure CLI:**
   ```bash
   # macOS
   brew install azure-cli
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login to Azure:**
   ```bash
   az login
   ```

3. **Verify access:**
   ```bash
   az account show
   ```

### Creating Secrets

Create secrets in Azure Key Vault:

```bash
# Create a Key Vault (if not exists)
az keyvault create \
  --name my-terraform-kv \
  --resource-group my-resource-group \
  --location eastus

# Add secrets
az keyvault secret set \
  --vault-name my-terraform-kv \
  --name tf-storage-account-name \
  --value "myterraformstate"

az keyvault secret set \
  --vault-name my-terraform-kv \
  --name tf-client-id \
  --value "your-service-principal-client-id"

az keyvault secret set \
  --vault-name my-terraform-kv \
  --name tf-client-secret \
  --value "your-service-principal-client-secret"
```

### Template File

```yaml
# azurerm-backend-azure.yaml.tmpl
# Render with: vals eval -f azurerm-backend-azure.yaml.tmpl > azurerm-backend-azure.yaml

storage_account_name: ref+azurekeyvault://my-terraform-kv/tf-storage-account-name
container_name: terraform-state
key: unifi-cloudflare-glue/terraform.tfstate
resource_group_name: my-resource-group
client_id: ref+azurekeyvault://my-terraform-kv/tf-client-id
client_secret: ref+azurekeyvault://my-terraform-kv/tf-client-secret
```

**Reference format:**
```yaml
ref+azurekeyvault://<vault-name>/<secret-name>
```

### Usage

```bash
# Render
evals eval -f azurerm-backend-azure.yaml.tmpl > azurerm-backend-azure.yaml

# Deploy
dagger call deploy \
    --backend-type=azurerm \
    --backend-config-file=./azurerm-backend-azure.yaml \
    ...

# Cleanup
rm azurerm-backend-azure.yaml
```

## GCP Secret Manager Integration

GCP Secret Manager integrates with Google Cloud IAM and works seamlessly with GKE and other GCP services.

### Setup and Authentication

1. **Install Google Cloud SDK:**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Linux (see https://cloud.google.com/sdk/docs/install-sdk)
   ```

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   ```

3. **Set your project:**
   ```bash
   gcloud config set project my-project-id
   ```

### Creating Secrets

Create secrets in GCP Secret Manager:

```bash
# Create secrets
echo -n "my-terraform-bucket" | gcloud secrets create tf-state-bucket --data-file=-
echo -n "path/to/service-account-key.json" | gcloud secrets create tf-sa-key-path --data-file=-
```

Or use versions:

```bash
# Add a new version
echo -n "new-value" | gcloud secrets versions add tf-state-bucket --data-file=-
```

### Template File

```yaml
# gcs-backend-gcp.yaml.tmpl
# Render with: vals eval -f gcs-backend-gcp.yaml.tmpl > gcs-backend-gcp.yaml

bucket: ref+gcpsecretsmanager://tf-state-bucket
prefix: unifi-cloudflare-glue/terraform
```

**Reference formats:**
```yaml
# Latest version
value: ref+gcpsecretsmanager://secret-name

# Specific version
value: ref+gcpsecretsmanager://secret-name#versions/1

# With project ID
value: ref+gcpsecretsmanager://secret-name?project=my-project-id
```

### Usage

```bash
# Set credentials for Terraform
credentials: ref+gcpsecretsmanager://tf-sa-key-content

# Render
evals eval -f gcs-backend-gcp.yaml.tmpl > gcs-backend-gcp.yaml

# Deploy
dagger call deploy \
    --backend-type=gcs \
    --backend-config-file=./gcs-backend-gcp.yaml \
    ...

# Cleanup
rm gcs-backend-gcp.yaml
```

## HashiCorp Vault Integration

HashiCorp Vault provides enterprise-grade secret management with multiple authentication methods.

### Setup and Authentication

1. **Install Vault CLI:**
   ```bash
   # macOS
   brew install vault
   
   # Linux
   wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
   unzip vault_1.15.0_linux_amd64.zip
   sudo mv vault /usr/local/bin/
   ```

2. **Set environment variables:**
   ```bash
   export VAULT_ADDR="https://vault.example.com:8200"
   export VAULT_TOKEN="your-vault-token"
   ```

3. **Verify connection:**
   ```bash
   vault status
   ```

### Creating Secrets

Store secrets in Vault KV v2:

```bash
# Enable KV v2 secrets engine (if not already enabled)
vault secrets enable -path=secret kv-v2

# Store secrets
vault kv put secret/terraform/aws \
  access_key="AKIA..." \
  secret_key="wJalrXUtnFEMI..."

vault kv put secret/terraform/azure \
  client_id="your-client-id" \
  client_secret="your-client-secret"
```

### Template File

```yaml
# s3-backend-vault.yaml.tmpl
# Render with: vals eval -f s3-backend-vault.yaml.tmpl > s3-backend-vault.yaml

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
access_key: ref+vault://secret/data/terraform/aws#/data/access_key
secret_key: ref+vault://secret/data/terraform/aws#/data/secret_key
```

**Reference format (KV v2):**
```yaml
# KV v2 format
ref+vault://<mount-path>/data/<path>#/data/<key>

# Examples:
ref+vault://secret/data/terraform/aws#/data/access_key
ref+vault://secret/data/terraform/azure#/data/client_id
```

### Usage

```bash
# Ensure VAULT_ADDR and VAULT_TOKEN are set
export VAULT_ADDR="https://vault.example.com:8200"
export VAULT_TOKEN="your-vault-token"

# Render
evals eval -f s3-backend-vault.yaml.tmpl > s3-backend-vault.yaml

# Deploy
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend-vault.yaml \
    ...

# Cleanup
rm s3-backend-vault.yaml
```

## Security Best Practices

### Gitignore Configuration

**Critical:** Prevent rendered secret files from being committed to version control.

Add to your `.gitignore`:

```gitignore
# Rendered vals backend configs (contain secrets)
examples/backend-configs/*.yaml
!examples/backend-configs/*.yaml.tmpl
!examples/backend-configs/*.hcl

# Or more specific patterns
/backend.yaml
/backend-*.yaml
*.rendered.yaml
```

### Secret Cleanup

Rendered backend files contain plaintext secrets. Always clean up immediately:

```bash
# Manual cleanup
rm backend.yaml

# Automated cleanup (recommended)
# See Makefile automation below
```

### Secret Rotation

Regularly rotate secrets to minimize exposure risk:

1. **Update the secret** in your secret management backend
2. **Re-render** your backend template
3. **Re-deploy** to apply new credentials
4. **Verify** deployment succeeds
5. **Revoke old secrets** (for backends that support it)

### Least Privilege Access

Grant minimal necessary permissions:

| Backend | Recommended Permissions |
|---------|------------------------|
| AWS | `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on state bucket; `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem` on lock table |
| Azure | `Storage Blob Data Contributor` on the container |
| GCP | `roles/storage.objectAdmin` on the bucket |
| 1Password | Vault-specific access, not account-wide |
| Vault | Policy limiting to specific paths |

### Environment Isolation

Use separate secrets for different environments:

```bash
# Development
op://Dev Vault/Terraform Backend/access_key

# Production  
ref+awssecretsmanager://prod/terraform-credentials
```

## Troubleshooting

### Common vals Errors

#### "no value found for key"

**Cause:** The secret reference path is incorrect.

**Solution:**
```bash
# Verify the secret exists
# For 1Password:
op item get "Item Name" --vault="Vault Name"

# For AWS:
aws secretsmanager get-secret-value --secret-id secret-name

# Check the exact field name in your reference
```

#### "authentication failed"

**Cause:** Not authenticated with the secret backend.

**Solution:**
```bash
# 1Password
eval $(op signin)

# AWS
aws sts get-caller-identity

# Azure
az account show

# GCP
gcloud auth application-default print-access-token

# Vault
vault status
```

#### "connection refused"

**Cause:** Cannot connect to secret backend (Vault-specific).

**Solution:**
```bash
# Check VAULT_ADDR
export VAULT_ADDR="https://vault.example.com:8200"

# Verify network connectivity
curl $VAULT_ADDR/v1/sys/health
```

### Authentication Failures

#### AWS "Unable to locate credentials"

```bash
# Check credentials are configured
aws configure list

# Or use environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

#### Azure "Please run 'az login'"

```bash
# Login interactively
az login

# Or use service principal
az login --service-principal \
  --username $ARM_CLIENT_ID \
  --password $ARM_CLIENT_SECRET \
  --tenant $ARM_TENANT_ID
```

#### 1Password "not currently signed in"

```bash
# Sign in
eval $(op signin)

# Or use biometric unlock
eval $(op signin --biometric)
```

### Backend-Specific Issues

#### S3 Backend Access Denied

Ensure the IAM user/role has correct permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/unifi-cloudflare-glue/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:::table/terraform-state-lock"
    }
  ]
}
```

#### Azure Backend Authorization Failed

Ensure service principal has Storage Blob Data Contributor role:
```bash
az role assignment create \
  --assignee $ARM_CLIENT_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/$RG_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"
```

## Automation Example

See the [Makefile.example](../examples/backend-configs/Makefile.example) for a complete automation workflow that:

- Renders secrets automatically
- Deploys infrastructure
- Cleans up rendered files (even on failure)
- Demonstrates 1Password CLI integration

Example usage:
```bash
cd examples/backend-configs
make deploy
make destroy
make clean-secrets
```

## Additional Resources

- [vals Documentation](https://github.com/helmfile/vals)
- [vals Expression Syntax](https://github.com/helmfile/vals?tab=readme-ov-file#expression-syntax)
- [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [HashiCorp Vault](https://www.vaultproject.io/)
