# TerraPulse local judging package

Current source/runtime distribution: 4 November 2026, Asia/Dhaka. The core project version remains 1.0.0. Earlier standalone archives retain their dated scope.

**Cloned from GitHub?** Restore the processed data first with `python3 scripts/fetch_runtime.py` (or `py -3 scripts\fetch_runtime.py` on Windows). This repository and its runtime release are private; authorized users need GitHub CLI authentication. Then follow the environment/server steps below. A source clone does not contain `RELEASE_MANIFEST.json`; use `scripts/fetch_runtime.py --verify` for its data check. The `verify_release.py` command below applies to a complete standalone judging archive.

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

## Three-minute investigation

1. Open Investigations and choose **Show the alert**: inspect the preserved Nepal footprint at the first changed observation.
2. Choose **Show what stayed changed**: the later alert disappears while the measured HH baseline difference remains. Read the limits beside the measurement.
3. Choose **Investigate River Memory**, then explore Wetland Pulse. Select a **Frozen reference** footprint and an observed date to inspect optical comparisons, including gaps and mixed results.
4. Expand competing explanations. Review next evidence and measured Nepal coherence links. Export a dossier.
5. Open **Expanded Nepal record** to play ten visits from June 20 to October 18. Compare with the explicit August 19 reference, then choose native 20 m or 80 m coherence for one of the two supplied pairs. The original Three Movements story stays attached to its original three-date record.

The top navigation preserves supported investigation state. Nepal-only tools are labeled. A requested unloaded date is explicitly unavailable; it is never interpolated. Copy the URL to share the current Investigations case/date/layer/footprint. Saved footprints, point neighborhoods and assessed polygons can be restored. A link to a Nepal-only workspace cannot reproduce a Bangladesh crop.

On the map, arrows move the cursor, Shift+arrow moves farther, Enter inspects or adds a drawing vertex, and Escape cancels drawing. Use the standard **Inspect polygon** button to finish. Story buttons work without automatic scrolling. Scroll-driven changes are opt-in and disabled when reduced motion is requested. The map's selected evidence is also summarized as text.

## Mandatory rehearsal and known limits

Complete [the disconnected runbook](docs/OFFLINE_REHEARSAL.md) and [browser/accessibility checklist](docs/reports/browser_a11y_2026-11-03.md) before treating this as a polished final submission. Automated network-denied handler checks are not proof of a physically disconnected browser rehearsal. Real-browser visual/accessibility/GPU checks are unverified under the recorded browser policy block.

IMERG rainfall remains unavailable for the requested dates; the August pattern remains unresolved. Rules/cutoffs are uncalibrated, optical overlap is descriptive, and event causes remain unverified. The two supplied Nepal GUNW pairs now have header-compatible native coherence crops. Bangladesh coherence is unavailable. LOS displacement remains unresolved; phase downloads are uncorrected radians. Public repository/video access and actual submission remain unverified.
