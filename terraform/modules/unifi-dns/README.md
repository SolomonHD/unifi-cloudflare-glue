# UniFi DNS Terraform Module

This Terraform module manages DNS records in UniFi network controllers using the `filipowm/unifi` provider. It works in conjunction with the KCL configuration layer to apply DNS entries generated from a unified service definition.

## Purpose

The `unifi-dns` module provides infrastructure-as-code management for UniFi's local DNS records. It:

- Queries the UniFi Controller for device IP addresses by MAC address
- Creates DNS A-records for device hostnames
- Creates DNS CNAME records for service aliases (now supported!)
- Handles missing devices gracefully with detailed reporting

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| filipowm/unifi provider | ~> 1.0 |

## Provider Authentication

This module uses the `filipowm/unifi` provider. Configure authentication via environment variables:

```bash
export UNIFI_USERNAME="admin"
export UNIFI_PASSWORD="your-password"
export UNIFI_API_URL="https://192.168.1.1"
# Optional: export UNIFI_SITE="default"
export UNIFI_INSECURE="true"  # If using self-signed certificates
```

## Usage

```hcl
module "unifi_dns" {
  source = "./terraform/modules/unifi-dns"

  config = {
    devices = [
      {
        friendly_hostname = "media-server"
        domain            = "internal.lan"
        service_cnames    = ["storage.internal.lan"]  # Now created as CNAME records
        nics = [
          {
            mac_address    = "aa:bb:cc:dd:ee:01"
            nic_name       = "eth0"
            service_cnames = ["nas-eth0.internal.lan"]  # Now created as CNAME records
          }
        ]
      },
      {
        friendly_hostname = "backup-server"
        nics = [
          {
            mac_address = "aa:bb:cc:dd:ee:03"
          }
        ]
      }
    ]
    default_domain = "internal.lan"
    site           = "default"
  }

  strict_mode = false
}
```

## Input Variables

### `config` (required)

Configuration object containing devices, domain settings, and controller settings.

| Field | Type | Description |
|-------|------|-------------|
| `devices` | list(object) | List of device configurations |
| `devices[].friendly_hostname` | string | Hostname for the device (DNS label format) |
| `devices[].domain` | string (optional) | Domain suffix for this device (overrides default_domain) |
| `devices[].service_cnames` | list(string) (optional) | Device-level CNAME aliases (now created as DNS records) |
| `devices[].nics` | list(object) | List of network interfaces (at least one required) |
| `devices[].nics[].mac_address` | string | MAC address of the NIC (aa:bb:cc:dd:ee:ff format) |
| `devices[].nics[].nic_name` | string (optional) | Name/identifier for the NIC |
| `devices[].nics[].service_cnames` | list(string) (optional) | NIC-level CNAME aliases (now created as DNS records) |
| `default_domain` | string | Default domain suffix for all devices |
| `site` | string (optional) | UniFi site name (default: "default") |

### `strict_mode` (optional)

| Type | Default | Description |
|------|---------|-------------|
| `bool` | `false` | If `true`, fail when MAC addresses are not found. If `false`, track missing MACs in outputs. |

## Outputs

| Name | Description |
|------|-------------|
| `dns_records` | Map of device hostname to local DNS record FQDN |
| `cname_records` | Map of CNAME record key to record details (new!) |
| `device_ips` | Map of MAC address to assigned IP (found devices only) |
| `missing_devices` | List of MAC addresses not found in UniFi Controller |
| `duplicate_macs` | List of MAC addresses appearing multiple times in configuration |
| `summary` | Summary of records created and any issues |
| `service_cnames_created` | List of service_cnames from config that were created (replaces service_cnames_ignored) |

## MAC Address Format

MAC addresses are automatically normalized to lowercase colon format (`aa:bb:cc:dd:ee:ff`). The module accepts these formats:

- `aa:bb:cc:dd:ee:ff` (colon-separated, recommended)
- `aa-bb-cc-dd-ee-ff` (hyphen-separated)
- `aabbccddeeff` (no separator)

## Multi-NIC Devices

For devices with multiple NICs:
- Only the first NIC's MAC is used for the primary A-record DNS
- The device's `friendly_hostname` is used as the DNS name
- All NICs are still queried to verify the device exists

## Error Handling

### Missing MAC Addresses

By default (`strict_mode = false`), missing MAC addresses are tracked in the `missing_devices` output without failing:

```hcl
output "missing_devices" {
  value = ["aa:bb:cc:dd:ee:ff"]  # These MACs weren't found
}
```

Enable `strict_mode = true` to fail on missing MACs.

### Duplicate MAC Addresses

Duplicate MAC addresses in the configuration are detected and reported in the `duplicate_macs` output. The first occurrence is used.

## CNAME Support

The `filipowm/unifi` provider supports CNAME records. The module now creates:
- A-records for each device's `friendly_hostname`
- CNAME records for `service_cnames` at both device and NIC levels

CNAMEs point to the primary hostname FQDN (e.g., `hostname.domain`).

## Integration with KCL

This module is designed to consume JSON output from the KCL UniFi generator:

```bash
# Generate JSON from KCL
kcl run kcl/main.k > outputs/unifi.json

# Use in Terraform
terraform apply -var-file=outputs/unifi.json
```

## Provider Migration Notes

This module was migrated from `paultyng/unifi` to `filipowm/unifi` provider:

### What's Changed
- **Provider source**: `paultyng/unifi` → `filipowm/unifi`
- **Provider version**: `~> 0.41` → `~> 1.0`
- **DNS resources**: Now uses native `unifi_dns_record` resources instead of `unifi_user` with `local_dns_record`
- **CNAME support**: Now fully supported and created as actual DNS records
- **Data source**: Still uses `unifi_user` (to look up clients by MAC address)

### State Migration

When migrating existing infrastructure:

1. **Backup your state**: `terraform state pull > backup.tfstate`
2. **Update module code** to this version
3. **Re-initialize**: `terraform init -upgrade`
4. **Import existing DNS records** (if needed):
   ```bash
   terraform import 'unifi_dns_record.dns_record["device-name"]' '<site>/<record-id>'
   ```
5. **Remove old resources** from state (they're managed differently):
   ```bash
   terraform state rm 'unifi_user.dns_record'
   ```

## Notes

- MAC addresses are normalized to lowercase colon format
- Devices with no IP assigned are treated as missing
- DNS records are created using native `unifi_dns_record` resources
- CNAME records are now created instead of just being tracked
