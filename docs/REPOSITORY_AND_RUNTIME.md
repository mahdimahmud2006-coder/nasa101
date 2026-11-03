# Source repository and runtime distribution

The Git repository contains source, configuration, tests, selected documentation visuals, scientific manifests and provenance. Acquired HDF5 products, generated raster/image payloads, environments, credentials, temporary output and release archives stay outside the current Git tree.

Earlier commits contain historical generated files. They remain in history to preserve the project record; no force-push or destructive history rewrite is required. A shallow clone avoids retrieving that older history. Removing generated files from the index does not remove local project files.

## Runtime installation

```bash
python3 scripts/fetch_runtime.py
python3 scripts/fetch_runtime.py --verify
```

The core profile restores maps, playback, canonical intensity rasters for probing, Nepal coherence and the scenario component cube. `--full` additionally restores full-resolution dual-polarization export rasters. Files are content-deduplicated across size-bounded ZIP parts; `config.runtime-assets.json` records each destination, SHA-256, byte count and release asset checksum.

Downloadable assets come from the `runtime-20261104` release in this repository. The repository and release are private; authorized users need GitHub access and `gh auth login`. No Earthdata credentials are included. Source inspection does not require downloading runtime files.

The installer validates archive names, paths, object sizes and hashes. It rejects traversal and code/config destinations and refuses to overwrite conflicting local files. Download caches live in ignored `runtime-downloads/`. The large runtime assets are locally processed products, not the source HDF5 archive. Raw-source reprocessing requires separately retained datasets.

## Checks before publishing

```bash
python3 scripts/audit_repository.py --staged
python3 scripts/audit_repository.py
python -m pytest tests/test_repository_hygiene.py -q
```

The checks cover known credential patterns, oversized files, acquired/runtime binaries, ignore exceptions, and safe restoration. Credential contents are never printed. This is scoped automated checking, not a guarantee that every possible secret format is detectable. Secret exclusions come after metadata exceptions so a JSON allowlist cannot accidentally admit credential files.

`.gitattributes` normalizes source line endings and marks image/archive data as binary. Existing scientific files are not reformatted. Do not use `git add -f` to bypass data or secret exclusions.

## Updating runtime data

Use a new release identifier, build with `scripts/package_runtime_assets.py`, verify the local bundle and installer behavior, and upload its versioned assets. Preserve earlier scientific product versions and releases. The runtime manifest and source must be published together. `scripts/package_release.py` remains available for complete local judging archives; older archives predate later source/UI changes.
