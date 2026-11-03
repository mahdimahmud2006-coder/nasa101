# Implementation 14 — frozen independent reference comparisons

Phase 5, 3 November 2026, Asia/Dhaka.

The evaluation design and twelve footprints were frozen in commit `889234019f4f3e2e919f63e5e791e69b511975bd` before new reference catalogs or imagery were examined. Each case has a geographic target, a putative stable comparison and an unmapped comparison. The last two labels are sampling roles, not independently verified truth. Earlier UN impact-map exposure and radar/DEM-based selection are disclosed in the frozen design. This is a prospective **descriptive** comparison, not blinded event classification.

## What changed

`src/compute/reference_pipeline.py` publishes new `references-v1/` bundles for all four cases. Twelve additional saved footprint DNA profiles are computed from existing native radar data; the original ten profiles and scientific outputs are preserved. Choose a **Frozen reference** footprint in Investigations. The Independent reference panel follows the selected footprint and actual radar visit, displays eligible optical imagery and measured overlap areas, and retains cloud gaps. Arbitrary clicks/polygons do not inherit a nearby reference result. Dossier exports carry the selected reference status, scope, source identifiers and frozen-design hash.

`TP-REFERENCE` is now measured, limited to these descriptive results. The ledger generates README/app/video claims in the new `claims-phase5-v1` snapshot, preserving older public snapshots. Runtime remains local and deterministic.

## Accepted data and sources

| Data | Provider / upstream | Access and licensing |
| --- | --- | --- |
| Small HLS L30/S30 RGB and Fmask windows | Microsoft Planetary Computer, USA; NASA/USGS Landsat and NASA HLS / ESA Sentinel-2 upstream | 204 native band windows, 338,167 saved bytes, no full tiles. NASA/LP DAAC policy and citation link recorded. STAC's `proprietary` license field is retained and is not relabeled CC0. |
| Existing radar windows | NASA/ASF; NASA–ISRO, USA/India | Existing accepted GCOV only; no new radar download. |
| OPERA DSWx-S1, DSWx-HLS, DIST | NASA CMR catalog metadata | Candidates screened, but no OPERA scientific raster is accepted in this version. A successful access probe is not a scientific reference result. |

Every accepted band window has an unsigned source URL, retrieval UTC, geographic query, provider/upstream, licensing policy, saved size and SHA-256 in `data/references/v1/hls-v2/sources.json`. No Chinese organization/site supplied these accepted datasets. Acquisition scripts obtain official Microsoft SAS tokens in memory; app previews use local thumbnails and require no credentials.

Primary method/policy sources: [NASA HLS QA/data products](https://hls.gsfc.nasa.gov/data-products/), [NASA HLS algorithms](https://hls.gsfc.nasa.gov/algorithms/), [LP DAAC data policy](https://lpdaac.usgs.gov/data/data-citation-and-policies/). HLS Fmask water is an algorithmic optical label; it is not OPERA DSWx or ground truth. Cloud, adjacency, shadow, snow and low-bit cirrus/reserved flags are excluded; aerosol bits are not separately excluded. Water is bit 5. Fill and missing reflectance/radar cells are excluded.

## Design and outcomes

The closest fully covering HLS catalog item within the predeclared five-day tolerance is chosen, breaking ties by cloud metadata and identifier before reading pixel values. A cloudy closest scene is retained as unavailable rather than replaced after inspecting outcomes. No footprint, radar cutoff or explanation rule is tuned. Disclosed spatial tolerance is 30 m; overlap receives no buffer. Reference-cell centers are included and nearest-grid HH/HV values use the fixed dark threshold. Area denominators are only assessable reference pixels; radar DNA means use their separate native grid.

| Case | Comparisons | With eligible optical pixels | Unavailable |
| --- | ---: | ---: | ---: |
| Nepal surface | 9 | 2 | 7 |
| Nepal corridor | 9 | 0 | 9 |
| Jamuna | 18 | 5 | 13 |
| Tanguar | 18 | 7 | 11 |

For the Jamuna geographic target at the August 29 radar visit, optical-assessable area and optical-water area both equal 0.7875 km², while the radar-dark intersection is only 0.0036 km². At October 16 the intersection is zero across 0.6903 km² of eligible optical-water area. Tanguar's August 29 target has 0.9801 km² assessable, 0.8748 km² optical water and 0.6372 km² intersection; its October 16 intersection is 0.4068 km². These are intentionally mixed results, restricted to selected pixels and nearby optical times, not water-classification accuracy or evidence of physical cause. The interface and exported record include each exact optical timestamp and absolute time difference.

## Verification and limitations

Phase entry: 235 Python tests, 54 JavaScript tests, nine analytical validators. New tests check tolerance boundaries, deterministic ties, QA bits, zero versus missing, frozen hashes, all 54 outcomes, and reference scope across UI selections/dates. `make validate-references` independently reconciles saved QA, reflectance eligibility, geographic masks, source hashes, chosen catalog items and all reported area counts. Full phase results and artifact-preservation evidence are in `reports/phase5_2026_11_03/after/` and `summary.json`.

No precision, recall, IoU, calibrated confidence, causal corroboration or independent stable-target truth is claimed. The Nepal target/corridor have no eligible date-matched optical evidence here. Browser visual/accessibility/GPU checks remain unverified; controller tests are explicit mocks. OPERA raster comparison remains a possible later extension. Phase 5's completion condition is met by actual date-matched descriptive comparisons, including negative/mixed outcomes. Next: Phase 6 Gate A only until compatibility, access and feasible subsets can be established.

Final Phase 5 verification: **239 Python tests, 55 JavaScript tests and ten analytical validators passed**; all baseline outputs preserved. [Inspected scientific reference figure](../reports/phase5_2026_11_03/figures/frozen_optical_checks.png) compares the frozen Bangladesh target chips and their descriptive areas; this is not an application screenshot or browser QA.
