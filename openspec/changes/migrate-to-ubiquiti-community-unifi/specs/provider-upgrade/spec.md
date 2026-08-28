## ADDED Requirements

### Requirement: Provider source migrations require schema mapping
A Terraform provider source-address migration MUST document every managed resource/data-source rename, required attribute rename/type change, import identifier, and computed-value dependency before state changes begin.

#### Scenario: UniFi provider source changes
- **WHEN** `filipowm/unifi` is replaced by `ubiquiti-community/unifi`
- **THEN** the mapping MUST cover clients, client IP lookup, A/CNAME DNS records, TTL representation, authentication, and outputs
- **AND** automated tests MUST exercise each mapped behavior

### Requirement: Provider address replacement is not assumed compatible
The migration MUST NOT use `terraform state replace-provider` as the complete migration when provider state schemas or resource types differ.

#### Scenario: Source providers expose incompatible schemas
- **WHEN** the old and new providers use different client resource types or DNS attributes
- **THEN** resources MUST be removed and imported through supported target-provider identities
- **AND** zero drift MUST be demonstrated before apply
