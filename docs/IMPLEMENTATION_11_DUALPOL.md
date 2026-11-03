# Implementation 11 — Diagonal-only dual-polarization evidence

**Date:** 2 November 2026, Asia/Dhaka. **Master-plan Phase 2.** Continues the original TerraPulse project and all prior workspaces. The nine existing NISAR inputs remain the complete raw acquisition inventory; no new radar file was downloaded.

## 1. What changed

All four cases now have an additive `dualpol-v1/` product directory beside their preserved `investigation/` directory. New numerical functions live in `src/compute/dualpol.py`; `dualpol_pipeline.py` reads the existing canonical HH/HV rasters without repeating or changing ingestion. It checks source grids and the saved raw-header covariance audit, records input/config/code/output hashes, stages the full build before publication and refuses to replace published products.

New products cover all 18 case-visits (nine unique acquisitions reused for the two crops in each physical series):

- Native CPR COGs and baseline/successive difference COGs for HH, HV and CPR. Signed changes use the paired-valid intersection of the two compared endpoints. The first visit has baseline zero only where valid and no preceding-visit difference.
- Native RGBA false-colour COGs and preview images with fixed, documented stretches, shared by every case and date.
- Native uncalibrated signature bit flags and separate, readable map views for low return, HH rise with stable HV, and HV rise. Flags can overlap; change hints are unavailable at the first visit.
- Fixed-footprint CPR traces and new `profiles.json` / `profiles.parquet`, retaining source observation IDs, UTC timestamps, common-valid support and the existing footprint selection.
- A two-dimensional 7×7 HH/HV cutoff grid per visit. The viewer offers three exact slices: vary HH, vary HV, or shift both together. The figure, visible count table, exported metadata and denominator describe the same crop-wide, all-visits common-valid footprint.

The investigation page adds a **“Read the relationship”** panel, CPR readouts and trace, crop-wide candidate hints, cutoff controls and expanded dossier exports. New fixed-scale maps are in the **View → Dual-pol** option group. Original layers and all five routes remain available. Optional missing/stale products show an explicit notice while the original investigation continues to work.

New shared files: `web/dualpol.mjs`, `web/dualpol.css`, `src/export/dualpol_render.py`, `config.dualpol.json`, `src/compute/validate_dualpol.py` and isolated scientific-figure renderer `scripts/render_dualpol_figures.py`. Registry: `web/public/cases/dualpol-v1.json`.

### Commands

```bash
./run.sh
# Open http://127.0.0.1:8000/investigations.html in your usual browser.
# Select a case, then use View → Dual-pol; the CPR/cutoff panel follows the date.
make validate-dualpol
make check-baseline
```

`make dualpol` is the reproducible **first-build** command. It deliberately fails if the published version already exists. For a subsequent build, copy the config, choose a new `product_version`, and run `.venv/bin/python -m src.compute.dualpol_pipeline --config <new-config.json>`; do not delete or overwrite the preserved products. The current UI and validator intentionally point to v1; publishing a new version requires an explicit pointer/config update.

The optional figure environment adds no dependency to app startup or `make verify`:

```bash
uv --cache-dir .uv-cache venv .venv-render --python .venv/bin/python
uv --cache-dir .uv-cache pip install --python .venv-render/bin/python -r requirements-render.txt
MPLCONFIGDIR=/tmp/terrapulse-mpl .venv-render/bin/python scripts/render_dualpol_figures.py --output reports/my-new-figure-export
```

The figure exporter also refuses to replace an existing destination. Scientific input values and scales are reproducible; encoded figure bytes may include renderer metadata. Saved QA exports are under `reports/phase2_2026_11_02/figures/`.

## 2. Calculations, masks and verification

### CPR and composite

The Phase 0 audit found **HHHH and HVHV only**, float32, in every active frequency-A/B grid. No off-diagonal terms are available. This selects the master prompt's proxy branch. No DpRVI, m–χ, interferometric coherence or displacement is computed.

`CPR_dB = HV_dB − HH_dB = 10 log10(HVHV / HHHH)` on the processed paired channels. The input dB fields were independently median-filtered in the existing pipeline; the ratio describes those filtered log-powers. It is the **sign reversal of the existing HH−HV layer**, not an independent observation. A footprint mean CPR is the mean of per-pixel log-power ratios on the same common-valid pixels, not the log of a ratio of spatially averaged powers.

False colour uses `R = HH`, `G = HV`, `B = HH−HV`, with fixed linear clipping:

| Component/view | Limits | Encoding |
|---|---|---|
| HH / red | −30 to 0 dB | Fixed linear stretch |
| HV / green | −40 to −5 dB | Fixed linear stretch |
| HH−HV / blue | 0 to 20 dB | Fixed linear stretch |
| Scalar CPR | −20 to 0 dB | Cividis |
| Every signed change | −8 to +8 dB | Crameri Vik, exact zero at normalized 0.5 |

RGBA alpha is paired validity; transparent pixels never become dark candidates. Native scalar COGs preserve values outside display limits. Per-layer saturation counts are saved and shown in the map note. RGB colours are a descriptive channel composite, not a perceptually uniform scalar scale or a land-cover legend; individual scalar views and numeric traces remain available. Existing historical renderings remain preserved; all newly introduced scalar maps follow the new palette policy.

### Candidate signatures

| Hint | Illustrative rule | Support |
|---|---|---|
| Low-return candidate | HH ≤ −17 AND HV ≤ −24 dB | Current paired-valid pixels |
| HH-rise / stable-HV candidate | ΔHH ≥ 3 AND abs(ΔHV) ≤ 1 dB from first visit | Paired-valid first/current intersection |
| HV-rise candidate | ΔHV ≥ 3 dB from first visit | Same endpoint intersection |

The HH/HV dark and 3 dB brightening settings remain unchanged. The 1 dB “stable HV” tolerance is a new, explicit **uncalibrated** descriptive setting. These are TerraPulse signatures, not a published mechanism retrieval algorithm or calibrated classes. A low return is consistent with smooth/specular surfaces, with shadow and dry smooth ground as alternatives; a bright HH response can be consistent with double-bounce-like geometry; HV can respond to depolarization and vegetation structure. Wetness, roughness, viewing geometry and radiometric effects remain alternatives. No probability, accuracy, winner, water classification or physical-cause attribution is inferred.

Bit flags: 1 low-return, 2 HH-rise/stable-HV, 4 HV-rise; 255 invalid. On the baseline only low-return is assessable; the manifest marks change hints unavailable. Zero flags on other visits mean none of these specific assessed signatures, not “no surface change.”

### Sensitivity design

Before examining references, the sweep is fixed at offsets −3, −2, −1, 0, +1, +2, +3 dB around the illustrative rule. Both cutoffs use inclusive ≤. All dates in a case use the **same paired-valid pixels across all observed visits**. The full 49-cell count matrix is saved; the three UI slices do not resample or tune thresholds. Missing support returns unavailable, not zero area. Sensitivity is not an uncertainty interval or an accuracy estimate.

These crop-wide sweep areas must not be confused with the original per-current-valid areas, the 199-pixel Nepal footprint, or the earlier centered-score alert areas. Static figure panels have separate km² ranges to show sensitivity within each case; they are not a shared-scale ranking of regions.

### Verification evidence

Before Phase 2, `make verify` passed **207 Python / 42 JavaScript tests**, six existing analytical validators, readiness and static checks. Fourteen new Python tests independently check ratio algebra/sign/missingness, known RGB values, invariant stretches, native RGB COG/alpha metadata, hint boundaries/overlap, exact inclusive sensitivity counts, fixed denominators, symmetric zero colour and overwrite refusal. Eight new JavaScript/controller tests check CPR, slices, legends, stale/missing extensions, dates, case/layer transitions and first-visit restrictions. Controller checks use explicitly mocked DOM/canvas/images, not a browser.

The new numerical validator independently checks every native pixel of CPR, RGB, difference masks/values and hint flags for all 18 case-visits, source/config/code/asset hashes and Parquet rows. Five independently recomputed cutoff cells per visit (90 total) verify production sensitivity counts; synthetic fixtures check the full matrix and monotonicity. **Final `make verify` passed: 221 Python tests, 50 JavaScript tests, all seven analytical validators (six preserved plus dual-pol), readiness and static checks. All 795 frozen files, 508 historical analytical outputs and 45 additional Phase 1 files remain unchanged.**

Final full-suite results and preservation counts are in `reports/phase2_2026_11_02/summary.json` and `after/make_verify.log`.

Static scientific figures were rendered with isolated Matplotlib 3.11.2 and visually inspected: all four cases, both RGB endpoint dates, the signed CPR maps and all sensitivity curves have visible marks, labels and scales. This is **figure QA only**. Browser layout, accessibility and GPU checks remain unverified under the prior URL-policy restriction; no alternate browser, headless automation or policy bypass was used.

## 3. Data actually used and provenance

| Input | Provider / upstream | Use and provenance |
|---|---|---|
| Nine previously loaded GCOV granules; 18 case-visits in four canonical crops | NASA Earthdata / ASF DAAC (USA), NASA–ISRO (USA/India), DOI 10.5067/NIL2GCOV-P1 | No raw acquisition added. Exact IDs/timestamps/version and diagonal terms remain in the Phase 0 raw inventory. Each new manifest records SHA-256 of every source canonical COG and original case manifest. |
| Cividis lookup table and license | Matplotlib project / cividis authors (USA); official Matplotlib repository | Source bytes, GET URL, retrieval UTC, source/license checksums and locally extracted numeric table under `data/palettes/v1/`. Matplotlib license retained. |
| Vik lookup table and license | Fabio Crameri Scientific colour maps; cmcrameri distribution, non-Chinese source | Officially documented map, distributed under retained cmcrameri MIT license. Source bytes, URL/retrieval UTC/checksum retained; cite DOI 10.5281/zenodo.1243862. |

`data/palettes/v1/provenance.json` records exact requests and retrieval metadata. `reports/phase2_2026_11_02/palette_file_hashes.json` additionally hashes all retained palette files. The validator verifies both upstream byte checksums and exact numeric extraction against the retained source. These lookup tables are software assets, not new Earth-observation measurements. No Chinese organization/site supplied new inputs. No unavailable radar or environmental dataset was fabricated; additional Phase 1 scene downloads remain pending approval.

Method references: [ASF GCOV documentation](https://nisar-docs.asf.alaska.edu/gcov/), [NASA NISAR polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/), [NASA/JPL imaging-radar explanation](https://airsar.jpl.nasa.gov/documents/genairsar/radar.html), and [Crameri scientific colour maps](https://www.fabiocrameri.ch/colourmaps/). These support measurement/visualization principles; **TerraPulse's signature thresholds are not validated by these references**.

## 4. New claims and status

These report IDs prepare for the Phase 4 ledger, which remains planned.

| ID | Status | Claim / evidence and limitation |
|---|---|---|
| P2-PROXIES | implemented | All four cases have CPR, fixed composites, endpoint differences, fixed-footprint traces and sensitivity views. Manifests and native COGs are in new paths. |
| P2-NUMERICS | measured | Saved values/masks/counts pass the independent numerical checks recorded in final verification. This establishes implementation arithmetic, not physical classification accuracy. |
| P2-NEPAL-CPR | measured | On the preserved 199-pixel Nepal zone, ΔCPR is +5.7152 dB on Aug 31 and +4.6256 dB on Sep 12, from the original fixed-support HH/HV differences. It summarizes the existing two channels rather than adding independent corroboration. |
| P2-MECHANISMS | hypothesized | Smooth/specular, double-bounce-like or vegetation-structure explanations are descriptive candidates with alternatives, never identified causes. |
| P2-EXPLANATION-FIT | planned | Context-backed competing explanations and the project-wide claim generator remain later phases. |

The original tracked-zone HH shifts remain **−7.5263 and −7.0766 dB**, with centered-score retained alert area **0.0199 → 0 km²**. Original nominal pair areas **0.0195 / 0.7949 / 0.0000 km²** still refer to a different rule. No previous result is relabelled, replaced or interpreted as ground displacement.

## 5. Limitations and decisions

The release still uses three Nepal and six Bangladesh dates. Nepal and Bangladesh remain separate track/frame series. A common valid footprint and matched acquisition geometry do not eliminate speckle, calibration, terrain or processing effects. False-colour changes and CPR do not establish a unique mechanism. Bangladesh terrain/rain/optical measurements have not been borrowed from Nepal and remain planned. The 17 August dip remains unresolved until the Phase 3 radiometric/context tests.

Additional scene ingestion still requires the separate decision in the [Phase 1 download sheet](PHASE1_DOWNLOAD_CANDIDATES.md). No large download is required to inspect this phase. The old portable archive remains frozen and predates these changes; Phase 7 must produce a new release artifact.

## 6. Recommended next phase

Phase 3: obtain separately sourced Bangladesh/Nepal-corridor terrain as needed, add scientific GPM IMERG V07 antecedent rainfall using actual UTC windows, freeze stable targets and investigate the 17 August Bangladesh pattern. Optional HLS remains cloud-aware. Follow provider restrictions and obtain approval for any large download. Stop at this phase boundary and await the user's go-ahead, as requested in the master prompt.
