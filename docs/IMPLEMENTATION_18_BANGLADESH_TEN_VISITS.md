# Bangladesh ten-visit observation record

Implemented 3 November 2026. Active local record: `bangladesh-v2`. Plan task: **SCI-01**.

## Accepted input

Four completed NASA–ISRO NISAR GCOV HDF5 files in `database/new/`:

| Acquisition UTC | Series | Result |
|---|---|---|
| 2026-06-30 23:21:34 | Ascending track 069 / frame 014 | Accepted |
| 2026-07-12 23:21:34 | Same series | Accepted |
| 2026-09-10 23:21:31 | Same series | Accepted |
| 2026-10-04 23:21:32 | Same series | Accepted |

Actual headers match the original physical series: L2 GCOV, release P05023, product version 1.0.11, frequency-A HH/HV, 40 MHz bandwidth, L-band, left-looking and ascending. Input exception flags are zero; the products report nominal processing. File size and modification time were stable during the header read. Both crop extractions pass the established minimum valid-coverage requirement. Exact filenames, schemas, source-window processing metadata and declared auxiliary inputs are retained in `reports/bangladesh_import_2026_11_03/source_audit.json` and the new product manifests.

These files are NASA/ASF products (USA), from NASA–ISRO (USA/India). The declared DEM lineage names NASA/JPL, ESA/EU Copernicus, DLR and Airbus. No Chinese government or agency provider was identified in those declarations. This is a review of declared providers, not independent certification of every contributor to a global auxiliary dataset. No new external datasets were acquired during this implementation.

## Active capability

Both **Jamuna River Memory** and **Tanguar Wetland Pulse**, plus Bangladesh **Surface change**, use ten observed dates:

**June 18, June 30, July 12, July 24, August 17, August 29, September 10, September 22, October 4 and October 16, 2026.**

The June 18 reference is retained. The nominal August 5 slot is a documented satellite outage and remains unobserved. The record has **10 observations / 11 nominal slots**, with no remaining downloadable GCOV slot missing inside this displayed interval. The chart does not connect across the outage or interpolate an acquisition.

The version includes:

- HH/HV intensity, reference and adjacent-observation differences, and HH−HV ratio.
- Radar-dark transitions, paired brightening, valid visit counts and observed dark-signature fraction.
- Fixed-scale dual-polarization maps, CPR, false-colour composites, candidate signatures and cutoff sensitivity.
- Recomputed fixed-footprint Change DNA, sampled persistence/onset/recovery, competing explanations and native point/polygon inspection.
- Observation-aligned radiometric controls, histograms and rainfall request windows. Scientific rainfall values remain unavailable.
- Acquisition calendar, active homepage counts and exports identifying the record version, country and exploration focus.

Observed visit fraction is not continuous inundation duration. Candidate signatures remain uncalibrated and do not establish water, erosion, habitat condition or physical cause.

## Support and reference treatment

The original six canonical HH/HV COGs per crop are reused byte for byte, with their hashes checked. All four saved footprint masks per crop and their selection history are retained; the first-date/terrain-only putative-control masks are also unchanged.

After recomputing support across ten dates, all saved footprints retain exactly the same common-valid pixel counts. Whole-crop support remains **3,992,004 pixels at Jamuna** and **2,873,204 pixels at Tanguar**. Putative controls retain **489,210** and **329,104** common-valid pixels respectively. This supports direct comparison of the original-date baseline means on those footprints; adjacent-date differences now use the inserted visits where applicable. No calibration correction is applied.

The original optical comparisons remain tied to the exact same frozen footprint and radar endpoint COGs. Their observation identifiers are explicitly rebound by timestamp after verifying COG equality. Each added radar date has an explicit unavailable optical-reference entry for every frozen reference footprint. Earlier optical matches are never assigned to an inserted date. Frozen reference footprints have new ten-visit radar traces; this does not constitute new independent optical validation.

No additional GUNW, thermal, optical or scientific rainfall files were supplied in this batch. Nepal coherence and the original Nepal environmental tools retain their own inputs and scope.

## Version binding and preservation

`config.records.json` points the local API to `web/public/cases/investigations-bangladesh-v2.json` and the two new record directories:

- `web/public/cases/jamuna_river/bangladesh-v2/`
- `web/public/cases/tanguar_wetland/bangladesh-v2/`

Each contains the investigation, dual-polarization, context, evidence and reference sidecars, plus its calendar. Client asset paths and probing/reasoning endpoints resolve the same active record. Context chronology is checked before use to prevent a six-date sidecar being attached by array position to ten dates. Observation identifiers are timestamp-based.

The active pointer was published atomically after native validation. The historical registry, six-visit products, calendars and earlier claim snapshots remain available. The preservation check covers 505 historical Bangladesh/calendar files. The original scientific pipeline code hashes also match their historical records; the new record builders are separate modules.

## Verification and reproduction

- `make validate-bangladesh-record` reconciles fresh interior raw samples, native masks/formulas, occupancy, valid visit counts, controls, saved profile means, reference bindings, hashes and historical preservation.
- `make test-ui` covers active ten-visit bindings in all three Bangladesh focuses, actual-date playback, shared links and outage handling, alongside existing UI behavior.
- `.venv/bin/python -m pytest -q` runs the Python suite, including active-version resolution, stale-context rejection and local API behavior.
- `scripts/audit_phase7.py` checks delivery and representative reasoning with Python sockets and DNS forbidden, including the new active sidecars. This is not a physical Wi-Fi-disconnected browser rehearsal.

The original build is additive and refuses to overwrite a published version. `make bangladesh-record` is the initial builder, not a command to rerun over this published record. Future imports require a new version. Full-source rebuilding and native validation require the separately retained source HDF5 files; normal application viewing and probing use the local processed products.

Rendered browser verification remains pending under the previously recorded local-URL policy restriction. Existing release archives predate this import; a new submission archive has not been generated during the data import.
