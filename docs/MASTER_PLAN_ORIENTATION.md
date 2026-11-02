# TerraPulse master-plan orientation — Phase 0

**Date:** 2 November 2026, Asia/Dhaka. **Scope:** Phase 0 only. No Phase 1–7 implementation or acquisition search has started. The user explicitly requested a phase boundary and a report before continuing.

## Result and evidence

| Report claim ID | Status tag | Verified statement | Evidence / limitation |
|---|---|---|---|
| P0-VERIFY | measured | `make verify` exits successfully: 189 Python tests, 37 JavaScript tests, six analytical validators, runtime preflight and static page checks | [Full log](../reports/phase0_2026_11_02/make_verify.log). Controller tests are mocks, not browser QA. |
| P0-PRESERVE | measured | All 782 pre-existing files in the analytical/viewer/report/release/media preservation inventory retain their original bytes, including all 508 historical analytical artifacts | [Preservation record](../reports/phase0_2026_11_02/verification_preservation.json). This includes preserving historical generated-report bytes as explained below. |
| P0-FREEZE | implemented | An immutable SHA-256 output manifest and a reusable freeze/check utility are supplied | [Baseline](../reports/baseline_2026_11_02.sha256), [scope](../reports/baseline_2026_11_02.scope.json), `scripts/freeze_baseline.py`. The scope lists additional top-level docs JSON and Phase 0 evidence captured at final freeze. |
| P0-SOURCES | measured | Four configured cases use nine unique source granules in two separate series: three Nepal acquisitions and six Bangladesh acquisitions | [Raw-file inventory](../reports/phase0_2026_11_02/granule_covariance_inventory.json), [case inventory](../reports/phase0_2026_11_02/case_inventory.json). Raw HDF5 files were opened read-only. |
| P0-COVARIANCE | measured | All nine active inputs contain only HHHH and HVHV in frequency A and B, each stored as float32 diagonal intensity; no off-diagonal covariance terms were found | Raw-file inventory records the actual dataset paths, shapes, dtypes, and listed-versus-present comparison. This finding applies to the active inputs, not every other local raw file. |
| P0-NEXT | planned | Phase 1 will add an independently sourced slot-calendar sidecar and archive candidate search | Not implemented here. Nominal repeat slots and the reported instrument gap require official archive/notice checks in that phase. |

These IDs identify this Phase 0 report's claims. They are **not** the Phase 4 Claim Ledger or its generator; those remain planned. No new physical-cause hypothesis is introduced in this phase.

### Verification report preservation

The existing `make verify` pipeline regenerates reports and figures. In the first Phase 0 verification run it changed only `docs/reports/implementation_04_05_qa.json`, which includes a hardware-dependent cached-request timing. The fresh generated version is retained under `reports/phase0_2026_11_02/validator_generated/`; the historical file was restored byte-for-byte. The full current verification output remains in the new log. The final repeated `make verify` also passed and changed none of the 782 pre-existing output files. [Verification history](../reports/phase0_2026_11_02/verification_history.json) distinguishes the two runs. No failing result was suppressed or relabeled.

Future phase checks must use new report paths or preserve historical report bytes in the same way. A plain `make verify` can otherwise change a frozen timing-report hash despite unchanged scientific results. This is an existing validator behavior, not a failure of the science baseline.

## Repository map — implemented components

| Location | Role and important entry points |
|---|---|
| `src/ingest/` | Real HDF5 schema audit (`inspect_h5.py`), metadata (`metadata.py`), compatible-series discovery (`timeseries.py`), native-window extraction (`extract_gcov.py`), separately sourced environmental/thermal/reference acquisition code |
| `src/compute/` | Original pair pipeline; fixed-zone time series; context; flood/landslide/DNA; new HH/HV investigation pipeline and probe; six numerical/export validators |
| `src/export/artifacts.py` | JSON, GeoTIFF, preview, region-vector and pixel-geometry output helpers. Canonical COG writer is reused from `timeseries_pipeline.py`. |
| `src/api/app.py` | Standard-library local HTTP server; serves static assets, manifests, probes, and local flood scenarios; no runtime LLM or remote inference |
| `src/api/readiness.py`, `run.sh` | Dependency/asset preflight, loopback startup; uses `.venv/bin/python` when available |
| `config*.json` | Separate project, original pair, time-series, context, flood, DNA, landslide and investigation settings; model thresholds and validity settings remain explicit |
| `data/derived/nepal_case_01/` | Preserved analytical products for implementations 01–07: native/processed rasters, pair outputs, time series, context, thermal, flood, DNA, landslide, Parquet and manifests |
| `web/public/cases/nepal_case_01/` | Original viewer/science assets used by Evidence Studio, comparison, timeline and Change Lab |
| `web/public/cases/{nepal_surface,nepal_impact_corridor,jamuna_river,tanguar_wetland}/investigation/` | New-workspace case manifests, HH/HV COGs, map previews, profiles, and river/wetland response products |
| `web/public/cases/investigations.json` | Four-case readiness registry; two physical acquisition series remain separate |
| `data/context/`, `data/catalogs/`, `database/` and root HDF5s | Retained source data, provenance/query snapshots and user-downloaded raw inputs; source caches are distinct from processed outputs |
| `web/` | Five HTML workspaces, plain JS/MJS modules and local CSS; `playback.mjs` and `terrain-view.mjs` are shared where appropriate |
| `tests/` | Python numerical/ingestion/API tests and Node logic/controller tests, with explicitly labeled synthetic fixtures and DOM/canvas/image/terrain mocks |
| `scripts/` | Static page checks, release packaging/integrity, and the new output-baseline utility |
| `docs/` | Methods, datasets, limitations, AI assistance, submission draft and implementation history |
| `docs/reports/`, `reports/` | Earlier QA outputs and additive Phase 0 evidence respectively |
| `dist/` | Existing portable archive; predates investigation imports and is not rebuilt during Phase 0 |

### Existing routes — implemented

- `/` — Evidence Studio, Nepal radar/environmental context and exploratory scenarios.
- `/comparison.html` — preserved original pair comparison, swipe/scan and nominal masks.
- `/timeseries.html` — preserved Nepal time-series/context viewer.
- `/change-lab.html` — Nepal Change DNA and exploratory hillside context.
- `/investigations.html` — four HH/HV cases, with `?mode=river` or `?mode=wetland` deep links.

Existing API families include `/api/cases`, `/api/investigations`, `/api/cases/{id}/investigation`, `/api/cases/{id}/investigation-probe`, legacy timeline/context/DNA/model routes and zone evidence routes. The raw HDF5 products are not browser runtime inputs.

## Data actually in use — measured

Provider/source for all nine radar inputs: **NASA–ISRO NISAR GCOV, NASA Earthdata / ASF DAAC**, collection `NISAR_L2_GCOV_PROVISIONAL_V1`, DOI `10.5067/NIL2GCOV-P1`. Existing local files only; no new download or external source query was performed for Phase 0.

| Physical series | UTC acquisition start | UTC acquisition end | Product version / release |
|---|---|---|---|
| Nepal 98/16 | 2026-08-19T23:39:18.000000000Z | 2026-08-19T23:39:53.999342105Z | 1.0.11 / P05023 |
| Nepal 98/16 | 2026-08-31T23:39:18.000000000Z | 2026-08-31T23:39:52.999342105Z | 1.0.11 / P05023 |
| Nepal 98/16 | 2026-09-12T23:39:18.000000000Z | 2026-09-12T23:39:52.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-06-18T23:21:35.000000000Z | 2026-06-18T23:22:10.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-07-24T23:21:33.000000000Z | 2026-07-24T23:22:08.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-08-17T23:21:32.000000000Z | 2026-08-17T23:22:06.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-08-29T23:21:32.000000000Z | 2026-08-29T23:22:06.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-09-22T23:21:32.000000000Z | 2026-09-22T23:22:06.999342105Z | 1.0.11 / P05023 |
| Bangladesh 69/14 | 2026-10-16T23:21:32.000000000Z | 2026-10-16T23:22:06.999342105Z | 1.0.11 / P05023 |

All nine are ascending, left-looking, frequency-A HH/HV, 40 MHz acquisitions in the named `4005_DHDH_A` mode. Actual metadata and full granule IDs are retained in the inventory and the exact list below. UTC suffixes in this table make explicit the raw identification fields' UTC meaning.

| Case | Canonical grid | Observed visits | Status |
|---|---|---:|---|
| `nepal_surface` | EPSG:32645, 2400×2400, 10 m; 24×24 km | 3 | measured |
| `nepal_impact_corridor` | EPSG:32645, 2400×2400, 10 m; 24×24 km | 3 | measured |
| `jamuna_river` | EPSG:32646, 2000×2000, 10 m; 20×20 km | 6 | measured |
| `tanguar_wetland` | EPSG:32646, 1600×1800, 10 m; 18×16 km | 6 | measured |

The six files supplied for Jamuna are reused as full scenes for the separate haor crop; no separate haor upload is implied. Two case views of one observation are not two independent acquisitions. Original historical HDF5 discovery contains additional incompatible tracks, frames, polarizations/releases and unsupported inputs; Phase 0 does not merge these into either active series.

### Exact active granule IDs — measured

```text
NISAR_L2_PR_GCOV_023_069_A_014_4005_DHDH_A_20260618T232135_20260618T232210_P05023_N_F_J_001
NISAR_L2_PR_GCOV_026_069_A_014_4005_DHDH_A_20260724T232133_20260724T232208_P05023_N_F_J_001
NISAR_L2_PR_GCOV_028_069_A_014_4005_DHDH_A_20260817T232132_20260817T232206_P05023_N_F_J_001
NISAR_L2_PR_GCOV_029_069_A_014_4005_DHDH_A_20260829T232132_20260829T232206_P05023_N_F_J_001
NISAR_L2_PR_GCOV_031_069_A_014_4005_DHDH_A_20260922T232132_20260922T232206_P05023_N_F_J_001
NISAR_L2_PR_GCOV_033_069_A_014_4005_DHDH_A_20261016T232132_20261016T232206_P05023_N_F_J_001
NISAR_L2_PR_GCOV_028_098_A_016_4005_DHDH_A_20260819T233918_20260819T233953_P05023_N_F_J_001
NISAR_L2_PR_GCOV_029_098_A_016_4005_DHDH_A_20260831T233918_20260831T233952_P05023_N_F_J_001
NISAR_L2_PR_GCOV_030_098_A_016_4005_DHDH_A_20260912T233918_20260912T233952_P05023_N_F_J_001
```

### Covariance decision — measured evidence, planned Phase 2 branch

In **every active input**, the actual `frequencyA` and `frequencyB` grid datasets are `HHHH` and `HVHV`, float32. `listOfCovarianceTerms` agrees with dataset presence. There are no cross-channel off-diagonal covariance terms such as `HHHV` in these active grids. No SSAR group is present. A/B here are L-band subbands, not separate L-/S-band observations.

Consequently Phase 2 should implement explicitly named proxies/composites and mechanism hints from diagonals. Do not label them DpRVI, m–χ, a complete polarimetric decomposition, ground displacement or coherence. The current `HH_dB − HV_dB` view already exists; the proposed CPR is **`HV_dB − HH_dB`**, its sign reversal. Keep both definitions and labels explicit rather than treating them as independent measurements.

## Protected hero result and thresholds — measured

The fixed Nepal zone has 199 native pixels and a 0.0199 km² footprint. Its centered-score successive retained areas are 0.0199 km² then 0, while its signed HH baseline shifts remain approximately −7.5263 and −7.0766 dB. This supports the measured persistence narrative; it does not establish a disaster cause.

Original nominal pair areas remain **0.0195 / 0.7949 / 0.0000 km²** for t1_t2 / t1_t3 / t2_t3. They use a different rule from the centered time-series score, and must not be relabeled as the 0.0199 km² tracked-zone result. The new Bangladesh rule remains HH ≤ −17 dB AND HV ≤ −24 dB, with ≥3 dB paired brightening: all illustrative and uncalibrated.

## Conventions and constraints for subsequent phases

Status for changes below is **planned**; existing components named above are implemented.

1. Keep Python package layout and small plain-JS shared modules. Preserve all five routes and their behavior; do not replace the app with a different frontend.
2. Reuse actual audited HDF5 paths, strict masks, median processing, `canonical_observation`, COG export and existing probe conventions. `read_observation` and `incompatibilities` check physical settings; the investigation path also checks named processing release. Never merge tracks 98/16 and 69/14.
3. Add science data to **new versioned directories or sidecar paths**. Existing rebuild commands replace prior products, so `make process`, `make timeseries`, `make jamuna`, `make wetland` and `make investigations` are not appropriate for extending frozen outputs in place. Reuse their helpers against new destinations instead. UI/code can load additive sidecars without mutating frozen manifests.
4. Existing relevant-source hashes bind some older validators to their producing helpers. Prefer new modules instead of modifying hash-bound science functions or rewriting old provenance to match new code.
5. Use explicit model/schema versions, named units and actual UTC timestamps. Retain no-data, use identical common-valid footprints for traces, and keep display rasters separate from numerical measurement grids.
6. Keep configuration in JSON as currently used. YAML rules/claims are planned for Phase 4; no YAML loader is presently declared in `requirements.txt`. Record any future dependency choice rather than assuming it is installed.
7. Four claim status tags are `implemented`, `measured`, `hypothesized`, `planned`. The project-wide generator/ledger is still planned; retain uncertainty next to any new assertion meanwhile. No runtime LLM or inferred confidence percentages.
8. New datasets must meet the user's non-Chinese-provider/site requirement and carry provider/upstream origin, license, retrieval timestamp, query and checksum. Phase 0 introduces no new dataset. Current raw metadata inspection is not a full-file checksum.
9. Record unavailability only after a real failed/empty source query. No Phase 1 candidate search, gap classification or interferometry availability query has been run here, so none is presented as `unavailable`.
10. Preserve the frozen portable archive. A future rebuilt release must use a new artifact path/version rather than overwrite `dist/terrapulse-1.0.0.zip`.

### Output-baseline operation — implemented

Run from the project root:

```bash
# Verify the newly frozen outputs; never overwrite the baseline.
.venv/bin/python scripts/freeze_baseline.py --check

# Standard independent checksum tool can read the same manifest.
sha256sum --check reports/baseline_2026_11_02.sha256
```

The baseline covers all current files under `data/derived/`, `web/public/`, `docs/reports/`, `dist/`, `reports/`, plus top-level docs JSON and scientific media. It excludes raw sources/source caches, code/configuration, prose, environments, Git metadata and its own manifest/scope sidecar. Phase 0 evidence files present at freeze are included. New files may be added after the freeze; no listed file may change. The `.scope.json` file records the exact count, bytes and manifest SHA-256.

## Differences, caveats and follow-up — measured / planned

- **Section 2 agrees with the active case grids, acquisition dates, test baseline and source versions.** Its expected diagonal-only branch is confirmed, rather than assumed.
- Some earlier documentation still says “displacement” for a dB difference, displays historical test counts, or describes older data readiness. The latest appended progress entries correct the meaning. Those preserved snapshots are not current physical movement claims; record/reconcile their user-facing wording through the planned Claim Ledger instead of silently rewriting frozen evidence.
- The Phase 0 run emits **105 dependency deprecation warnings** while passing. They are not test failures and were not hidden.
- Existing Change Lab QA embeds historical 169/25 test-count fields. The current `make verify` pytest/Node output is the controlling 189/37 count; do not sum old embedded values as additional tests.
- The heading at the top of `PROJECT_PROGRESS.md` still advertises the 14 October milestone; the latest 31 October entry and current tests control this orientation. No reset or removal of that history occurred.
- Current active files are approximately **6.22–6.75 GiB each** (57.59 GiB across nine unique inputs), rather than assuming the prompt's generic 30–61 GB warning describes these particular files. Future candidates still require exact size listing and approval before large downloads.
- The existing portable archive has no investigation workspace or Bangladesh case manifests. It genuinely predates these additions; it was inspected, not rebuilt.
- Bangladesh terrain/rain/optical context, instrument-gap calendar, new physics proxies, Explanation Fit, frozen reference scoring, interferometry and the project-wide Claim Ledger remain **planned**. Nepal POWER and excluded IMERG-GIS diagnostic records remain preserved; rejected GIS zeros must not be reused as accepted rainfall.
- Direct browser visual/accessibility/GPU verification and a physical disconnected rehearsal remain unverified. The earlier explicit browser URL-policy block is preserved; no Playwright, alternate browser or indirect bypass was attempted.
- The current Git checkout has pre-existing modified and untracked work. Phase 0 does not reset, clean, commit, publish or alter Git metadata. Phase 5's requested “commit before reference inspection” will need to respect the available permissions at that future gate.

## Next boundary — planned

Proceed to **Phase 1 / Implementation 10** only after the user's go-ahead. First verify the official gap notice and current archive candidates; build a nominal-slot calendar with observed/unloaded/gap/unavailable states backed by actual queries. Do not download scenes at that step. The final archive-candidate list and sizes must be reviewable before any large download approval.
