## Context

The project currently has two separate Terraform modules: `unifi-dns` and `cloudflare-tunnel`. When using the `deploy()` function with persistent local state (`--state-dir`), both deployments share the same state file, causing provider conflicts. Each module tries to initialize both providers because Terraform sees resources from both modules in the shared state.

The current workaround requires users to use separate state directories or manually configure providers, which is error-prone and creates a poor user experience.

## Goals / Non-Goals

**Goals:**
- Create a combined Terraform module that wraps both `unifi-dns` and `cloudflare-tunnel`
- Enable atomic deployment from a single Terraform configuration
- Eliminate provider conflicts when using shared state
- Maintain explicit dependency: UniFi DNS completes before Cloudflare Tunnel
- Preserve all existing functionality of individual modules
- Provide clear documentation on when to use combined vs individual modules

**Non-Goals:**
- Modifying the existing `unifi-dns` or `cloudflare-tunnel` modules
- Adding new features to either sub-module
- Changing the Dagger/Python deployment logic (handled in separate prompts)
- Supporting deployment scenarios beyond atomic combined deployment

## Decisions

### Use Root-Level Provider Configuration

**Decision:** Configure both UniFi and Cloudflare providers at the root module level.

**Rationale:** This ensures both providers are initialized once for the entire configuration, avoiding the conflict that occurs when separate modules each try to configure providers.

**Alternatives Considered:**
- Passing provider configurations through module blocks: More complex, still requires root-level provider config
- Keeping providers in sub-modules: Continues to cause conflicts with shared state

### Explicit Dependency Chain

**Decision:** Use `depends_on = [module.unifi_dns]` in the cloudflare_tunnel module call.

**Rationale:** Ensures UniFi DNS records are created before Cloudflare Tunnel attempts to reference them. This is critical because Cloudflare Tunnel services use local hostnames that must already resolve.

**Alternatives Considered:**
- Implicit dependency through output references: More fragile, less explicit
- No dependency: Risk of tunnel creation failing due to unresolvable hostnames

### Support Both Config Patterns

**Decision:** Accept both `config` (object) and `config_file` (path) inputs for both UniFi and Cloudflare.

**Rationale:** Maintains compatibility with existing usage patterns from individual modules. Some users prefer passing objects directly, others prefer file paths.

**Alternatives Considered:**
- Only support config_file: Would break existing object-based usage
- Only support config object: Less flexible for file-based workflows

### Relative Module Paths

**Decision:** Use relative paths (`../unifi-dns/`, `../cloudflare-tunnel/`) for module sources.

**Rationale:** Keeps the module self-contained within the repository. Absolute paths or registry sources would require publishing or fixed directory structures.

**Alternatives Considered:**
- Absolute paths: Not portable across different clone locations
- Git/Terraform Registry sources: Requires separate versioning and publishing

### Passthrough Variable Pattern

**Decision:** Define all variables in the combined module that are needed by sub-modules, then pass them through.

**Rationale:** Explicit variable definition makes the interface clear and enables validation at the combined module level.

**Alternatives Considered:**
- Single `config` object containing everything: Less explicit, harder to document and validate

## Risks / Trade-offs

**Risk:** Module path changes break relative references
→ **Mitigation:** Document that modules must maintain sibling relationship; use Terraform module registry for production if path stability is critical

**Risk:** Combined module becomes too large/complex
→ **Mitigation:** Keep module as thin wrapper; all logic remains in sub-modules

**Risk:** Provider version conflicts between sub-modules
→ **Mitigation:** versions.tf in combined module specifies exact versions expected by both sub-modules

**Risk:** Users confused about when to use combined vs individual modules
→ **Mitigation:** README clearly documents use cases for each approach

**Trade-off:** Combined module requires all provider credentials even if only using one sub-module
→ **Acceptance:** This is the intended use case (atomic deployment); users needing selective deployment should use individual modules

## Migration Plan

No migration needed - this is a new module. Existing users can optionally switch to the combined module:

1. Create new KCL configuration (or reuse existing)
2. Reference the combined module: `source = "terraform/modules/glue"`
3. Pass both UniFi and Cloudflare configurations
4. Run `terraform init` and `terraform apply`
5. (Optional) Remove old separate deployments after verifying combined deployment works

## Open Questions

None - design is straightforward wrapper pattern with well-understood requirements.
