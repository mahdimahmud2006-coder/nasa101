# TerraPulse local judging package

The processed runtime release is dated 4 November 2026. For a checkout of the current source, the [standalone Atlas](README.md#offline-atlas-for-judges) is the quickest way to open the project.

**Cloned from GitHub?** Restore the processed data first with `python3 scripts/fetch_runtime.py` (or `py -3 scripts\fetch_runtime.py` on Windows). See the [public runtime download and setup instructions](docs/REPOSITORY_AND_RUNTIME.md#runtime-installation) for direct downloads and the additional inputs required by the current source. After creating the environment and installing dependencies, run `make check-ready` on Linux or macOS or `python -m src.api.readiness` with the virtual environment active on Windows. Use `scripts/fetch_runtime.py --verify` to check the release data. The `verify_release.py` command below applies to the complete local judging archive.

## Start on Linux or macOS

Extract the complete archive into one folder. With Python 3.12 or newer installed:

```bash
cd /path/to/extracted/terrapulse
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/verify_release.py
chmod +x run.sh
./run.sh
```

Open `http://127.0.0.1:8000/`. Keep the terminal running. Stop with Ctrl+C. Dependency installation needs internet once; the saved application does not need internet or Earthdata credentials to run.

## Start on Windows

```powershell
cd C:\path\to\extracted\terrapulse
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\verify_release.py
$env:OFFLINE="1"
.venv\Scripts\python.exe -m src.api.app
```

These are source-based startup instructions; clean-machine Windows/macOS runs remain unverified. Test the actual judging computer before presentation.

## Requirements and package scope

Use a current desktop browser. A practical starting target is 8 GB RAM and an ordinary integrated GPU using the 2D view; 16 GB RAM is preferable for rebuilding scientific products. These are planning estimates, not hardware benchmarks. Allow room for the extracted assets, archive, Python environment and temporary work; the public asset tree is larger after the Nepal extension; use the package manifest and allow at least 8 GB free for core runtime download/cache and setup. Full native exports require roughly 20 GB free while cached archives and installed data coexist. An SSD is recommended. WebGL is optional because the terrain renderer has a 2D fallback; real-browser/GPU verification remains pending.

The archive contains current local web assets, canonical radar rasters needed by neighborhood/polygon inspection, context and reference bundles, rules, claims, source, tests and the small flood runtime component cube. Raw HDF5 granules, source caches, credentials and full reprocessing inputs are excluded. `scripts/verify_release.py` checks all packaged file hashes. Full `make verify` requires the separately retained source datasets and phase reports in the development repository; it is not the portable package's self-test.

For the current Atlas editions, see [the judging quickstart](docs/ATLAS_JUDGING_QUICKSTART.md) and [runtime distribution](docs/REPOSITORY_AND_RUNTIME.md). The existing runtime archives are dated, and the latest local edition requires the processed supplements listed there.
