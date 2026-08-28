## Context

`portainer-docker-compose` currently consumes commit `44cb3a25` from `fix-cloudflare-token` through both Dagger and KCL. That branch is a fast-forward descendant of this repository's `main` and contains the Network 10.x workaround that creates/adopts persistent UniFi clients before reading their current IP. A production Dagger plan against controller `192.168.60.1` proved that the branch's selected `filipowm/unifi` v1.0.0 authenticates with `UNIFI_API_KEY` and produces 0 add, 0 change, and 0 destroy.

The provider's v1.1.0 release does not claim an API-key authentication fix. This change therefore establishes a trustworthy same-provider baseline, not a remediation for a reproduced auth defect. Live execution is blocked until `harden-dagger-secret-and-state-handling` is complete and exposed credentials have been addressed.

## Goals / Non-Goals

**Goals:**

- Preserve the proven Network 10.x client-registration behavior on `main`.
- Select `filipowm/unifi` v1.1.x deterministically and verify no state or infrastructure churn.
- Record API-key auth as the tested primary path and username/password as compatibility only.
- Exercise provider DNS CRUD at production-like cardinality in an isolated `solomonhd.ai` namespace.
- Replace downstream feature-branch pins with the reviewed normalized revision.

**Non-Goals:**

- Migrate resource ownership or state to `ubiquiti-community/unifi`.
- Destroy, recreate, or apply changes to production `sghd.io` DNS records.
- Reuse production-managed MAC addresses in a second Terraform state.
- Add unattended GitHub Actions or Cloudflare live CI.

## Decisions

### 1. Treat the branch as a behavioral patch set, not as an auth branch

Implementation will review and preserve the branch's five commits, especially the `unifi_user` resource followed by the dependent `data.unifi_user` lookup. Tests and documentation will identify this as an `UnknownUser`/unremembered-client workaround independent of API-key authentication.

Alternative considered: discard the branch because the production plan currently succeeds. Rejected because success depends on behavior that has not reached `main`.

### 2. Constrain the current provider to v1.1.x

The module constraint becomes `~> 1.1.0`, and a reproducible initialization check verifies selection of v1.1.0 or a reviewed patch successor. The upgrade is described as maintenance because neither the baseline failure nor upstream release notes identify an auth fix.

Alternative considered: leave `~> 1.0`, which can float across all 1.x releases during ephemeral Dagger initialization. Rejected because it does not document the reviewed baseline.

### 3. Separate safe DNS CRUD from client lookup validation

A dedicated Terraform test fixture creates a production-scale mix of A and CNAME records below a unique `unifi-poc-<run>.solomonhd.ai` namespace using benign private-address targets. It does not use the production KCL file or production client MACs. The existing production plan proves client read/refresh behavior; an optional operator-designated sacrificial MAC can exercise create/adopt behavior without overlapping production state ownership.

Alternative considered: clone the entire production KCL with only the domain replaced. Rejected because the cloned state would also manage the same UniFi client MACs and could rename or modify production clients.

### 4. Require lifecycle-complete baseline evidence

The disposable fixture runs create, read/zero-drift plan, one benign update, destroy, and API absence verification. Cleanup is mandatory and uses the hardened integration lifecycle. Production is verified separately by read-only plan before and after the provider update.

### 5. Normalize consumers only after the repository revision is published

After the normalized change is merged and tagged or committed on `main`, the Portainer consumer updates both `dagger.json` and `kcl/kcl.mod` to the identical reviewed revision and corrects its credential-rotation note. A tag is preferred for reproducibility; an immutable `main` commit is acceptable.

## Risks / Trade-offs

- [Branch integration includes poorly described historical commits] → Review the full diff and retain only behavior covered by tests.
- [Provider v1.1 introduces unrelated changes] → Compare provider schema/lock output and require identical production plan results before and after.
- [Sandbox names leak into local DNS temporarily] → Use a unique prefix, bounded timeout, cleanup ledger, and post-destroy API verification.
- [Test fixture does not exercise every production client lookup] → Pair fixture CRUD evidence with the exact production read-only plan.
- [Downstream pins can diverge] → Update Dagger and KCL pins atomically to the same tag or commit.

## Migration Plan

1. Complete the secret/state hardening change and its credential prerequisites.
2. Integrate and test the `fix-cloudflare-token` patch set on a feature branch.
3. Capture a zero-drift production plan with the v1.0.0 baseline.
4. Update the constraint to v1.1.x and run offline/schema tests.
5. Run the disposable `solomonhd.ai` lifecycle test with the current provider.
6. Re-run the production plan and require 0 add, 0 change, and 0 destroy.
7. Merge and publish the normalized `main` revision.
8. Atomically update both downstream pins and correct the Portainer audit/OpenSpec note.

Rollback repins the consumer to the previous immutable commit and provider selection. It does not destroy production resources.

## Open Questions

- Choose a dedicated sacrificial client MAC only if client create/adopt testing is required beyond the proven production refresh.
- Decide at release time whether the downstream consumer should use a semantic tag or an immutable `main` commit.
