## Context

The hardening implementation passes its focused secret, lifecycle, type/compile, KCL, and Terraform checks, but the repository-wide unit run includes older suites written for contracts that later changes removed or split. In particular, deployment-guidance tests instantiate a deleted `deploy_cloudflare()` path, while generator-output tests mix the standalone generator `result` contract with a consumer `main.k` contract that exports `unifi_output` and `cf_output`.

Three queued changes will still alter provider fixtures and add a live-canary boundary. This cleanup therefore must run last and validate the resulting public surface rather than freeze today's intermediate implementation.

## Goals / Non-Goals

**Goals:**

- Restore one green, authoritative offline verification baseline after all queued changes land.
- Make tests describe supported public Dagger and KCL contracts.
- Retain the hardening regression coverage and keep offline verification credential-free.
- Remove stale exclusions and finish repository-wide Python formatting.

**Non-Goals:**

- Restore deleted standalone deployment functions solely to satisfy old tests.
- Change infrastructure, provider state, production credentials, or live-test policy.
- Run ahead of the provider and canary changes or constrain their fixture design.

## Decisions

### 1. Enforce an explicit queue gate

Implementation begins only after the provider baseline, provider migration, and live Cloudflare canary changes are complete. This avoids repairing mocks twice and makes the final test baseline reflect the long-term provider surface.

Alternative considered: repair every failing test immediately. Rejected because several failures exercise APIs or schemas intentionally changed by queued work.

### 2. Test supported behavior instead of preserving historical entry points

Deployment-guidance coverage moves to the combined `deploy()` function and its component-selection flags. Tests for removed standalone functions are deleted or rewritten; production code does not gain compatibility wrappers merely for the suite.

Generator tests separate two contracts: standalone generator modules expose their sample output as `result`, while Dagger generation consumes purpose-built KCL fixtures exporting the documented consumer keys. Tests do not run the repository library `main.k` as though it were a consumer configuration.

### 3. Establish one complete offline verification baseline

The change records and runs a single documented command sequence covering formatting, type/compile checks, the full unit suite, and KCL schema/generator checks. Hardening sentinel and failure-injection tests remain included. Live infrastructure tests stay separately authorized and are not required for the offline baseline.

## Risks / Trade-offs

- [Queued changes introduce a different final API] → Start only after all prerequisite changes are complete and derive fixtures from their published contracts.
- [Deleting obsolete tests reduces accidental coverage] → Map each removed test to a supported behavior test or explicitly document why the behavior no longer exists.
- [A green suite masks skipped legacy tests] → Inventory skips, xfails, and marker exclusions and permit only documented live-integration boundaries.
- [Formatting creates a broad diff] → Isolate mechanical formatting from behavioral test rewrites where practical and verify with `git diff --check`.

## Migration Plan

1. Confirm the three queued prerequisite changes are complete and archived.
2. Capture the full failing-test and formatting inventory without credentials.
3. Reconcile main requirements, fixtures, mocks, and tests with the final supported APIs.
4. Run the complete offline baseline and strict OpenSpec validation.
5. Publish the repaired baseline without performing any infrastructure mutation.

Rollback reverts only test, formatting, and specification commits; no provider state or managed resource rollback is involved.

## Open Questions

- Choose the final single-command wrapper or task-runner target after the queued changes establish their verification commands.
