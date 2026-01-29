# Tasks: Update cloudflare_zone Data Source

## Analysis
- [x] Review current cloudflare_zone data source usage
- [x] Identify v5.x schema requirements
- [x] Confirm no changes needed to output consumers

## Implementation
- [x] Update data source to use filter block syntax
- [x] Verify references to data.cloudflare_zone.this.id still work
- [x] Run terraform fmt to ensure proper formatting

## Validation
- [x] Run terraform validate
- [x] Confirm no breaking changes to outputs

## Documentation
- [x] Update AGENTS.md if needed
