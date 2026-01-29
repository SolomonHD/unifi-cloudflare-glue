# Design: KCL Generation Container Architecture

## Overview

This document describes the container architecture for the KCL generation functions. The design focuses on using Dagger's container APIs to run KCL in isolated, reproducible environments.

## Container Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Dagger Host                              │
│                                                                  │
│  ┌─────────────────────┐        ┌─────────────────────────────┐ │
│  │   User Source Dir   │───────▶│   KCL Container             │ │
│  │   (KCL configs)     │        │   - kcllang/kcl:latest      │ │
│  │                     │        │   - Mounted at /src         │ │
│  └─────────────────────┘        │   - Working dir: /src       │ │
│                                 │                             │ │
│                                 │  ┌───────────────────────┐  │ │
│                                 │  │ kcl run generators/   │  │ │
│                                 │  │       unifi.k         │  │ │
│                                 │  └───────────────────────┘  │ │
│                                 │            │                │ │
│                                 │            ▼                │ │
│                                 │  ┌───────────────────────┐  │ │
│                                 │  │   JSON Output         │  │ │
│                                 │  │   (stdout capture)    │  │ │
│                                 │  └───────────────────────┘  │ │
│                                 └─────────────────────────────┘ │
│                                            │                     │
│                                            ▼                     │
│                                 ┌───────────────────────┐        │
│                                 │   dagger.File         │        │
│                                 │   (returned to caller)│        │
│                                 └───────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Container Configuration

### Base Image

```python
# Official KCL image with CLI tools
image = f"kcllang/kcl:{kcl_version}"  # e.g., "kcllang/kcl:latest"
```

**Image Details**:
- Repository: `kcllang/kcl` on Docker Hub
- Contains: KCL CLI, standard library, common dependencies
- Tags: `latest`, `v0.x.x`, specific versions

### Directory Structure in Container

```
/src/                          # Mounted user source
├── kcl.mod                    # KCL module manifest
├── kcl.mod.lock              # Dependency lock
├── schemas/                   # Schema definitions
├── generators/               # Generator files
│   ├── unifi.k              # UniFi generator
│   └── cloudflare.k         # Cloudflare generator
└── ...                       # Other KCL files
```

## Implementation Pattern

### Function Implementation

```python
@function
async def generate_unifi_config(
    self,
    source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
) -> dagger.File:
    """Generate UniFi JSON configuration from KCL schemas."""
    
    # Create container with KCL
    ctr = (
        dagger.dag.container()
        .from_(f"kcllang/kcl:{kcl_version}")
        .with_directory("/src", source)
        .with_workdir("/src")
    )
    
    # Run KCL generator
    result = await ctr.with_exec(["kcl", "run", "generators/unifi.k"]).stdout()
    
    # Return as file
    return dagger.dag.directory().with_new_file("unifi.json", result).file("unifi.json")
```

### Alternative: File-based Output

If generators write to files instead of stdout:

```python
# Run generator (writes to file)
ctr = await ctr.with_exec(["kcl", "run", "generators/unifi.k", "-o", "/output/unifi.json"]).sync()

# Return the generated file
return ctr.file("/output/unifi.json")
```

## Caching Strategy

### Container Layer Caching

```python
# Container image is cached by version
ctr = dagger.dag.container().from_(f"kcllang/kcl:{kcl_version}")

# Directory is cached by content hash
ctr = ctr.with_directory("/src", source)
```

**Cache Keys**:
1. `kcllang/kcl:{kcl_version}` - Base image layer
2. `source` directory hash - Source code layer
3. Generator execution - Not cached (always runs fresh)

### Optimization

For repeated runs with same source:
- Base image: Cached after first pull
- Source directory: Cached if unchanged
- Generator: Always executes (deterministic output)

## Error Handling

### Missing kcl.mod

```python
# Check for module manifest
manifest_exists = await source.file("kcl.mod").exists()
if not manifest_exists:
    raise ValueError("✗ No kcl.mod found in source directory. Is this a valid KCL module?")
```

### KCL Execution Errors

```python
try:
    result = await ctr.with_exec(["kcl", "run", "generators/unifi.k"]).stdout()
except dagger.ExecError as e:
    return f"✗ KCL execution failed:\n{e.stderr}"
```

### Generator File Not Found

```python
# Check generator exists
gen_exists = await source.file("generators/unifi.k").exists()
if not gen_exists:
    return "✗ Generator file not found: generators/unifi.k"
```

## Security Considerations

### No Secret Exposure

- No secrets required for public KCL modules
- Source directory is mounted read-only (implicit)
- No network access required (pure generation)

### Container Isolation

- Each function runs in isolated container
- No persistent state between calls
- Source directory is the only input

## Performance Characteristics

### Cold Start (First Run)

1. Pull KCL image: ~10-30s (depends on network)
2. Mount source directory: ~1s (local)
3. Run generator: ~2-5s

**Total**: ~15-35s

### Warm Start (Cached)

1. Use cached image: ~0s
2. Mount source (if changed): ~1s
3. Run generator: ~2-5s

**Total**: ~3-6s

### Optimization Tips

- Pin `kcl_version` to specific version for reproducibility
- Use `latest` for development, specific version for CI/CD
- Consider warming cache in CI with `dagger call` in setup step

## Comparison: Stdout vs File Output

| Approach | Pros | Cons |
|----------|------|------|
| **Stdout** | Simple, no temp files | Must capture and create file |
| **File** | Direct file return | Generator must support `-o` flag |

**Decision**: Use stdout approach since KCL `run` outputs to stdout by default.

## Future Extensions

### Parallel Generation

```python
# Generate both in parallel
unifi_future = self.generate_unifi_config(source, kcl_version)
cloudflare_future = self.generate_cloudflare_config(source, kcl_version)

unifi_file, cloudflare_file = await asyncio.gather(unifi_future, cloudflare_future)
```

### Custom KCL Modules

If private Git repos are needed:

```python
# Mount SSH key for private repos
ctr = ctr.with_mounted_secret("/root/.ssh/id_rsa", ssh_key)
ctr = ctr.with_exec(["git", "config", "--global", "url.ssh://git@github.com/.insteadOf", "https://github.com/"])
```

### Validation Step

```python
# Validate JSON before returning
try:
    json.loads(result)
except json.JSONDecodeError as e:
    return f"✗ Invalid JSON output: {e}"
```
