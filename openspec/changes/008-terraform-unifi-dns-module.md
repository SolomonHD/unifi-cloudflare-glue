# OpenSpec Prompt: Terraform UniFi DNS Module

## Context

The Terraform UniFi DNS module manages local DNS records in the UniFi Controller. It creates A-records for device NICs and CNAME records for services, querying the UniFi Controller for current IP assignments.

## Goal

Implement a complete Terraform module that manages UniFi DNS records based on JSON input describing devices, NICs, and services.

## Scope

### In Scope
- Define all input variables with validation
- Create data source to query UniFi Controller for device IPs by MAC
- Implement A-record creation for friendly_hostnames (round-robin for multi-NIC)
- Implement CNAME creation for service hostnames
- Define outputs for created records and missing devices
- Handle missing MAC addresses gracefully

### Out of Scope
- Cloudflare module (separate prompt)
- KCL configuration (already implemented)
- Cloudflared deployment (external to Terraform)

## Desired Behavior

1. **Input Variables**:
   ```hcl
   variable "config" {
     type = object({
       devices = list(object({
         friendly_hostname = string
         domain           = string
         service_cnames   = optional(list(string), [])
         nics = list(object({
           mac_address   = string
           nic_name      = optional(string)
           service_cnames = optional(list(string), [])
         }))
       }))
     })
   }
   ```

2. **Data Source Queries**:
   - Query UniFi Controller for each MAC address
   - Return IP address for each found device
   - Track missing MACs for reporting

3. **DNS Record Resources**:
   - Create `unifi_dns_record` A-records for friendly_hostname → IP
   - Round-robin A-records when device has multiple NICs
   - Create `unifi_dns_record` CNAMEs for service hostnames
   - CNAMEs point to friendly_hostname FQDN

4. **Outputs**:
   - `a_records`: Map of created A-records
   - `cname_records`: Map of created CNAMEs
   - `missing_devices`: List of MACs not found in UniFi
   - `device_ips`: Map of MAC to assigned IP

## Constraints & Assumptions

1. **Existing Controller**: UniFi Controller must already exist
2. **Provider Auth**: Credentials passed via environment variables
3. **MAC Format**: Accept any format, normalize internally
4. **Missing Devices**: Warn but don't fail if MAC not found (configurable)

## Acceptance Criteria

- [ ] `terraform/modules/unifi-dns/variables.tf` defines all inputs with validation
- [ ] `terraform/modules/unifi-dns/main.tf` queries UniFi and creates DNS records
- [ ] `terraform/modules/unifi-dns/outputs.tf` returns records and missing devices
- [ ] A-records round-robin for multi-NIC devices
- [ ] CNAMEs correctly point to device FQDNs
- [ ] Module validates input JSON structure
- [ ] Missing MACs are tracked and reported
- [ ] Module README documents usage and variables
- [ ] Terraform validates successfully (`terraform validate`)

## Dependencies

- **Depends On**: 001-project-scaffolding (module structure must exist)
- **Soft Depends On**: 005-kcl-unifi-generator (generates input format)

## Expected Files/Areas Touched

- `terraform/modules/unifi-dns/variables.tf` (complete implementation)
- `terraform/modules/unifi-dns/main.tf` (complete implementation)
- `terraform/modules/unifi-dns/outputs.tf` (complete implementation)
- `terraform/modules/unifi-dns/README.md` (documentation)
