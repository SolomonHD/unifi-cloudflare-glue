## Implementation Tasks: Terraform Cloudflare Tunnel Module

### 1. Input Variable Definitions
- [x] 1.1 Define `config` variable with object type for zone_name, account_id, and tunnels map
- [x] 1.2 Define nested type for tunnel objects (tunnel_name, mac_address, services)
- [x] 1.3 Define nested type for service objects (public_hostname, local_service_url, no_tls_verify)
- [x] 1.4 Add validation that zone_name is non-empty
- [x] 1.5 Add validation that account_id is non-empty
- [x] 1.6 Add DNS loop prevention validation (local_service_url cannot contain zone_name)

### 2. Data Source Implementation
- [x] 2.1 Create `cloudflare_zone` data source to query existing zone by name
- [x] 2.2 Add validation that zone exists (fail if not found)
- [x] 2.3 Extract zone_id from data source for use in resources

### 3. Tunnel Resource Creation
- [x] 3.1 Create `cloudflare_tunnel` resource for each MAC address (one per tunnel)
- [x] 3.2 Use tunnel name from configuration for tunnel resource name
- [x] 3.3 Set account_id and name attributes on tunnel resources
- [x] 3.4 Store tunnel ID and token for outputs

### 4. Tunnel Config Resource Creation
- [x] 4.1 Create `cloudflare_tunnel_config` resource for each tunnel
- [x] 4.2 Generate ingress rules from services configuration
- [x] 4.3 Map public_hostname to hostname in ingress rules
- [x] 4.4 Map local_service_url to service in ingress rules
- [x] 4.5 Set no_tls_verify option on ingress rules when true
- [x] 4.6 Add catch-all rule returning 404 as final ingress rule

### 5. DNS Record Resource Creation
- [x] 5.1 Create `cloudflare_record` CNAME resources for each service public_hostname
- [x] 5.2 Set CNAME target to `${tunnel_id}.cfargotunnel.com`
- [x] 5.3 Set record type to "CNAME" and proxied to true
- [x] 5.4 Use zone_id from data source for all records

### 6. Output Definitions
- [x] 6.1 Define `tunnel_ids` output - map of MAC address to tunnel ID
- [x] 6.2 Define `tunnel_tokens` output - map of MAC address to tunnel token (sensitive = true)
- [x] 6.3 Define `credentials_json` output - map of MAC to credentials file content (sensitive = true)
- [x] 6.4 Define `public_hostnames` output - list of all created public hostnames
- [x] 6.5 Define `zone_id` output - the Cloudflare zone ID used
- [x] 6.6 Add descriptive output descriptions

### 7. Error Handling & Edge Cases
- [x] 7.1 Handle missing zone gracefully with clear error message
- [x] 7.2 Validate local_service_url uses internal domains only
- [x] 7.3 Handle empty services list (tunnel with no ingress rules except catch-all)
- [x] 7.4 Ensure tunnel tokens are marked sensitive
- [x] 7.5 Handle duplicate MAC addresses in configuration

### 8. Documentation
- [x] 8.1 Update README.md with module purpose and usage
- [x] 8.2 Document all input variables with types and defaults
- [x] 8.3 Document all outputs with descriptions and sensitivity
- [x] 8.4 Add example usage in README
- [x] 8.5 Document provider authentication requirements
- [x] 8.6 Document security considerations (token sensitivity)

### 9. Testing & Validation
- [x] 9.1 Run `terraform validate` successfully
- [x] 9.2 Run `terraform fmt` to ensure formatting
- [x] 9.3 Verify module uses correct provider resources
- [x] 9.4 Verify DNS loop validation works correctly
- [x] 9.5 Verify tunnel tokens are marked sensitive
