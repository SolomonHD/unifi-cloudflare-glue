## 1. Create Module Directory Structure

- [x] 1.1 Create `terraform/modules/glue/` directory
- [x] 1.2 Verify directory is at the same level as `unifi-dns/` and `cloudflare-tunnel/`

## 2. Create Provider Configuration (versions.tf)

- [x] 2.1 Create `versions.tf` with Terraform version constraint `>= 1.5.0`
- [x] 2.2 Add `filipowm/unifi` provider with version `~> 1.0`
- [x] 2.3 Add `cloudflare/cloudflare` provider with version `~> 5.0`
- [x] 2.4 Add `hashicorp/random` provider with version `~> 3.0`

## 3. Create Input Variables (variables.tf)

- [x] 3.1 Add `unifi_config` variable (object type, default null)
- [x] 3.2 Add `unifi_config_file` variable (string type, default "")
- [x] 3.3 Add `cloudflare_config` variable (object type, default null)
- [x] 3.4 Add `cloudflare_config_file` variable (string type, default "")
- [x] 3.5 Add `unifi_url` variable (string, required)
- [x] 3.6 Add `api_url` variable (string, default "")
- [x] 3.7 Add `unifi_api_key` variable (string, sensitive, default "")
- [x] 3.8 Add `unifi_username` variable (string, sensitive, default "")
- [x] 3.9 Add `unifi_password` variable (string, sensitive, default "")
- [x] 3.10 Add `unifi_insecure` variable (bool, default false)
- [x] 3.11 Add `strict_mode` variable (bool, default false)
- [x] 3.12 Add `cloudflare_token` variable (string, sensitive, required)

## 4. Create Module Configuration (main.tf)

- [x] 4.1 Add `provider "unifi"` block with URL, API key, and insecure configuration
- [x] 4.2 Add `provider "cloudflare"` block with API token
- [x] 4.3 Add `module "unifi_dns"` block sourcing `../unifi-dns/`
- [x] 4.4 Pass all UniFi-related variables to unifi_dns module
- [x] 4.5 Add `module "cloudflare_tunnel"` block sourcing `../cloudflare-tunnel/`
- [x] 4.6 Pass all Cloudflare-related variables to cloudflare_tunnel module
- [x] 4.7 Add `depends_on = [module.unifi_dns]` to cloudflare_tunnel module

## 5. Create Output Definitions (outputs.tf)

- [x] 5.1 Add output for `unifi_dns_records` (from module.unifi_dns)
- [x] 5.2 Add output for `unifi_cname_records` (from module.unifi_dns)
- [x] 5.3 Add output for `unifi_device_ips` (from module.unifi_dns)
- [x] 5.4 Add output for `unifi_missing_devices` (from module.unifi_dns)
- [x] 5.5 Add output for `unifi_duplicate_macs` (from module.unifi_dns)
- [x] 5.6 Add output for `unifi_summary` (from module.unifi_dns)
- [x] 5.7 Add output for `unifi_service_cnames_created` (from module.unifi_dns)
- [x] 5.8 Add output for `cloudflare_tunnel_ids` (from module.cloudflare_tunnel)
- [x] 5.9 Add output for `cloudflare_credentials_json` (from module.cloudflare_tunnel, sensitive)
- [x] 5.10 Add output for `cloudflare_public_hostnames` (from module.cloudflare_tunnel)
- [x] 5.11 Add output for `cloudflare_zone_id` (from module.cloudflare_tunnel)
- [x] 5.12 Add output for `cloudflare_tunnel_names` (from module.cloudflare_tunnel)
- [x] 5.13 Add output for `cloudflare_record_ids` (from module.cloudflare_tunnel)

## 6. Create Module Documentation (README.md)

- [x] 6.1 Add module purpose and description
- [x] 6.2 Document prerequisites (UniFi and Cloudflare access)
- [x] 6.3 Document all input variables in a table
- [x] 6.4 Document all outputs in a table
- [x] 6.5 Add usage example with module instantiation
- [x] 6.6 Add example with config_file inputs
- [x] 6.7 Add example with config object inputs
- [x] 6.8 Document when to use combined module vs individual modules

## 7. Validation and Testing

- [x] 7.1 Run `terraform init` in the glue module directory
- [x] 7.2 Run `terraform validate` and confirm no errors
- [x] 7.3 Verify `terraform plan` shows both UniFi and Cloudflare resources
- [x] 7.4 Verify dependency graph shows UniFi before Cloudflare (`terraform graph`)
- [x] 7.5 Test with sample UniFi configuration file
- [x] 7.6 Test with sample Cloudflare configuration file
- [x] 7.7 Verify all outputs are correctly mapped from sub-modules

## 8. Documentation Review

- [x] 8.1 Review README for clarity and completeness
- [x] 8.2 Verify code comments explain the wrapper pattern
- [x] 8.3 Update any references to module paths in project documentation
