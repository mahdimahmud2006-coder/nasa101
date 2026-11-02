# Implementation 09: Jamuna import and shared Tanguar Haor activation

**Completed: 31 October 2026.** The six user-downloaded science files in `database/bangladesh-shared/` now power both Bangladesh workspaces. The project remains TerraPulse. The two Nepal investigations and earlier analytical outputs were preserved.

## Open the results

Start `./run.sh`, then open:

- **River Memory / Jamuna:** http://127.0.0.1:8000/investigations.html?mode=river
- **Wetland Pulse / Tanguar Haor:** http://127.0.0.1:8000/investigations.html?mode=wetland

No separate haor download is needed for this six-date series. The original full scenes cover both crop windows; the crop is selected locally. Additional acquisitions on new compatible dates can extend the series, but duplicate files add no observations.

## What was checked

All six embedded granule IDs match their complete original filenames and the NASA Earthdata / ASF DAAC download plan. Each has actual frequency-A HHHH and HVHV datasets. Acquisition timestamps are distinct; product version is 1.0.11, release P05023, track 69/frame 14, ascending, 40 MHz. Both crops fall inside each raw grid. Files were stable in size/modification time during header inspection.

Full processing then checked per-channel canonical alignment, quality masks, valid looks, positive finite power and 3×3 validity-safe median processing. Invalid pixels remain missing. The saved native rasters, response areas, observation fractions, common-footprint traces and preview files passed output validation.

| Property | Jamuna / Sirajganj | Tanguar Haor |
|---|---|---|
| Geographic window center (lon, lat) | 89.71, 24.49 | 91.08, 25.10 |
| Window size | 20 × 20 km | 18 × 16 km |
| Native grid | 2000 × 2000 at 10 m | 1600 × 1800 at 10 m |
| Projection | EPSG:32646 | EPSG:32646 |
| Paired-valid coverage on each visit | 99.8001% | 99.7640% |
| Paired-valid area on each visit | 399.2004 km² | 287.3204 km² |
| Observed dates, 2026 | Jun 18; Jul 24; Aug 17; Aug 29; Sep 22; Oct 16 | Same six full-scene observations |

The small missing border is consistent with the strict median-filter neighborhood requirement. Native pixel spacing is not a claim of independent 10 m effective resolution. Six irregularly spaced observations do not establish daily inundation duration or a seasonal climatology.

## Available interactions

Both Bangladesh modes now show measured HH/HV observations, a shared-contrast date player, first/selected swipe, baseline and previous-visit differences, paired traces and evidence exports. River Memory provides dark-signature gains/losses relative to the first observation. Wetland Pulse provides dark/bright signature exploration. Both offer an observed-valid-visit fraction map.

A geographic study-window profile is available immediately. It uses the exact same paired-valid native pixels on all six dates; it is not a water or habitat reference. Broad spatial averages can hide opposing local responses. Click the map for a fixed 11×11-pixel local neighborhood and export its source-linked evidence dossier.

## Measured signature areas

These are **uncalibrated radar-dark candidate areas**, using the already configured HH ≤ −17 dB AND HV ≤ −24 dB rule. They are not confirmed water extents, riverbank erosion, flood damage, or wetland habitat loss.

| Date (UTC), 2026 | Jamuna dark-signature candidates, km² | Haor dark-signature candidates, km² |
|---|---:|---:|
| Jun 18 | 14.5269 | 138.1953 |
| Jul 24 | 23.3835 | 131.9424 |
| Aug 17 | 3.0202 | 45.5584 |
| Aug 29 | 14.0533 | 144.8115 |
| Sep 22 | 11.8774 | 132.4684 |
| Oct 16 | 10.1163 | 171.6872 |

The coverage denominator is constant within each case here, so these candidate-area comparisons are not caused by changing missingness. Physical interpretation remains unresolved: wind/roughness, moisture, vegetation/scattering, acquisition effects and actual surface transitions can affect the signals. Independent, date-matched optical or field evidence is needed before labeling these changes as water, erosion or habitat change. Existing Nepal rainfall, terrain and thermal layers are not reused as Bangladesh measurements.

## Rebuild just the intended case

```bash
make jamuna       # updates Jamuna; preserves all other saved cases
make wetland      # updates Tanguar Haor; preserves all other saved cases
make validate-investigations
```

Equivalent explicit command for both Bangladesh cases:

```bash
.venv/bin/python -m src.compute.investigation_pipeline --case jamuna_river --case tanguar_wetland
```

`make investigations` still rebuilds every configured case. The new selective build keeps unselected registry entries and files unchanged. Registry publication uses a completed temporary JSON replacement. Avoid viewing a case while its assets are being replaced.

## Verification and remaining work

- **189 Python tests and 37 JavaScript tests pass.** Two new Python tests check selective-build preservation and rejection of unknown cases. Controller tests now exercise real six-visit imports and direct River Memory links, while explicitly mocked pending-data states remain tested.
- All six analytical validation targets pass their stated scopes. The strengthened investigation validator independently reconstructs dark/bright areas, transition-area accounting and valid-visit fractions from saved native HH/HV rasters.
- All 508 earlier recorded analytical artifacts remain byte-identical. Neither Nepal case was rebuilt during this import.
- JavaScript UI checks use explicit DOM/canvas/image mocks. Real-browser visual/accessibility verification and a physically disconnected rehearsal remain pending under the previously recorded browser URL-policy block. No alternate browser route was used.
- The existing portable release archive predates this import and must be rebuilt before distributing updated results.

Evidence: [source audit](reports/bangladesh_2026_10_31/source_audit.json), [audit script](reports/bangladesh_2026_10_31/audit_sources.py), [saved-output validation](reports/bangladesh_2026_10_31/saved_outputs.json), [full verification log](reports/bangladesh_2026_10_31/verification.log). Routine `make validate-investigations` reports now go to `docs/reports/investigations_latest/` rather than overwriting the 28 October historical report.

The supplied files match the requested NASA/ASF source identifiers and recorded non-Chinese provider. No new external dataset was downloaded by the agent in this turn. This is source/provenance documentation, not a competition/legal eligibility certification.
