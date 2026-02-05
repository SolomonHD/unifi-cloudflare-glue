## Context

Users currently lack practical examples showing appropriate deployment patterns for different environments. Existing examples don't differentiate between development (fast iteration), staging (team collaboration), and production (security/compliance). This leads to users either over-engineering simple dev setups or under-securing production deployments.

The project already has state management capabilities (ephemeral, persistent local, remote backends) and vals integration for secret injection. This change leverages these existing capabilities by creating environment-specific examples demonstrating when and how to use each approach.

## Goals / Non-Goals

**Goals:**
- Provide three complete, copy-paste-ready environment examples matching real-world usage patterns
- Demonstrate appropriate state management strategy for each environment (ephemeral → S3 lockfile → S3 + DynamoDB/vals)
- Show security progression from simple (env vars) to production-grade (vals/1Password)
- Create comprehensive documentation explaining tradeoffs and when to use each pattern
- Ensure examples highlight cost implications for informed decision-making

**Non-Goals:**
- CI/CD pipeline configuration (separate future work)
- Multi-region deployment patterns
- Kubernetes or container orchestration examples
- Monitoring/observability setup
- Automated secret rotation implementation

## Decisions

### Decision 1: Three distinct examples instead of parameterized template

**Choice:** Create three separate example directories rather than one parameterized example

**Rationale:**
- Users want to copy-paste without needing to understand parameter systems
- Different environments have fundamentally different file structures (dev has scripts, staging has Makefile, production adds SECRETS.md)
- Clearer to show the "ideal" for each environment rather than conditional templating
- Easier to maintain and test each independently

**Alternatives considered:**
- Single parameterized example with environment flag → Rejected: Too complex for copy-paste, obscures actual differences
- Two examples (dev + production) → Rejected: Staging is common enough to warrant its own example

### Decision 2: Dev environment uses ephemeral state (no backend)

**Choice:** Development example has no backend configuration, state lives only in container

**Rationale:**
- Fastest iteration: No backend setup required
- Safe experimentation: No risk of corrupting shared state
- Zero cost: No S3/DynamoDB resources needed
- Clean slate: Every run starts fresh

**Alternatives considered:**
- Local state file → Rejected: Adds filesystem management complexity, not needed for dev iteration
- Remote state → Rejected: Over-engineering for solo dev work, adds latency and cost

### Decision 3: Staging uses S3 with lockfile (no DynamoDB)

**Choice:** Staging backend uses S3 with lockfile for locking, not DynamoDB

**Rationale:**
- Cost-effective: Single S3 bucket instead of S3 + DynamoDB table
- Sufficient for teams: Lockfile provides adequate coordination for pre-production
- Lower complexity: One fewer resource to manage
- Good middle ground between dev and production

**Alternatives considered:**
- No locking → Rejected: Team collaboration requires coordination
- DynamoDB locking → Rejected: Over-engineered for non-critical staging environment, adds cost

### Decision 4: Production uses vals for secret injection

**Choice:** Production example demonstrates vals with 1Password integration

**Rationale:**
- Production-ready: Secrets never touch disk in plaintext
- Existing integration: Project already has vals documentation and patterns
- Industry standard: 1Password is widely adopted
- Automatic cleanup: Makefile removes rendered secrets after operations

**Alternatives considered:**
- Environment variables → Rejected: Not secure enough for production (secrets in process environment, shell history)
- Terraform Cloud variables → Rejected: Vendor lock-in, not all users use Terraform Cloud
- AWS Secrets Manager → Rejected: Assumes AWS, we want cloud-agnostic patterns

### Decision 5: Each example has complete KCL configuration

**Choice:** Each environment directory includes its own `kcl/main.k` rather than referencing shared config

**Rationale:**
- Self-contained: Users can copy single directory and run it
- Examples can show environment-appropriate patterns (dev uses test domains, production uses real domains)
- No path dependencies that break when copied elsewhere

**Alternatives considered:**
- Shared KCL in examples/ root → Rejected: Breaks copy-paste workflow, adds coupling

### Decision 6: Deployment scripts match environment complexity

**Choice:** Dev uses bash scripts, staging/production use Makefiles

**Rationale:**
- Dev: Simple bash scripts for quick runs (`./deploy.sh`, `./destroy.sh`)
- Staging/Production: Makefiles for complex workflows (secret rendering, cleanup, multiple targets)
- Progressive complexity matches environment needs

**Alternatives considered:**
- Makefiles for all → Rejected: Over-complicated for simple dev workflow
- Scripts for all → Rejected: Production secret cleanup requires build tool features

## Risks / Trade-offs

### Risk: Examples become outdated as project evolves
**Mitigation:** Include examples in documentation review process, add note at top of each README pointing to latest version

### Risk: Users might use dev pattern in production
**Mitigation:** Clear warnings in dev README, comparison table shows why this is inappropriate, docs explain security implications

### Risk: 1Password example may not match user's secret manager
**Mitigation:** Document 1Password as example, include comment in files showing how to adapt for Vault/AWS Secrets Manager

### Risk: S3 backend examples assume AWS
**Mitigation:** Comment in staging/production backend configs mentioning GCS/Azure alternatives, link to backend docs

### Trade-off: Three separate examples means more maintenance
**Accepted:** Copy-paste usability outweighs maintenance cost, examples are relatively static

### Trade-off: Complete KCL in each example leads to duplication
**Accepted:** Self-contained examples more valuable than DRY principle for example code

## Migration Plan

Not applicable - this is additive documentation and examples, no migration needed.

## Open Questions

None - all approaches are well-established patterns in the project's existing documentation.
