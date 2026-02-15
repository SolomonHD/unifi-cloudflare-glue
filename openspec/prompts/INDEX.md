# OpenSpec Prompt Index: Fix Deploy and Destroy Functions

## Overview

The `deploy` and `destroy` Dagger functions are missing critical features that the `plan` function has implemented correctly. This index tracks the prompts needed to bring them into alignment.

## Current Issues

1. **Missing Cache Busting**: `deploy` and `destroy` lack `no_cache` and `cache_buster` parameters
2. **No CACHE_BUSTER Environment Variable**: Cache busting doesn't work without setting this env var
3. **Container Reference Loss**: Functions don't preserve container references after execution like `plan` does
4. **Fragile Working Directory Logic**: Uses string checks instead of proper state directory handling

## Reference Implementation

The `plan` function (lines 983-1383) is the correct reference. Key patterns to replicate:
- Lines 1001-1002: Parameter definitions for `no_cache` and `cache_buster`
- Lines 1091-1098: Cache buster validation and epoch timestamp generation
- Lines 1178-1179, 1272-1273: Setting CACHE_BUSTER environment variable
- Lines 1198-1207: Preserving container references after execution
- Lines 1181-1187: Proper state directory working directory setup

## Prompts

| # | ID | Description | Status |
|---|-----|-------------|--------|
| 01 | add-cache-busting-to-deploy-destroy | Add no_cache/cache_buster parameters and CACHE_BUSTER env var support | Pending |
| 02 | fix-container-references-and-workdir | Fix container reference preservation and working directory logic | Pending |

## Dependencies

- Prompt 02 depends on Prompt 01 (needs cache_buster variables to exist)

## Files to Modify

- `src/main/main.py`: Contains all Dagger functions
  - `deploy()` function (line ~746)
  - `destroy()` function (line ~1385)
  - `deploy_unifi()` function (line ~356)
  - `deploy_cloudflare()` function (line ~542)
