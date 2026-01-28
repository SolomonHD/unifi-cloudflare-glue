# Project Context: unifi-cloudflare-glue

## Purpose

A hybrid DNS infrastructure tool that bridges local UniFi network DNS with Cloudflare Tunnel edge DNS using a unified configuration layer. The goal is "define once, deploy everywhere" - users describe their infrastructure in KCL (services, MAC addresses, internal hostnames), and the system generates Terraform-compatible JSON for both UniFi local resolution and Cloudflare public exposure.

## Tech Stack

- **KCL (Kusion Configuration Language)**: Schema definitions and JSON generators
- **Terraform**: Infrastructure provisioning (UniFi DNS, Cloudflare Tunnel)
- **Dagger**: Containerized CI/CD pipelines and CLI tooling
- **Python**: Dagger module SDK

## Project Conventions

### Code Style
- KCL: Expression-based functional style (no statement for-loops)
- Python (Dagger): Async functions, type annotations with `Annotated[..., Doc(...)]`
- Terraform: Standard HCL formatting

### Architecture Patterns
- **Unified Configuration**: Single KCL config generates both UniFi and Cloudflare outputs
- **MAC Address Normalization**: All MACs stored as lowercase colon format (`aa:bb:cc:dd:ee:ff`)
- **One Tunnel Per Device**: Each physical host gets exactly one Cloudflare tunnel
- **DNS Loop Prevention**: Cloudflare local_service_url must use internal domains only

### Testing Strategy
- KCL validation through schema check blocks
- Dagger integration tests with ephemeral resources
- Terraform plan validation before apply

### Git Workflow
- Feature branches for changes
- OpenSpec-managed proposals in `openspec/changes/`
- Prompt archiving to `openspec/archive/prompts/`

## Domain Context

### DNS Architecture
- **UniFi DNS**: Local network resolution for internal services (`.internal.lan`)
- **Cloudflare Tunnel**: Edge connectivity for external access (`.example.com`)
- **Service Distribution**: Services marked as `unifi_only`, `cloudflare_only`, or `both`

### Data Flow
1. User writes KCL defining servers, MACs, NICs, services
2. KCL validation ensures cross-provider consistency
3. KCL generators output:
   - `unifi.json`: Devices with NICs and internal CNAMEs
   - `cloudflare.json`: Tunnels keyed by MAC with services
4. Terraform applies UniFi DNS first (creates local DNS)
5. Terraform applies Cloudflare tunnels (points to now-resolvable local hostnames)

## Important Constraints

1. **No DNS Loops**: Cloudflare local_service_url must use `.internal.lan` domains
2. **MAC Normalization**: Support multiple input formats, normalize to lowercase colons
3. **Existing Resources**: Both modules use data sources for existing infrastructure
4. **External Deployment**: Cloudflared containers run outside Terraform

## External Dependencies

- **UniFi Controller**: API access for DNS management (provider: `filipowm/unifi`)
- **Cloudflare**: Zero Trust Tunnel and DNS management (provider: `cloudflare/cloudflare`)
- **KCL Registry**: Module dependencies from `kcl-lang.io` or GitHub
- **KCL Container Image**: `kcllang/kcl` for Dagger containerized execution

## Module Structure

```
unifi-cloudflare-glue/
├── dagger.json              # Dagger module manifest
├── pyproject.toml           # Python dependencies
├── src/main/main.py         # Dagger functions (UnifiCloudflareGlue class)
├── kcl/                     # KCL schemas and generators
│   ├── schemas/             # Base, UniFi, Cloudflare schemas
│   └── generators/          # unifi.k, cloudflare.k
├── terraform/               # Terraform modules
│   └── modules/
│       ├── unifi-dns/       # UniFi DNS module
│       └── cloudflare-tunnel/  # Cloudflare Tunnel module
└── openspec/                # Change management
    ├── prompts/             # Pending prompts
    ├── changes/             # Active proposals
    └── archive/             # Completed/archived changes
```

## Dagger Module Naming

- **Module name**: `unifi-cloudflare-glue` (from `dagger.json`)
- **Class name**: `UnifiCloudflareGlue` (Dagger generates from module name)
- **Repository**: Can be called via `dagger call -m github.com/user/repo@version unifi-cloudflare-glue <function>`

## Calling Patterns

### Local Development (inside repo)
```bash
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json
```

### Installed Module
```bash
dagger install github.com/user/unifi-cloudflare-glue@version
dagger call -m unifi-cloudflare-glue generate-unifi-config --source=. export --path=./unifi.json
```

### Remote Module
```bash
dagger call -m github.com/user/unifi-cloudflare-glue@version unifi-cloudflare-glue generate-unifi-config --source=. export --path=./unifi.json
```
