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

### Requirement: Exact provider behavior is qualified before handoff
The UniFi migration MUST qualify exactly `ubiquiti-community/unifi` 0.65.0, including import/read effects, site resolution, TTL zero/null semantics, and active/offline client IP behavior before production handoff.

#### Scenario: Missing client or incorrect site is encountered
- **WHEN** preflight cannot prove an existing object in the intended controller/site or qualification shows Read can call `CreateClient`
- **THEN** execution MUST treat import/refresh as potentially mutating and stop unsafe production discovery
- **AND** tests MUST cover missing-client and wrong-site behavior without deliberate production negative tests

#### Scenario: Provider defaults or offline behavior differ
- **WHEN** TTL zero/default maps to null/omission or offline `last_ip` is null, stale, or different
- **THEN** the mapping MUST be version-qualified and tested
- **AND** unexplained production differences MUST block handoff rather than be accepted by apply
