## Implementation Tasks: Migrate UniFi DNS Module to filipowm/unifi Provider

### 1. Provider Configuration Update
- [x] 1.1 Update versions.tf to use `filipowm/unifi` provider source
- [x] 1.2 Update provider version constraint to ~> 1.0 (or latest stable)
- [x] 1.3 Verify provider authentication configuration

### 2. Data Source Migration
- [x] 2.1 Review filipowm/unifi data sources for device/MAC lookups
- [x] 2.2 Update data source configuration for new provider syntax
- [x] 2.3 Ensure MAC address normalization continues to work

### 3. DNS Resource Migration
- [x] 3.1 Replace `unifi_user` resources with `unifi_dns_record`
- [x] 3.2 Map existing resource attributes to new provider schema
- [x] 3.3 Handle A-record creation for device hostnames
- [x] 3.4 Handle CNAME records if provider supports them
- [x] 3.5 Remove `allow_existing = true` workaround

### 4. Outputs Update
- [x] 4.1 Update `dns_records` output to reference new resource type
- [x] 4.2 Update `device_ips` output to use new data source references
- [x] 4.3 Ensure `missing_devices` output continues to work
- [x] 4.4 Update `summary` output to reference new resources
- [x] 4.5 Add `cname_records` output for new CNAME support

### 5. Documentation Update
- [x] 5.1 Update README.md provider reference to filipowm/unifi
- [x] 5.2 Update provider documentation links
- [x] 5.3 Document any authentication method changes
- [x] 5.4 Update requirements table with new provider version
- [x] 5.5 Remove/update limitations section (CNAME support now added)
- [x] 5.6 Add provider migration notes section

### 6. Validation & Testing
- [x] 6.1 Run `terraform init` to verify provider download
- [x] 6.2 Run `terraform validate` to verify configuration
- [x] 6.3 Run `terraform fmt` to ensure formatting
- [x] 6.4 Verify backward compatibility with existing KCL output format
- [x] 6.5 Document any breaking changes in resource behavior

### 7. Migration Notes
- [x] 7.1 Document state migration requirements (if any)
- [x] 7.2 Provide migration guide for existing deployments
- [x] 7.3 Note any Terraform state manipulation needed

## Summary of Changes

### Provider Migration
- Changed from `paultyng/unifi` (~> 0.41) to `filipowm/unifi` (~> 1.0)

### Data Source
- Continues to use `unifi_user` data source to query devices by MAC address

### Resources
- **A-records**: Now use `unifi_dns_record` with `type = "A"`
- **CNAME-records**: Now supported and created with `type = "CNAME"`
- Removed `allow_existing` workaround (no longer needed)

### Outputs
- `dns_records`: Updated to reference new resource type
- `device_ips`: Unchanged structure
- `missing_devices`: Unchanged
- `cname_records`: New output for CNAME records
- `service_cnames_created`: Replaces `service_cnames_ignored` (now actually created!)

### Input Interface
- Fully backward compatible - no changes to variable schema

### Authentication
- Environment variables updated:
  - `UNIFI_USERNAME` / `UNIFI_PASSWORD`
  - `UNIFI_API_URL`
  - `UNIFI_INSECURE` (for self-signed certs)
  - `UNIFI_SITE` (optional)
