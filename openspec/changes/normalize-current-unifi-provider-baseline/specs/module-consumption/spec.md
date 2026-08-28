## ADDED Requirements

### Requirement: Production consumers use reviewed immutable revisions
Production Dagger and KCL consumers MUST reference a reviewed release tag or immutable commit reachable from `main` rather than a long-lived feature branch.

#### Scenario: Normalized provider baseline is published
- **WHEN** a consumer updates to the normalized repository revision
- **THEN** its Dagger and KCL dependency declarations MUST reference the same tag or commit
- **AND** neither declaration may continue to reference `fix-cloudflare-token`

### Requirement: Consumer coordination preserves atomicity
Downstream dependency and documentation updates MUST be coordinated so callers cannot resolve different module revisions for Dagger and KCL.

#### Scenario: Portainer consumer pin is changed
- **WHEN** `dagger.json` is updated to the normalized revision
- **THEN** `kcl/kcl.mod` MUST be updated in the same consumer commit
- **AND** the credential-rotation note MUST be corrected to state that the glue path uses API-key authentication
