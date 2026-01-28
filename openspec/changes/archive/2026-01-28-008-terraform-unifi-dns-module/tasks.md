## Implementation Tasks: Terraform UniFi DNS Module

### 1. Input Variable Definitions
- [x] 1.1 Define `config` variable with object type for devices, domain, and controller settings
- [x] 1.2 Define nested type for device objects (friendly_hostname, domain, service_cnames, nics)
- [x] 1.3 Define nested type for NIC objects (mac_address, nic_name, service_cnames)
- [x] 1.4 Add validation rules for MAC address format
- [x] 1.5 Add validation rules for hostname format (DNS label)
- [x] 1.6 Add validation that each device has at least one NIC

### 2. Data Source Implementation
- [x] 2.1 Create `unifi_user` data source to query devices by MAC address
- [x] 2.2 Normalize MAC addresses to lowercase colon format for consistent lookups
- [x] 2.3 Handle missing MAC addresses gracefully (track but don't fail)
- [x] 2.4 Extract IP addresses from found UniFi devices
- [x] 2.5 Create map of MAC address to assigned IP

### 3. DNS Record Resource Creation
- [x] 3.1 Create `unifi_user` resources with `local_dns_record` for device hostnames
- [x] 3.2 Handle multi-NIC devices (use first NIC's MAC, as UniFi only supports one DNS per MAC)
- [x] 3.3 Use device domain or default_domain for record FQDN
- [x] 3.4 Set appropriate local_dns_record for local DNS
- [x] 3.5 Add record names and IPs to output map

### 4. CNAME Resource Creation
- [x] 4.1 Document UniFi limitation (no CNAME support)
- [x] 4.2 Track service_cnames in outputs for reference
- [x] 4.3 Note: UniFi Controller does not support CNAME records natively

### 5. Output Definitions
- [x] 5.1 Define `dns_records` output - map of hostname to DNS FQDN
- [x] 5.2 Define `device_ips` output - map of MAC to assigned IP
- [x] 5.3 Define `missing_devices` output - list of MACs not found in UniFi
- [x] 5.4 Define `duplicate_macs` output - list of duplicate MACs in config
- [x] 5.5 Define `summary` output - overview of created records and issues
- [x] 5.6 Add descriptive output descriptions

### 6. Error Handling & Edge Cases
- [x] 6.1 Handle missing MAC addresses without failing (configurable strict mode)
- [x] 6.2 Handle devices with no IP assigned yet
- [x] 6.3 Handle duplicate MAC addresses across devices
- [x] 6.4 Handle empty service_cnames gracefully
- [x] 6.5 Add warning outputs for missing devices

### 7. Documentation
- [x] 7.1 Update README.md with module purpose and usage
- [x] 7.2 Document all input variables with types and defaults
- [x] 7.3 Document all outputs with descriptions
- [x] 7.4 Add example usage in README
- [x] 7.5 Document provider authentication requirements
- [x] 7.6 Document UniFi limitations (no CNAME, single DNS per MAC)

### 8. Testing & Validation
- [x] 8.1 Run `terraform validate` successfully
- [x] 8.2 Run `terraform fmt` to ensure formatting
- [x] 8.3 Module uses correct provider resources (`unifi_user` with `local_dns_record`)
- [x] 8.4 Verify module handles missing MACs gracefully
- [x] 8.5 Verify MAC normalization works correctly

## Notes

**UniFi Provider Limitations Discovered:**
- UniFi does not have a `unifi_dns_record` resource type
- DNS is managed via the `unifi_user` resource's `local_dns_record` attribute
- Only one DNS name per MAC address is supported
- CNAME records are not supported by the UniFi Controller API

**Implementation Adjustments:**
- Used `unifi_user` resource with `allow_existing = true` to manage existing clients
- Documented CNAME limitations in README and outputs
- Multi-NIC devices use only the first NIC's MAC for DNS
