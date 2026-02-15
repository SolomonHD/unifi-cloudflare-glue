## 1. Update deploy_unifi() Function

- [x] 1.1 Add `no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False` parameter to function signature
- [x] 1.2 Add `cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = ""` parameter to function signature
- [x] 1.3 Add validation logic: raise ValueError if both `no_cache` and `cache_buster` are provided
- [x] 1.4 Calculate `effective_cache_buster` value (epoch timestamp if `no_cache=True`, else `cache_buster`)
- [x] 1.5 Set `CACHE_BUSTER` environment variable on Terraform container after setup but before execution
- [x] 1.6 Update function docstring with parameter documentation and usage examples

## 2. Update deploy_cloudflare() Function

- [x] 2.1 Add `no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False` parameter to function signature
- [x] 2.2 Add `cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = ""` parameter to function signature
- [x] 2.3 Add validation logic: raise ValueError if both `no_cache` and `cache_buster` are provided
- [x] 2.4 Calculate `effective_cache_buster` value (epoch timestamp if `no_cache=True`, else `cache_buster`)
- [x] 2.5 Set `CACHE_BUSTER` environment variable on Terraform container after setup but before execution
- [x] 2.6 Update function docstring with parameter documentation and usage examples

## 3. Update deploy() Function

- [x] 3.1 Add `no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False` parameter to function signature
- [x] 3.2 Add `cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = ""` parameter to function signature
- [x] 3.3 Add validation logic: raise ValueError if both `no_cache` and `cache_buster` are provided
- [x] 3.4 Calculate `effective_cache_buster` value (epoch timestamp if `no_cache=True`, else `cache_buster`)
- [x] 3.5 Pass `effective_cache_buster` to `deploy_unifi()` and `deploy_cloudflare()` calls
- [x] 3.6 Update function docstring with parameter documentation and usage examples

## 4. Update destroy() Function

- [x] 4.1 Add `no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False` parameter to function signature
- [x] 4.2 Add `cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = ""` parameter to function signature
- [x] 4.3 Add validation logic: raise ValueError if both `no_cache` and `cache_buster` are provided
- [x] 4.4 Calculate `effective_cache_buster` value (epoch timestamp if `no_cache=True`, else `cache_buster`)
- [x] 4.5 Set `CACHE_BUSTER` environment variable on Cloudflare container before execution
- [x] 4.6 Set `CACHE_BUSTER` environment variable on UniFi container before execution
- [x] 4.7 Update function docstring with parameter documentation and usage examples

## 5. Validation and Testing

- [x] 5.1 Verify `dagger functions` shows new parameters for all four functions
- [x] 5.2 Test `dagger call deploy --no-cache` executes without error
- [x] 5.3 Test `dagger call destroy --cache-buster=test-key` executes without error
- [x] 5.4 Test that using both flags raises appropriate error message
- [x] 5.5 Verify backward compatibility: calling functions without new parameters works as before
