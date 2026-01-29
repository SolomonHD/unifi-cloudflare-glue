## MODIFIED Requirements

### Requirement: Terraform Cloudflare Tunnel Module - Zone Data Source (v5.x)

The Terraform module SHALL query the existing Cloudflare Zone using the v5.x data source schema with filter block.

#### Scenario: Query Cloudflare Zone by name using filter block
Given a zone_name from the configuration
When the `cloudflare_zone` data source is configured with a filter block
Then it SHALL use the syntax:
  ```
  data "cloudflare_zone" "this" {
    filter {
      name = local.effective_config.zone_name
    }
  }
  ```
And it SHALL NOT use the deprecated direct name attribute

#### Scenario: Zone data source returns zone_id
Given a successful zone data source query with filter block
When the data source is evaluated
Then it SHALL return the zone details including zone_id
And the zone_id SHALL be accessible via `data.cloudflare_zone.this.id`

#### Scenario: Fail when zone does not exist
Given a zone_name that does not exist in Cloudflare
When the data source queries Cloudflare
Then Terraform SHALL fail with a clear error message indicating the zone was not found

#### Scenario: Backward compatibility for zone_id references
Given resources that reference the zone data source
When they use `data.cloudflare_zone.this.id`
Then they SHALL continue to work without modification
