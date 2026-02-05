# Getting Started

This guide will help you install and deploy `unifi-cloudflare-glue` for the first time.

## Prerequisites

Before you begin, ensure you have the following:

- **Terraform** >= 1.5.0
- **KCL** installed (`curl -sSL https://kcl-lang.io/script/install-cli.sh | bash`)
- Access to a **UniFi controller**
- A **Cloudflare account** with Tunnel credentials

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SolomonHD/unifi-cloudflare-glue.git
cd unifi-cloudflare-glue
```

### 2. Initialize the KCL Module

```bash
cd kcl
kcl mod add kcl-lang/hello
cd ..
```

### 3. Explore the Example

See the [`examples/homelab-media-stack/`](../examples/homelab-media-stack/) directory for a complete working configuration that demonstrates how to configure services for both UniFi and Cloudflare.

## First Deployment

### Option 1: Using Dagger (Recommended)

The Dagger module provides containerized KCL generation and deployment without requiring local KCL or Terraform installation:

```bash
# Generate UniFi configuration
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json

# Generate Cloudflare configuration
dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
```

### Option 2: Using Local KCL

1. Define your services in KCL (see the [examples](../examples/) directory)
2. Generate JSON configurations:
    ```bash
    cd kcl
    kcl run generators/unifi.k > unifi.json
    kcl run generators/cloudflare.k > cloudflare.json
    ```
3. Apply Terraform configurations:
    ```bash
    cd terraform/modules/unifi-dns
    terraform init
    terraform apply -var-file="../../unifi.json"
    ```

## Next Steps

- **[Dagger Reference](dagger-reference.md)** - Complete function reference and examples
- **[Terraform Modules](terraform-modules.md)** - Using modules standalone
- **[State Management](state-management.md)** - Configure state backends
- **[Security](security.md)** - Security best practices
