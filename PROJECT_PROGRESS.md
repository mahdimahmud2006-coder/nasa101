> **Current update — 14 October 2026:** TerraPulse 1.0 now includes implementations 01–07, the radar-led Evidence Studio, Change Lab, runtime preflight and portable packaging. All 508 previously recorded analytical outputs remain unchanged. Current verification is 169 Python tests and 25 JavaScript logic tests, plus analytical validators. See [final project diagnosis](docs/FINAL_PROJECT_READINESS.md) and [implementation 06/07](docs/IMPLEMENTATION_06_07.md). The report below is the preserved earlier milestone history; its original test counts and browser checks are historical. Current browser visual QA, physical disconnected rehearsal, empirical hazard validation and competition eligibility remain pending.

# TerraPulse — Full Project Progress and Verification Report

**Report generated:** 2026-09-30 21:56:12 +06 (UTC+06:00)  
**Team:** DevAtMad  
**Challenge:** Dancing with the SARs  
**Case:** Nepal Himalayan Surface-Change Investigation  
**Workspace:** `/home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1`

## 1. Current project status

The **local implementation is complete and verified for the supplied Nepal case**. TerraPulse now converts real NISAR HDF5 measurements into an offline interactive surface-change investigation. Six source products have been audited, three repeat observations identified, and all three temporal comparisons computed and exported.

Fresh verification for this report: **27 automated tests passed, zero failed**, and **all three exported comparisons validated**. Python compilation and JavaScript syntax checks passed. The current Python source-code fingerprint matches the fingerprint stored with the outputs.

This completes the local processing/demo milestone. It does not establish independently validated disaster causes or publication/submission readiness. NISAR is **PROVISIONAL** and every causal interpretation remains **UNVERIFIED**.

### Milestones

| Workstream | Status | Evidence |
| --- | --- | --- |
| Raw audit | Complete | All six HDF5s inventoried: actual schema, attributes, timestamps, coordinates and fill values. |
| Repeat observations | Complete | Three distinct dates; same-date releases excluded from temporal mixing. |
| Comparability | PASS | All three selected pairs share compatible geometry, processing version and native grid; >99% footprint overlap. |
| Fixed analysis area | Complete | 24 km square around Kathmandu Valley/northern hills; chosen before inspecting change. |
| Deterministic science | Complete | Quality masking, power-to-dB, median filter, signed change, MAD cutoff, cleanup, connected regions and projected area. |
| Scientific outputs | Complete | All three comparisons have real rasters, region statistics, GeoJSON, sensitivity and provenance. |
| Science tests | PASS | 27 cases passed in the fresh run for this report. |
| Export validation | PASS | All three saved comparisons validate against raster/mask/region geometry. |
| Interactive viewer | Complete; previously verified | Before/after/swipe, scan reveal, overlay, date-pair selector, region inspection, zoom and methods. |
| Responsive layout | PASS in original QA | Desktop 1366 × 900 and phone 390 × 844, without horizontal overflow. |
| Offline asset loading | PASS in original QA | All observed page resources loaded from localhost; no CDN/font/basemap dependency. |
| Documentation/license | Complete for local milestone | Methods, datasets, limitations, validation, AI-use, runbook and Apache-2.0 code license. |
| Physical disconnected rehearsal | Not performed | Machine Wi-Fi was not turned off. |
| Independent causal validation | Not performed | All causes remain UNVERIFIED; no confirmed flood/landslide claim. |
| Public repository / submission | Not performed | No upload or competition submission was made. |

## 2. How the project looks now

The viewer is a dark earth-observation workspace with muted green panels and yellow scan/highlight accents. One real Nepal case is enabled.

| Area | Current features |
| --- | --- |
| Header | TerraPulse branding, local-data context, NISAR PROVISIONAL labels and Methodology. |
| Left controls | Kathmandu Valley case, three dates, all three date pairs, Before/Swipe/After controls, overlay toggle and SCAN REGION. |
| Central radar viewer | Real local radar previews, draggable swipe handle, north indicator, scale bar, zoom/reset controls and computed change overlay. |
| Summary strip | Common valid analysis area, candidate change area and retained region count. |
| Evidence panel | Dates, repeat interval, selected-region statistics, histogram, threshold rule, sensitivity and cause-UNVERIFIED status. |
| Region interaction | Select actual map polygons or ranked region buttons; center/zoom on a selected region. |
| Methods dialog | Granule IDs, exact source path, polarization, AOI/grid, preprocessing, thresholds, cleanup, area method, alternatives, versions and limits. |
| Zero-result state | Aug 31 → Sep 12 displays no retained nominal candidates; it does not claim no real change occurred. |
| Downloads | Selected-pair evidence JSON; geographic GeoJSON available in methods. |

The yellow radar sweep reveals **saved deterministic evidence**. It is presentation, not live AI inference. Yellow marks increased backscatter; blue marks decreased backscatter. Quantities come from native-resolution processing, not display-image pixels.

### Saved interface screenshot

The original browser-verification screenshot shows Aug 19 → Sep 12: **0.7949 km² and 30 candidate regions**. It was not recaptured during this reporting turn.

![TerraPulse verified demo](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/demo.png>)

## 3. Dataset audit

Source: **NASA–ISRO NISAR L2 GCOV PROVISIONAL**, collection `NISAR_L2_GCOV_PROVISIONAL_V1`, product DOI `10.5067/NIL2GCOV-P1` from source metadata.

| Local HDF5 | Acquisition date, UTC | Product version | Release | Selected |
| --- | --- | --- | --- | --- |
| `aug19(1).h5` | 2026-08-19 | 1.0.12 | X05026 | No: alternate same-date release |
| `aug19.h5` | 2026-08-19 | 1.0.11 | P05023 | Yes |
| `aug31(1).h5` | 2026-08-31 | 1.0.12 | X05026 | No: alternate same-date release |
| `aug31.h5` | 2026-08-31 | 1.0.11 | P05023 | Yes |
| `sept12(1).h5` | 2026-09-12 | 1.0.12 | X05026 | No: alternate same-date release |
| `sept12.h5` | 2026-09-12 | 1.0.11 | P05023 | Yes |

The `(1)` products are alternate processing releases of the same acquisitions, not extra dates or adjacent coverage. The consistent **P05023 / 1.0.11** series is used. Science dataset paths/grids agree between variants; processing metadata and some string widths differ. No same-date or mixed-version temporal comparison is used.

Raw filenames and locations are preserved. The archive is retained without redundant extraction. All six HDF5 sizes still match the saved audit. Byte-size agreement is not a whole-file checksum.

### Verified measurement and geometry

- Track **98**, frame **16**, ascending and left-looking.
- Term **HHHH / HH polarization / frequency A**, real diagonal covariance power.
- Exact path: `/science/LSAR/GCOV/grids/frequencyA/HHHH`.
- Source shape **33840 × 34488**.
- Native CRS **EPSG:32645**, spacing **10 m × 10 m**, with y spacing −10 m.
- AOI: requested center **85.33° E, 27.80° N**, **24 km × 24 km**, snapped to **2400 × 2400 pixels**.
- Fixed geographic extent was chosen before inspecting change, for context and bounded processing.
- No reprojection or mosaicking is needed for this set. Incompatible grids are rejected.

### Accepted repeat pairs

Overlap is intersection area divided by the smaller footprint area, after projecting footprints to UTM.

| Pair | Separation, days | Footprint overlap | Status |
| --- | --- | --- | --- |
| aug19.h5 → aug31.h5 | 12 | 99.8950% | PASS |
| aug19.h5 → sept12.h5 | 24 | 99.8918% | PASS |
| aug31.h5 → sept12.h5 | 12 | 99.2782% | PASS |

### Source quality counts

| Source | AOI pixels | Valid after source quality gates | Valid after median filtering |
| --- | --- | --- | --- |
| aug19.h5 | 5,760,000 | 5,749,602 | 5,735,334 |
| aug31.h5 | 5,760,000 | 5,672,910 | 5,658,643 |
| sept12.h5 | 5,760,000 | 5,492,956 | 5,478,640 |

Median-filter outputs require every contributing source pixel to be valid. Common valid coverage is then calculated independently per pair.

## 4. Implemented scientific workflow

```text
Actual HDF5 audit → repeat-date / geometry / version / overlap checks
→ fixed native-grid AOI extraction
→ finite positive power, valid source mask and positive number of looks
→ 10 × log10(real diagonal gamma-0 power)
→ nodata-safe 3 × 3 median per observation
→ common finite-pixel mask
→ signed ΔdB = after − before
→ robust threshold → minimal opening → connected-region size filtering
→ native-pixel areas and regional statistics
→ sensitivity, geographic boundaries, local previews and evidence JSON
```

| Parameter | Current value |
| --- | --- |
| Metric | Signed after-minus-before dB change |
| Robust spread | 1.4826 × median(abs(ΔdB − median(ΔdB))) |
| Nominal detection rule | abs(ΔdB) ≥ 3.0 × robust spread |
| Threshold center | Zero physical change; measured distribution median is recorded, not subtracted. |
| Median preprocessing | 3 × 3, with strict all-valid contributing neighborhoods |
| Opening | One iteration, four-connected 3 × 3 cross |
| Minimum region | 100 native pixels |
| Connectivity | Four-connected |
| Ranking | Area descending, then absolute median change descending |
| Area method | Absolute affine determinant × CRS linear-unit factors |
| Actual pixel grid area | 100 m² = 0.0001 km² |
| Sensitivity | Cutoff −10%, nominal, +10%; identical cleanup |
| Other candidates reported | MAD multipliers 2.0, 2.5 and 3.0 |

Area is projected grid area, not sloped terrain surface area. Geographic-degree grids are rejected rather than assumed to have constant area. Display previews use shared contrast and at most 1200 pixels per side; native rasters determine measurements.

### Preserved baseline

The first unsmoothed conservative run retained **zero regions**. It remains in `data/derived/baseline_unsmoothed.json`. The final small median filter reduces isolated SAR speckle and is explicitly recorded. No disaster classification or desired event shape was manufactured.

## 5. Computed results

These are **threshold-dependent radar-change candidate areas**, not confirmed disaster-impact areas.

| Comparison, UTC dates | Common valid km² | Nominal cutoff dB | Candidate km² | Regions |
| --- | --- | --- | --- | --- |
| 2026-08-19 → 2026-08-31 | 565.8349 | 4.1190 | 0.0195 | 1 |
| 2026-08-19 → 2026-09-12 | 547.8402 | 4.3204 | 0.7949 | 30 |
| 2026-08-31 → 2026-09-12 | 547.8383 | 3.9954 | 0.0000 | 0 |

### Threshold sensitivity

Sensitivity is not statistical confidence or classification accuracy.

| Comparison | Area at −10% cutoff, km² | Nominal area, km² | Area at +10% cutoff, km² |
| --- | --- | --- | --- |
| 2026-08-19 → 2026-08-31 | 0.0301 | 0.0195 | 0.0178 |
| 2026-08-19 → 2026-09-12 | 1.5218 | 0.7949 | 0.4174 |
| 2026-08-31 → 2026-09-12 | 0.0111 | 0.0000 | 0.0000 |

### Alternative MAD thresholds

The final nominal method uses multiplier 3.0. Other rows document parameter sensitivity.

| Comparison | MAD multiplier | Cutoff dB | Candidate km² | Regions |
| --- | --- | --- | --- | --- |
| 2026-08-19 → 2026-08-31 | 2.0 | 2.7460 | 0.3666 | 18 |
| 2026-08-19 → 2026-08-31 | 2.5 | 3.4325 | 0.0569 | 4 |
| 2026-08-19 → 2026-08-31 | 3.0 | 4.1190 | 0.0195 | 1 |
| 2026-08-19 → 2026-09-12 | 2.0 | 2.8803 | 4.2159 | 100 |
| 2026-08-19 → 2026-09-12 | 2.5 | 3.6003 | 2.0201 | 52 |
| 2026-08-19 → 2026-09-12 | 3.0 | 4.3204 | 0.7949 | 30 |
| 2026-08-31 → 2026-09-12 | 2.0 | 2.6636 | 0.2798 | 17 |
| 2026-08-31 → 2026-09-12 | 2.5 | 3.3295 | 0.0197 | 1 |
| 2026-08-31 → 2026-09-12 | 3.0 | 3.9954 | 0.0000 | 0 |

## 6. All automated test cases that passed

Fresh `make test` result: **27 passed in 0.57 s**, no failures or skips. Parameterized cases are listed separately. Actual test source: `tests/test_science.py`.

| # | Exact collected test name | Behavior checked | Result |
| --- | --- | --- | --- |
| 1 | `test_area_100_thirty_metre_pixels` | 100 pixels of 30 m × 30 m yield exactly 0.09 km² within tolerance. | PASS |
| 2 | `test_rotated_area_uses_determinant` | Rotated/sheared affine geometry uses the determinant. | PASS |
| 3 | `test_geographic_area_rejected` | Longitude/latitude grids are rejected for projected-area calculation. | PASS |
| 4 | `test_identical_arrays_zero_change` | Identical observations produce zero change. | PASS |
| 5 | `test_known_signed_delta` | Known increases/decreases produce correct signed differences. | PASS |
| 6 | `test_nodata_not_change` | NaN/Inf never become false change candidates. | PASS |
| 7 | `test_unaligned_arrays_rejected` | Mismatched array shapes are rejected. | PASS |
| 8 | `test_components_and_area` | Small regions are removed; retained areas and statistics match known geometry. | PASS |
| 9 | `test_cleanup_never_fills_invalid` | Cleanup cannot turn invalid pixels into candidates. | PASS |
| 10 | `test_no_change_no_regions` | Zero change produces no connected candidates. | PASS |
| 11 | `test_mad_cutoff` | The configured robust MAD formula gives the expected cutoff. | PASS |
| 12 | `test_zero_mad_requires_explicit_threshold` | Zero MAD requires an explicit absolute-dB cutoff. | PASS |
| 13 | `test_bad_threshold_rejected[0]` | Invalid threshold parameter is rejected; separate zero, negative and NaN cases. | PASS |
| 14 | `test_bad_threshold_rejected[-1]` | Invalid threshold parameter is rejected; separate zero, negative and NaN cases. | PASS |
| 15 | `test_bad_threshold_rejected[nan]` | Invalid threshold parameter is rejected; separate zero, negative and NaN cases. | PASS |
| 16 | `test_sensitivity_uses_same_cleanup` | Sensitivity uses the same cleanup and yields expected areas. | PASS |
| 17 | `test_date_nanoseconds_and_utc` | Nanosecond source dates are interpreted with UTC semantics. | PASS |
| 18 | `test_same_observation_versions_not_temporal` | Same-date processing variants cannot form a temporal comparison. | PASS |
| 19 | `test_real_repeat_pair` | Actual Aug 19/Aug 31 metadata passes repeat-date and overlap checks. | PASS |
| 20 | `test_incompatible_geometry_rejected[track-1]` | The altered track, orbit direction, product version or spacing is rejected. | PASS |
| 21 | `test_incompatible_geometry_rejected[orbit_direction-Descending]` | The altered track, orbit direction, product version or spacing is rejected. | PASS |
| 22 | `test_incompatible_geometry_rejected[product_version-other]` | The altered track, orbit direction, product version or spacing is rejected. | PASS |
| 23 | `test_incompatible_geometry_rejected[spacing-value3]` | The altered track, orbit direction, product version or spacing is rejected. | PASS |
| 24 | `test_extract_masks_and_converts_power` | Synthetic HDF5 extraction masks invalid samples and converts valid power to dB. | PASS |
| 25 | `test_median_removes_isolated_speckle` | Median filtering removes an isolated spike and protects raster edges. | PASS |
| 26 | `test_median_does_not_leak_nodata` | Invalid neighborhoods cannot leak through preprocessing. | PASS |
| 27 | `test_histogram_zero_is_centered_and_preserves_pixel_count` | Histogram zero is centered and counts preserve finite pixels. | PASS |

These numerical/ingestion tests include synthetic arrays/HDF5 and saved real metadata. They do not prove independent event-classification accuracy, exhaustive test coverage or subpixel image-registration accuracy.

### Fresh terminal output

```text
$ make test
.venv/bin/python -m pytest -q
...........................                                              [100%]
27 passed in 0.57s

$ make validate
.venv/bin/python -m src.compute.validate
PASS t1_t2: raster, mask, region statistics and geographic polygons agree (0.0195 km²)
PASS t1_t3: raster, mask, region statistics and geographic polygons agree (0.7949 km²)
PASS t2_t3: raster, mask, region statistics and geographic polygons agree (0.0000 km²)
All exported comparisons validated.
```

## 7. Export validation and additional fresh checks

`make validate` passed for all three comparisons:

| Check | Result |
| --- | --- |
| Mask grid and CRS agree with saved change raster | PASS |
| Summary candidate area agrees with actual retained pixels | PASS |
| Invalid pixels are never classified as candidate change | PASS |
| Mask nodata matches invalid change pixels | PASS |
| Saved mask reproduces exactly from saved change and processing parameters | PASS |
| Evidence region count agrees with regional records | PASS |
| Summed region areas agree with total candidate area | PASS |
| GeoJSON feature count agrees with retained regions | PASS |
| Projected geographic-vector area agrees with raster area within coordinate-rounding tolerance | PASS |
| Region polygons are geometrically valid | PASS |
| Every exported causal status remains UNVERIFIED | PASS |

| Other check | Fresh result |
| --- | --- |
| python -m compileall -q src | PASS: Python modules compile |
| node --check web/app.js | PASS: JavaScript syntax valid |
| Current/exported Python source-code fingerprint | PASS: exact match |
| Six raw source sizes versus audit | PASS: unchanged byte sizes |
| Saved screenshot | Present |
| Unsmoothed baseline | Present |

Source-window SHA-256 values cover the extracted native power, quality mask and number-of-looks bytes. They are **not** checksums of the complete multi-GB source files. Ingestion also checks identity, layer shape and coordinates/CRS against audited metadata.

## 8. Browser, responsive and offline verification

The following results are the **existing browser-verification record in `docs/QA.json`**, not new browser tests in this reporting turn. Scientific/export/syntax/fingerprint checks above were refreshed for this report.

| Browser behavior | Recorded result |
| --- | --- |
| Before/after view | PASS |
| Slider enabled only in swipe mode | PASS |
| Direct drag of swipe handle | PASS |
| Scan reveal animation | PASS |
| Actual area/statistics | PASS |
| All three acquisition pair selections | PASS |
| Actual geographic-region polygon selection | PASS |
| Region-centered zoom | PASS |
| Overlay toggle | PASS |
| Methodology dialog open/close | PASS |
| Zero-region state | PASS |

| Environment check | Recorded result |
| --- | --- |
| Browser | Codex in-app browser |
| Console | 0 errors; 0 warnings |
| Desktop | 1366 × 900; no horizontal overflow |
| Phone | 390 × 844; no horizontal overflow |
| Radar/overlay loading | PASS |
| Observed asset sources | All localhost; 0 external page asset requests |
| Runtime | OFFLINE=1, local assets only |
| External CDN / font / basemap dependency | None |
| Earthdata login / runtime API key | Not required |
| Wi-Fi physically disabled | No: not tested |

Online NASA/ASF links are optional references activated on click. They are not needed for the local demo. A physical disconnected rehearsal remains a separate user-operated preparation step; machine networking settings were not changed.

## 9. Current project structure

```text
NEPALv1/
├── six original .h5 files and aug19.zip
├── IMPLEMENTATION.md / SKILL.md
├── README.md / PROJECT_PROGRESS.md / LICENSE
├── Makefile / config.json / pyproject.toml / requirements.txt
├── .env.example / .gitignore
├── src/
│   ├── ingest/
│   │   ├── inspect_h5.py           complete actual schema audit
│   │   ├── metadata.py             inventory and pair checks
│   │   └── extract_gcov.py         window extraction and source checks
│   ├── compute/
│   │   ├── align.py                compatible grids / common mask
│   │   ├── preprocess.py           validity-safe median filter
│   │   ├── change.py               delta and histogram/statistics
│   │   ├── threshold.py            configurable MAD/absolute cutoff
│   │   ├── regions.py              cleanup, regions and ranking
│   │   ├── area.py                 real projected pixel geometry
│   │   ├── uncertainty.py          cutoff sensitivity
│   │   ├── pipeline.py             complete scientific orchestration
│   │   └── validate.py             exported-data consistency
│   ├── export/artifacts.py         rasters, previews, boundaries, JSON
│   └── api/app.py                  local standard-library server
├── tests/test_science.py           27 collected cases
├── data/derived/
│   ├── audit.json / audit.txt / inventory.json
│   ├── baseline_unsmoothed.json
│   └── nepal_case_01/
│       ├── native/processed observations and previews
│       ├── t1_t2/ / t1_t3/ / t2_t3/
│       └── metadata, AOI, config, manifest and primary-pair aliases
├── web/
│   ├── index.html / styles.css / app.js
│   └── public/cases/nepal_case_01/  compact local demo assets
└── docs/
    ├── DATASETS.md / METHODOLOGY.md / VALIDATION.md
    ├── LIMITATIONS.md / AI_USE.md / DEMO_RUNBOOK.md
    ├── QA.json / RESULTS.json / demo.png
    └── reports/progress-verification.json
```

The repository uses the smallest structure supporting this verified case rather than every optional file in the plan. The server exposes local JSON endpoints without requiring FastAPI.

## 10. Artifacts and reports available now


| Output group | Files | Size |
| --- | --- | --- |
| Full analytical case | 53 | 211.56 MiB |
| Compact public demo case | 34 | 16.02 MiB |


Each comparison has `change_raw.tif`, `change_mask.tif`, `region_labels.tif`, `change_regions.geojson`, `regions_display.json`, change previews, `overlay.png`, `evidence.json` and `methodology.json`.

Case-level outputs include the three native unfiltered dB rasters, three processed rasters, shared-contrast previews, `aoi.geojson`, `metadata.json`, `manifest.json` and configuration. Top-level before/after/evidence aliases refer to the primary Aug 19 → Aug 31 pair. No raw HDF5 is loaded by the browser.

### Supporting reports

- [README.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/README.md>): project overview and operation.
- [DATASETS.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/DATASETS.md>): granule IDs, dates, release selection and actual layer paths.
- [METHODOLOGY.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/METHODOLOGY.md>): implemented science and preprocessing.
- [VALIDATION.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/VALIDATION.md>): input, numerical and interpretation checks.
- [LIMITATIONS.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/LIMITATIONS.md>): provisional status, ambiguity and scope.
- [AI_USE.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/AI_USE.md>): AI assistance and deterministic computation.
- [DEMO_RUNBOOK.md](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/DEMO_RUNBOOK.md>): demo/rehearsal sequence.
- [QA.json](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/QA.json>): original browser, responsive and offline verification record.
- [RESULTS.json](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/RESULTS.json>): saved numerical comparison summaries.
- [progress-verification.json](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/docs/reports/progress-verification.json>): fresh verification snapshot supporting this report.
- [test_science.py](</home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/tests/test_science.py>): actual test implementation.


## 11. Software versions and provenance

| Component | Exported version |
| --- | --- |
| terrapulse | 1.0.0 |
| python | 3.14.4 |
| numpy | 2.5.3 |
| scipy | 1.18.1 |
| h5py | 3.16.0 |
| rasterio | 1.5.1 |
| pyproj | 3.8.0 |
| shapely | 2.1.2 |
| pillow | 12.3.0 |

Current/exported Python-source SHA-256:

```text
d5376750574d465ec875fc9b1013da8125080b0639097a6748a78414c8335157
```

Evidence preserves original source filenames and internal granule IDs, UTC timestamps, exact HDF5 path, product/specification versions, track/frame/orbit/look/pass, DOI, source sizes, actual AOI/window/grid, validity counts, window checksums, preprocessing, thresholds, cleanup, measured regions, sensitivity, software versions and validation status.

## 12. Run and reproduce

From the project folder:

```bash
make demo
```

Open **http://127.0.0.1:8000/**. The exact command is:

```bash
OFFLINE=1 .venv/bin/python -m src.api.app
```

The already-shipped viewer can run with standard Python without installing the scientific stack:

```bash
OFFLINE=1 python3 -m src.api.app
```

The server binds to loopback; `--port 8001` can select another port. This report does not independently verify that the server is still active at the moment the report is read.

To reproduce the science:

```bash
make setup       # initial dependency download requires internet
make inspect     # actual source schema and metadata audit
make test        # all numerical/ingestion tests
make process     # all three comparisons and viewer assets
make validate    # saved raster/mask/region/vector checks
```

Audit again after changing raw files; process again after changing configuration. Scientific values are computed by ordinary code, with no LLM runtime or generated causal classification. Code assistance is documented in AI_USE.md.

## 13. Remaining work and limitations

| Item | Current state / next step |
| --- | --- |
| Independent causal validation | Not done. Independent optical/event/ground evidence is needed before confirmed flood or landslide language. |
| Physical offline rehearsal | Not done. Manually disable Wi-Fi and repeat the runbook. |
| Public event-specific framing | Neutral surface-change framing is implemented; stronger claims need evidence and review. |
| Public repository | Not uploaded; review sharing scope and exclusions before publication. |
| Competition submission | Not submitted; submission material and event readiness remain separate steps. |
| Arbitrary/global data operation | Outside this case; live global acquisition, automatic reprojection and neighboring-frame mosaicking are not implemented. |
| Formal performance assessment | No independent classification accuracy, calibrated confidence interval, registration accuracy or operational certification is claimed. |

NISAR remains **PROVISIONAL**. Radar changes can reflect moisture, vegetation, terrain, speckle or processing effects. Median preprocessing introduces local dependence and suppresses small changes. Cutoffs and minimum-region filtering influence areas, as the sensitivity tables show. Projected area is not sloped terrain area. Zero retained regions does not prove no change.

The completed milestone is a reproducible local **surface-change investigation demo** with real measurements, tested outputs, visible uncertainty and source provenance. Independent causal validation, a physical offline rehearsal and external publication/submission remain unfinished workstreams.

## 14. Next-phase update — 1 October 2026

The earlier sections record the first implementation milestone. The next phase now adds fixed-pixel temporal analysis for all 30 August 19 → September 12 regions (29 descriptive cumulative-consistent, one early-dominant), +10% threshold robust cores for all three pairs (0.0178, 0.4174, 0.0000 km²), and a top-ten independent source screen. The archived UNOSAT/UNESCO mapped flood polygons intersect none of the 30 nominal candidates, so every cause remains **UNVERIFIED**. Sentinel-2 catalog metadata was screened, but no optical pixels were validated. The research uses no Chinese government or agency source.

The viewer now defaults to the 24-day pair and exposes nominal/robust overlay, temporal class, source-review note and the zero-region explanation. `make process` reproduces the new outputs; `make test` passes 38 tests and `make validate` checks nominal preservation, robust geometry/area, temporal geometry and source checksum. Python compilation and JavaScript syntax checks pass. The current source fingerprint is saved in pair evidence.

The updated viewer has **not** passed an interactive browser test because the browser tool blocked access to the local page under its URL policy. The physical Wi-Fi/Ethernet-disabled rehearsal also remains pending user action, as recorded in `docs/QA.json`. The empty `.git` directory is not an initialized repository (`git status` fails), so no competition tag or publication was performed. The science version should not be marked frozen until those checks and repository setup are complete.

## 15. Implementation 02 — 14 October 2026

All 16 HDF5 files in `database for imp2` were audited, alongside the other supplied data (27 non-cache files total). The new dates change track/frame or frequency-A bandwidth/carrier/polarization configuration and do not extend the original compatible frame-16 series. The matching frame-17 August 19/31 files form a separate two-date group. Exact decisions and compatible groups are preserved in `data/derived/nepal_case_01/timeseries/source_audit.json`.

The functional time-series extension is implemented: compatible-observation manifests, canonical Cloud Optimized GeoTIFFs, successive signed differences and centered MAD scores, fixed zone tracking, missing-data-safe transition-frequency maps, baseline-relative recovery, Parquet/GeoJSON evidence, four API routes, and a separate timeline viewer at `/timeseries.html`. It currently uses the compatible August 19/August 31/September 12 acquisitions. The new centered-score candidate areas are 0.0199 and 0.0000 km², with one tracked zone. The score cutoff remains explicitly **UNCALIBRATED**; causes remain **UNVERIFIED**.

The tracked zone has 199 native pixels, a mean signed baseline displacement of −7.5263 dB at its August 31 observed peak and −7.0766 dB on September 12. Its transition frequency is 1/2 and its descriptive return-toward-baseline metric is 5.97%. A zero later successive candidate mask does not imply that the earlier displacement disappeared.

**73 tests pass**. Original export validation and the time-series pixel/COG/geometry/Parquet validator pass; all 73 historical analysis artifacts remain byte-identical to the pre-extension snapshot. HTTP-handler/static resource checks pass, and Python/JavaScript syntax checks pass. Interactive browser verification and physical disconnected rehearsal remain pending; no prior browser policy block was bypassed. Additional compatible dates and actual validation evidence are still needed for a longer series and calibrated cutoff. Full details are in [docs/IMPLEMENTATION_02.md](docs/IMPLEMENTATION_02.md) and `docs/reports/implementation_02_qa.json`.

## 16. Released-challenge review — 28 October 2026

This entry supersedes earlier milestone descriptions for current status. Implementations 01–07, Evidence Studio, Change Lab, the terrain/rainfall and Landsat context, exploratory flood/landslide models, release tools, and existing analytical outputs remain intact. Earlier use of “displacement” for a dB difference means a **backscatter difference**, not measured ground motion. The archived independent map describes preliminary mudflow/rockflow impacts, not flood-water extent.

The newly supplied Dancing with the SARs statement was reviewed against the actual project and primary NASA/ASF documentation. The recommended next phase is a corroborated surface-change investigation with a longer baseline, paired HH/HV measurements, and a traceable evidence dossier. The complete analysis, project alternatives and acceptance gates are in [the challenge strategy](docs/CHALLENGE_STRATEGY_2026-10-28.md).

Three new feasibility results were established: the existing full scenes cover the independent impact mapping (17/17 representative sample points quality-valid on every date); actual HV data are present and usable in the current crop; NASA CMR now lists candidate acquisitions on ten dates for this track/frame. These are research results, **not an implemented second case, ten-date series, independent causal validation, or a new application polarization mode**. No additional HDF5 products were downloaded. New datasets must continue to meet the user's non-Chinese-source requirement.

The radar-layer coverage badge was corrected to use radar validity rather than flood-model assessability. All 26 JavaScript tests pass with explicit mocks, static checks pass, and all 508 previously recorded analytical outputs were rehashed unchanged. The prior Python baseline remains 169 tests; that suite was not rerun in this research turn. README source/measurement/interface claims were corrected. Current browser visual checks and a physical disconnected rehearsal remain pending. The existing portable archive predates these review corrections and must be rebuilt before distributing updated source. Public repository access and actual competition submission were not verified or performed in this review.

## 17. Three-workspace build — 28 October 2026

The project remains **TerraPulse**. The new `/investigations.html` workspace now contains **Surface investigations**, **River Memory**, and **Wetland Pulse**. Two real Nepal investigation cases are processed with frequency-A HH and HV: the retained Kathmandu crop and an added reference-aligned Rasuwa–Nuwakot crop. Users can play actual dates, compare first/selected observations, switch between baseline and successive differences, inspect fixed common-valid neighborhoods, view paired traces and export source-linked evidence dossiers. The new corridor intersects approximately 6.4230 km² of preliminary mapped mudflow/rockflow impacts; spatial overlap is not event-classification accuracy.

The river/wetland signature engine, case configurations and interface are implemented. Bangladesh observations remain **AWAITING_DATA**. A live NASA CMR search identified a shared track-69/frame-14 ascending P05023 sequence covering both the Jamuna/Sirajganj and Tanguar Haor windows. Six priority full-scene files total about 38 GiB and support both modes without duplicate downloads. Their actual raw metadata, quality and compatible coverage must still pass import checks. Follow [download/import instructions](docs/DOWNLOAD_AND_IMPORT.md), then run `make investigations` and reload the workspace.

This build passes 187 Python tests and 35 JavaScript tests, the six analytical validation targets and static page checks. New controller tests use explicit mocks; browser visual QA remains unverified. All 508 earlier analytical artifacts remain unchanged. No new HDF5 product was downloaded by the agent and no competition submission/publication was performed. The existing distribution archive still predates the new implementation. Full details are in [Implementation 08](docs/IMPLEMENTATION_08_INVESTIGATIONS.md).

## 18. Jamuna upload imported — 31 October 2026

The user supplied **only the six full-scene files requested for Jamuna**, in `database/bangladesh-shared/`. All six embedded identities match the NASA/ASF catalog plan and pass physical comparability checks. River Memory now uses the real six-date Jamuna series (18 June–16 October 2026), with paired-valid coverage of 99.8001% across the 20 × 20 km crop. HH/HV playback, baseline and preceding-visit differences, signature gains/losses, observed-visit fractions, fixed-neighborhood probes and evidence exports are active.

Those **same full scenes also include Tanguar Haor**. No separate haor upload or external download was received/used. Extracting a second geographic crop from them passed 99.7640% paired-valid coverage across its 18 × 16 km window, allowing Wetland Pulse to activate without duplicate downloads. The two crops are distinct geographic analyses of the same six acquisitions.

A common-valid geographic study-window trace is now available immediately in each Bangladesh mode; local opposing signals can cancel in this average. Native-raster validation independently checks the dark/bright response areas, transition accounting and observed-visit fractions. Signatures remain uncalibrated and do not prove water, erosion or habitat change. No Nepal environmental context was reused as Bangladesh data.

Selective rebuild commands `make jamuna` and `make wetland` preserve other cases; `--case` can be repeated. All 189 Python tests and 37 JavaScript tests pass, along with the six analytical validation targets. The 508 earlier analytical outputs remain byte-identical and neither Nepal case was rebuilt. Current evidence and limitations are in [Implementation 09](docs/IMPLEMENTATION_09_BANGLADESH.md). Browser visual QA and a physical disconnected rehearsal remain pending.


## 19. 2 November 2026 — Master-plan Phase 1: acquisition truth

Phase 0 completed the baseline freeze. Phase 1 now adds honest nominal calendars to all four investigations and the Nepal time-series viewer. The official ASF instrument gap is shaded; unloaded slots are hatched and labeled; long/gap-crossing comparisons show their intervals. Existing playback uses only real observations. Dossiers now include this temporal provenance.

Four completed ASF crop searches found eight extra catalog-compatible PR/P05023 granules: four for Bangladesh (25.0547 GiB) and four for Nepal (26.4297 GiB). October 30 Nepal has only an incompatible UR result in this snapshot. No radar downloads or additional ingestion occurred. All new source metadata came from NASA/ASF (USA), upstream NASA–ISRO (USA/India).

`make verify` passes **207 Python tests, 42 JavaScript tests and six analytical validators**, plus readiness/static checks. All **795 frozen files** and **508 historical analytical outputs** are unchanged. Fresh timing QA is retained separately while historical report bytes are preserved. Browser visual/accessibility/GPU checks and disconnected rehearsal remain unverified.

See [Implementation 10](docs/IMPLEMENTATION_10_TIME_AXIS.md), [download decision sheet](docs/PHASE1_DOWNLOAD_CANDIDATES.md), and [verification summary](reports/phase1_2026_11_02/summary.json). Phase 1 calendar/search work is complete; download/ingestion needs approval under the master prompt. Phase 2 remains pending the user's go-ahead. This continues the original TerraPulse project and all its earlier workspaces.


## 20. 2 November 2026 — Master-plan Phase 2: diagonal-only radar relationships

All four cases now have new `dualpol-v1` products: CPR (HV−HH dB), fixed HH/HV/HH−HV false-colour composites, HH/HV/CPR baseline and preceding-visit differences, uncalibrated candidate scattering signatures, fixed-footprint CPR Parquet/traces and a cutoff-sensitivity explorer. The existing canonical HH/HV inputs supply every new measurement. There are no new radar acquisitions, and the original processing outputs and routes remain intact.

The protected 199-pixel Nepal footprint has ΔCPR **+5.7152 dB on Aug 31** and **+4.6256 dB on Sep 12**, showing that the preserved HH drop was larger than the HV drop. CPR is a sign reversal of the existing HH−HV relation, not independent corroboration. Physical causes remain unresolved. Low-return, HH-rise/stable-HV and HV-rise hints are explicitly uncalibrated, descriptive candidates. No DpRVI, decomposition, coherence or displacement is inferred from diagonal GCOV.

`make verify` passes **221 Python tests, 50 JavaScript tests and seven analytical validators**, plus readiness/static checks. The new validator checks native values and masks, exact composite channels, signature flags, source/code/assets hashes, Parquet rows and independently recomputed cutoff cells. All **795 frozen files**, **508 historical analytical outputs** and **45 additional Phase 1 files** retain their original checksums. Scientific figures were exported and inspected; app browser/accessibility/GPU QA remains unverified under the previous policy restriction.

See [Implementation 11](docs/IMPLEMENTATION_11_DUALPOL.md), [phase verification](reports/phase2_2026_11_02/summary.json) and [scientific atlas](reports/phase2_2026_11_02/figures/dualpol_atlas.png). In `/investigations.html`, use the new Dual-pol options in View and the “Read the relationship” panel. The original app environment needs no new package. Optional Matplotlib exports use a separate environment.

Phase 2 is complete. Phase 3 (independently sourced terrain/rain context and the 17 August stable-target investigation) awaits the user's go-ahead. Phase 1 large radar downloads remain a separate approval decision.


## 21. 2 November 2026 — Phases 3 and 4

Phase 3 adds separately sourced NASADEM windows for all four crops, buffered hydrology and geometry-screening candidates, exact UTC rainfall windows, frozen first-date/terrain putative control masks and full native-source histograms for the six Bangladesh scenes. Median slope is about 1.95 degrees Jamuna and 1.36 degrees Tanguar. The August dip remains unresolved. Scientific IMERG V07 catalog queries returned no matching 2026 granules; rain totals remain null and earlier GIS zeros stay excluded. Verification: 225 Python / 51 JavaScript tests and eight validators.

Phase 4 adds ten saved DNA footprints, map-neighborhood/polygon reasoning APIs, deterministic competing-explanation rules, observed-visit persistence and censored recovery, with no fabricated cause, confidence or historical matches. The original Nepal footprint remains intact; Bangladesh transition footprints are explicitly retrospective. A YAML 1.2 JSON-subset claim ledger generates README/app/presentation text. Numeric result drift is checked separately from source arithmetic. Verification: **235 Python / 54 JavaScript tests, nine validators**; all 795 frozen files and 508 historical outputs unchanged. No large radar acquisition was downloaded. Browser QA remains unverified. See Implementation 12/13 and the phase summaries.


## 22. 2 November 2026 — requested Phase 4 checkpoint

Phases 1–3 implementation and Phase 4 are complete, with explicit data gaps: scientific IMERG totals remain unavailable and the August 17 cause remains unresolved. A fresh full verification passes 235 Python tests, 54 JavaScript tests and nine analytical validators. All 1,315 preexisting outputs covered by the preservation wrapper, the 795-file freeze and the separate 508 historical analytical files are unchanged. The active ledger remains the Phase 4 snapshot.

See [the checkpoint report](docs/PHASE4_CHECKPOINT.md) for delivered features, limits, startup instructions and staged research. Earlier authorization had started Phase 5 optical acquisition and Phase 6 catalog screening; these are staged only and are not reported as completed phases or accepted scientific validation. This checkpoint follows the latest instruction to finish through Phase 3, proceed with Phase 4 and report.


## 23. 3 November 2026 — Phase 5 complete; Phase 6 Gate A complete

Phase 5 publishes date-matched HLS optical comparisons for twelve precommitted geographic reference footprints, preserving original saved profiles and adding twelve separately labeled profiles. Fourteen of 54 footprint/date comparisons have eligible optical pixels; 40 remain unavailable. All four cases retain their own scope and cloud gaps, and no nearby comparison is inherited by a user-selected polygon. Jamuna and Tanguar outcomes are mixed, retained without tuning and reported as descriptive overlap rather than accuracy. Small windows came from NASA/USGS/ESA upstream via Microsoft (USA), with full recorded provenance. OPERA catalogs were screened but no OPERA science raster is claimed. Verification: 239 Python / 55 JavaScript tests, ten validators. See [Implementation 14](docs/IMPLEMENTATION_14_REFERENCES.md).

Phase 6 completes the product-aware Gate A search/report and adds a case-specific planned-state panel and dossier section. Thirteen metadata-eligible candidates exist on loaded dates (four GUNW pairs, nine GSLC scenes). One Bangladesh GUNW search is incomplete. A bounded external-network probe returned NASA HTTP 401; no authenticated source headers or feasible crop subset were accepted. Derived GUNW single-pol output is no longer incorrectly rejected as a source acquisition mode mismatch. Coherence and LOS displacement remain null/planned; the conditional science branch is not implemented. No large download occurred. See [the gate report](docs/INTERFEROMETRY_GATE.md) and [Implementation 15](docs/IMPLEMENTATION_15_INTERFEROMETRY.md).

Final verification: **243 Python tests, 59 JavaScript tests and eleven analytical validators pass**, including reference leakage/scope, exact candidate dates/releases, null science fields and delayed case-switch responses. All 795 frozen files, 508 historical analytical outputs and 56 published Phase 5 artifacts are unchanged; the wrapper preserves all 1,374 preexisting output files in its scope. Claims use a new `claims-phase6-v1` snapshot. Original workspaces and scientific outputs remain intact. Browser visual/accessibility/GPU checks, physical disconnected rehearsal and a rebuilt portable release remain pending. Phase 7 has not started. The current local server was started for the updated preview.


## 24. 3 November 2026 — Phase 7 implementation and delivery candidate

The five existing pages now share persistent navigation and supported URL state. Investigations restores actual dates, saved/reference footprints, point neighborhoods and assessed polygons; missing dates and unsupported legacy states are explicit. Nepal-only pages remain scoped. Three Movements opens the existing Nepal detect/persist evidence then River Memory, with Wetland Pulse alongside. Keyboard map cursor/drawing, text summaries, focus/reduced-motion styles and native form labels are implemented. No scientific products or thresholds were rebuilt.

Automated verification passes **246 Python tests, 67 JavaScript tests and eleven analytical validators**. A separate audit serves 44 local page/source/evidence/reasoning requests with Python sockets and DNS forbidden, and checks labels and four theme contrast pairs. All 795 frozen files and 508 historical analytical outputs remain unchanged. The active ledger has 18 claims in a new `claims-phase7-v1` snapshot. These results do not establish a real-browser, assistive-technology, GPU or physically disconnected rehearsal.

A new dated release builder includes current rules, claims, shared modules and claim-linked provenance, excludes raw granules/credentials, preserves old archives and verifies every packaged file. Exact build success, size and checksum are recorded in `reports/phase7_2026_11_03/package-r2.json` and the archive sidecar. [Portable instructions](RELEASE_README.md), [claim-linked storyboard](docs/VIDEO_STORYBOARD.md), [browser checklist](docs/reports/browser_a11y_2026-11-03.md) and [offline runbook](docs/OFFLINE_REHEARSAL.md) are provided. See [Implementation 16](docs/IMPLEMENTATION_16_EXPERIENCE_RELEASE.md).

Phase 7 is **implemented pending manual acceptance**, not fully accepted: browser visual/accessibility/GPU checks remain unverified under the earlier policy block; the physical network-disconnected rehearsal awaits actual user evidence; clean judging-machine startup and public repository/video access remain unverified. The configured GitHub origin could not be verified by the web fetch; no push, upload, deployment or submission occurred. The optional static public copy is not built because current dynamic local APIs and asset size require a separate delivery design. Phase 6 coherence/LOS measurements remain planned until authenticated compatible subsets are accepted.


## 25. 3 November 2026 — supplied Nepal observations and measured coherence

Accepted all nine supplied files in `database/extra datasets/`: seven compatible Nepal GCOV observations and two GUNW pairs. The new **Expanded Nepal record** extends both existing Nepal crops to ten visits from June 20 to October 18, with explicit August 19 reference, observed-date playback, fixed-scale HH/HV/CPR maps and differences, common-footprint traces, native neighborhood inspection, shareable state and downloadable evidence. It is linked from Investigations and runs at `http://127.0.0.1:8001/expanded.html` in the current session; port 8000 was occupied by the earlier server.

The original 199-pixel Kathmandu footprint remains fully common-valid across ten visits. Its October 18 HH difference is about **−6.5660 dB relative to August 19**; original August 31/September 12 values remain unchanged. Earlier variability is visible, and the reference is not claimed to be undisturbed. Corridor all-visit support decreases explicitly from 62,829 to 62,820 pixels while preserving the same mapped footprint geometry and every older result.

Measured HH coherence is available for August 19→31 and August 31→September 12 at its separate native 20 m and 80 m grids. Native masks, connected components, uncorrected phase, ionosphere and uncertainty layers are retained with source/window hashes and provenance. These are actual supplied measurements, not synthetic phase consistency. Coherence summaries are crop-wide; original Change DNA and optical matches do not silently inherit new inputs. LOS displacement remains unresolved because reference, sign, unwrapping and correction checks are pending.

Full verification passes **255 Python tests, 80 JavaScript tests and twelve analytical validators**. Every coherence crop/mask reconciles with native HDF5 values, with 28 independently extracted GCOV interior samples and derived-asset hash checks. All 1,606 published products protected during verification retain their bytes, including the original 1,379 outputs and all previous archives; historical timing-report bytes are restored after retaining fresh QA output separately. The 795-file baseline also passes. Active claims use a new `claims-expanded-v2` snapshot; the old gate and claim snapshots remain preserved. No new dataset was downloaded.

The supplied files contain no Bangladesh or rainfall additions. River Memory and Wetland Pulse remain on six actual visits pending shared June 30, July 12, September 10 and October 4 GCOV files. Scientific IMERG Late catalog candidates exist, but no rain measurements were imported. The August 5/7 instrument-outage dates remain missing. Source metadata identifies NASA/ISRO and declared non-Chinese auxiliary providers; two filename/header flags are explicitly recorded. Real-browser/accessibility/GPU acceptance, physical offline rehearsal and clean judging-machine acceptance remain unverified. See [Implementation 17](docs/IMPLEMENTATION_17_SUPPLIED_DATA.md) and `reports/extra_2026_11_03/`. A new dated portable extension archive is built separately; earlier archives are preserved.


## 26. 3 November 2026 — playback repair and confirmed satellite gap

The instrument outage is a real permanent source gap, confirmed again against NASA / ASF. Chart lines now break across it and the interface explains why no extra NISAR file can restore August 5/7. Playback is available for both ten intensity visits and the two actual coherence pairs. Added map-level Play/Pause, Previous/Next, range and Loop, frame/date status and bounded missing/stalled-frame errors. The previous source deliberately disabled coherence playback; a browser-specific HH/HV failure remains unverified, so that cause is not invented.

The complete JavaScript suite passes **86 tests**, plus six-page static checks. All **795 frozen files** pass, and all expanded scientific assets retain their hashes. New metadata searches identify seven additional Nepal GUNW candidates and two known Bangladesh candidates; Bangladesh search is incomplete. Four recommended Nepal files total about **8.79 GiB**, including a 24-day July 26→August 19 endpoint comparison. It does not observe inside the outage. No science data was downloaded and no existing output or archive was replaced.

See [the playback repair](docs/PLAYBACK_AND_GAP_FIX.md), [direct NASA download guide](docs/NISAR_ADDITIONAL_GUNW_DOWNLOADS.md) and `reports/playback_2026_11_03/`. Reload the live source at port 8001 to load the updated controls. Existing portable archives predate this UI repair. Real-browser and physical offline acceptance remain pending under the recorded limits.


## 27. 3 November 2026 — Bangladesh calendar gaps and shared GCOV request

Both Bangladesh cases retain six actual visits. A fresh local inventory confirms that June 30, July 12, September 10 and October 4 GCOV files are still absent; newly supplied extra files are Nepal scenes. A new completed NASA/ASF metadata check for both Bangladesh crops verifies the four shared candidates and direct download URLs, totaling about **25.05 GiB**. GUNW cannot substitute for these GCOV intensity acquisitions. August 5 remains a permanent satellite-outage slot without an acquisition to recover.

The acquisition card now separates these two reasons, adds four direct NASA download actions with shared-folder instructions and clearly marks the outage as undownloadable. HH/HV and CPR traces stop at all missing repeat visits and the outage; their actual samples and endpoint metrics remain unchanged. **90 JavaScript tests** and six-page static checks pass. All 795 frozen baseline files and the protected Bangladesh science/calendar hashes remain unchanged. No science data was downloaded, no old product was overwritten, and real-browser acceptance remains unverified.

See [the gap explanation](docs/BANGLADESH_GAP_CLARIFICATION.md), [four-file NASA download guide](docs/BANGLADESH_GCOV_DOWNLOADS.md) and `reports/bangladesh_gap_2026_11_03/`. The current source is served on port 8001 by the independent user service. Existing portable archives predate the live interface repairs.


## 28. Geographic product presentation and improvement roadmap — 3 November 2026

The root now opens a TerraPulse overview with an interactive comparison of actual Jamuna HH observations, Bangladesh/Nepal country tabs, concise tool descriptions and a Field guide. The Nepal environmental workspace has the explicit `/studio.html` address; older root links carrying a Nepal selection retain that selection through a redirect. All analytical pages share geographic primary navigation and contextual country tools. Nepal retains its full record, dossiers, terrain/thermal, Change DNA/slopes, timeline and radar comparison. Bangladesh exposes River Memory, Wetland Pulse and a Surface change focus that reuses the two accepted Bangladesh crops without relabeling their scientific measurements. Shared links restore that focus and selected case; exports identify country and exploration focus separately from the source module.

Presentation uses real radar previews, a restrained dark/cyan landscape theme, readable controls, responsive layouts, keyboard country tabs and reduced-motion support. Explanatory material is organized into a Field guide and expandable evidence sections. Product-facing introduction copy describes capabilities rather than development history. The immutable scientific datasets, existing thresholds and historical products were not reprocessed.

The challenge/value review distinguishes a useful investigation workflow from unproven operational impact. The improvement plan and JSON tracker identify current implementation, pending manual acceptance, downloading Bangladesh GCOV, additional coherence, optical corroboration, user testing and deferred scientific claims. The four missing Bangladesh GCOV visits remain a data dependency; the permanent outage remains unobserved. No new dataset was marked accepted merely because a download is underway.

Verification: 101 JavaScript tests pass, including navigation/home controls and existing analytical playback; 9 targeted Python release/API checks pass; eight pages pass static checks; 132 local links/assets resolve; runtime preflight passes; 795 frozen baseline files match. The existing local preview service is active on port 8001, and opening the overview was queued in the app. Rendered browser, responsive visual and physical network-disconnected checks remain pending under the previously documented browser-policy restriction. No public deployment/submission or new release archive was made. Existing archives predate this UI revision.

Evidence: `reports/presentation_2026_11_03/summary.json`, `javascript.log`, `python.log`, `static_web.json`, `local_links.json`, `readiness.json`, `baseline.log`, and `source_manifest.json`. Planning: `docs/PRODUCT_IMPROVEMENT_PLAN.md`, `docs/PRODUCT_IMPROVEMENT_TRACKER.json`, `docs/CHALLENGE_VALUE_REVIEW.md`. Approximately 24 GiB free space was observed while downloads were in progress; recheck remaining download and processing requirements before importing.


## 29. Bangladesh ten-visit record from supplied downloads — 3 November 2026

Plan task SCI-01 is implemented and active. Four actual GCOV files in `database/new/` fill June 30, July 12, September 10 and October 4 in both Jamuna and Tanguar. Header audits verify the accepted ascending track 069/frame 014 L-band HH/HV physical configuration, nominal processing, zero input exception flags and P05023/product 1.0.11 compatibility. New crop extractions pass the existing valid-coverage threshold. NASA/ASF and declared NASA–ISRO/ESA-Copernicus auxiliary provenance were reviewed and retained.

An additive `bangladesh-v2` record contains ten dates from June 18 through October 16. It retains June 18 as reference and the nominal August 5 satellite outage. HH/HV maps, reference/successive differences, dark transitions and observed occupancy, CPR and composites, candidate hints, cutoff sensitivity, controls, histograms, rain request windows, saved Change DNA, reference-footprint traces and calendars are recomputed and version-bound together. The UI and point/polygon APIs use the same active record through `config.records.json`; exports identify the record and exploration focus. Homepage counts use the active registry. The four downloadable-gap prompts are removed from the active calendar; the actual outage remains explicit.

The original six COGs, frozen saved footprint masks and original putative-control selection masks are retained. Their ten-date common-valid supports happen to match the six-date supports exactly. Original optical comparisons are retained only on identical radar endpoint COGs and their original frozen footprints, rebound by actual timestamp. Each inserted date has explicit unavailable optical entries. No new GUNW, thermal, optical or scientific rainfall was supplied, and those measurements were not inferred from intensity.

Verification: 261 Python tests and 103 JavaScript tests pass; native checks reconcile 48 fresh raw interior samples and all-pixel CPR/differences, masks, occupancy and valid visit count, controls, fixed-footprint means, sensitivity checks, reference bindings and provenance. All 505 historical Bangladesh/calendar files and the 795-file frozen baseline match. Static pages, active-version runtime readiness and representative HTTP-handler delivery/reasoning with Python sockets/DNS forbidden pass. The existing preview service was restarted and is active on port 8001. Rendered browser checks and physical Wi-Fi-disconnected rehearsal remain unverified/pending under the prior restriction. No new release archive, public deployment or submission was made.

The plan and JSON tracker mark SCI-01 complete. Additional compatible GUNW, independent corroboration and user acceptance remain separately tracked. Details: `docs/IMPLEMENTATION_18_BANGLADESH_TEN_VISITS.md`. Evidence: `reports/bangladesh_import_2026_11_03/summary.json`, `source_audit.json`, `native_validation.json`, `build.json`, `activation.json`, `lineage_review.json`, `python.log`, `javascript.log`, `socket_denied_runtime.json`, `baseline.log`, `readiness.json`, `static_web.json`, `historical_sha256.json`, `source_manifest.json`. Earlier claim snapshots and release archives retain their dated scope.


## 30. Recorded-visit presentation — 3 November 2026

At the user's request, the primary acquisition timeline now shows recorded dates only. Bangladesh Surface change, River Memory and Wetland Pulse no longer show an August 5 nominal-date card, warning banner or shaded outage band. Nepal's intensity trace likewise omits the prominent outage banner and shading; its acquisition notice is under the closed Measurement coverage & interpretation section. Legacy investigation calendars follow the same recorded-visit presentation. Detailed nominal acquisition coverage, source notices and any legacy download actions remain under collapsed methods.

Plots retain actual UTC timestamps, elapsed-time positions and the existing line-break rules. No missing acquisition is inserted or connected as if continuously observed. Playback still traverses available source frames only. Interval captions use a neutral actual-day separation, while the original interval flags and coverage metadata remain in exports. No scientific data, threshold, footprint, reference, computation or native product was changed.

Verification: 104 JavaScript tests pass, including all Bangladesh focuses and the Nepal trace/playback checks. Eight pages pass static checks. All 505 historical Bangladesh/calendar files, ten active Bangladesh manifests, 690 active analytical assets across Bangladesh and expanded Nepal, and the 795-file frozen baseline match their existing checksums. Socket/DNS-denied handler delivery and claims checks pass. Browser rendering remains unverified under the prior policy restriction. Existing release archives retain their prior presentation. Evidence: `reports/observed_visits_2026_11_03/summary.json`, `scientific_preservation.json`, `javascript.log`, `static_web.json`, `socket_denied_runtime.json`, `baseline.json`.


## 31. Source publication preparation and repository hygiene — 4 November 2026

The user requested a hardened Git ignore policy, a judge-oriented README and publication to `mahdimahmud2006-coder/nasa101`. The user explicitly chose to keep the repository private. The README now leads with the persistence investigation, separates Bangladesh and Nepal, uses actual attributed radar composites, explains capability and scientific limits, and provides source/runtime setup and an expandable claim ledger. It retains AI disclosure and source licenses.

Git tracks source, configuration, provenance and curated documentation visuals. Acquired/raw products, generated raster/image payloads, environments, credentials, logs, temporary output and distribution archives are excluded. Previously tracked generated files are removed from the current index without deleting local files or rewriting historical commits. Secret guards follow metadata exceptions to prevent accidental re-inclusion. A repository audit checks the selected publication set for known credential patterns and large/local files; historical text was also scanned with scoped checks.

Processed runtime data is packaged separately as `runtime-20261104`: five content-deduplicated assets under GitHub's per-asset limit, with `config.runtime-assets.json` hashes and a safe standard-library installer. The core restores viewing, probing, Nepal coherence and scenarios; an optional native profile restores additional dual-polarization export rasters. No raw HDF5 or credentials are included. Private release downloads require authorized GitHub access. Existing local data and earlier archives remain on disk.

Verification before publication: 289 Python tests and 104 JavaScript tests pass, including 28 repository/runtime hygiene checks. Staged/tracked file audits and 315 historical text-blob checks report no matching credential findings; runtime core integrity, eight-page static checks, claim consistency and readiness pass. Rendered browser and clean judging-machine checks retain their prior pending scope. Publication confirmation will be recorded after the push and release upload. Evidence: `reports/publication_2026_11_04/prepublication_summary.json`, `staged_audit.json`, `tracked_audit.json`, `history_audit.json`, `hygiene_tests.log`, `python.log`, `javascript.log`, `runtime_verify.log`, `static_web.json`, `readiness.json`.


## 32. Visual README and judging walkthrough — 4 November 2026

The README now features four authentic scientific layer snapshots spanning Jamuna, Tanguar and Nepal, concise captions, a country-based judging tour and restrained navigation emojis. Two Nepal image copies join the existing Bangladesh composites; all four match their accepted source previews byte-for-byte. A snapshot provenance document records paths and SHA-256 hashes. Expandable sections present the existing terrain figure and explicitly identify the older Nepal interface capture as archival. The twenty-claim ledger remains unchanged. No new interface screenshot or browser acceptance is claimed. README local links, image references, claim consistency and repository hygiene were checked before pushing. The separate private runtime upload remains in progress during this documentation update.
