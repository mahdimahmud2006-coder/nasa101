# Implementation 08: TerraPulse investigations, River Memory and Wetland Pulse

**Historical build snapshot.** The [31 October Bangladesh import](IMPLEMENTATION_09_BANGLADESH.md) subsequently activated both river and wetland modes using six actual observations. Statements below about awaiting data describe the initial build.

Built 28 October 2026. The project remains **TerraPulse**. This is the first shared investigation implementation; it preserves implementations 01–07 and their analytical artifacts.

## Available now

Run `./run.sh` and open **http://127.0.0.1:8000/investigations.html**. Evidence Studio also links to the new workspace.

- A three-workspace interface with case selection and clear data-readiness states.
- Two fully processed Nepal cases using the actual three existing HDF5 files: `nepal_surface` (original Kathmandu crop) and `nepal_impact_corridor` (new reference-aligned crop).
- Native 10 m HH/HV COGs; per-channel/window quality hashes and exact source granule IDs; shared per-channel display contrast across dates.
- HH and HV maps, HH−HV dB ratio, first-baseline and consecutive HH differences, first/selected visit swipe, discrete-date playback, and a full-series paired trace using actual elapsed time.
- Fixed 11×11 native-pixel neighborhood inspection on click or Enter at map center; common-valid pixels remain identical across dates/channels. A minimum 80% common-valid fraction is required for reported neighborhood means.
- Saved profiles for the existing 199-pixel tracked zone and the preliminary independently mapped footprint within the new corridor.
- Independent mapped-impact outline and provenance, competing-explanation panel, source/method dialog and evidence-dossier JSON export.
- Generic River Memory / Wetland Pulse processing and map controls, currently awaiting Bangladesh inputs. No proxy Nepal observations are presented as Bangladesh data.

The existing tracked zone reproduces HH baseline shifts near −7.5263 / −7.0766 dB and HV shifts near −1.8112 / −2.4510 dB. Its cause remains unresolved. The new crop intersects **6.4230 km²** of independent preliminary mapped impacts; the slight difference from the earlier illustrative 6.4192 km² window is due to snapping the crop onto the native radar grid. About 97.88% of the rasterized mapped footprint is common-valid across channels/visits. This permits a descriptive reference-footprint trace, not a claim of event classification accuracy.

The mean HH baseline shift across the common-valid mapped footprint is approximately −0.2019 dB on 31 August and −0.0212 dB on 12 September; HV shifts are approximately −0.7317 and −0.6606 dB. Do not transfer the original zone's roughly 7 dB shift onto the mapped event. A broad footprint average may conceal heterogeneous local responses; cause and detection validity require further investigation.

## How the river and wetland engines work

They use the same canonical HH/HV processing and actual observations as the surface investigation. Configuration is in `config.investigations.json`.

- A **radar-dark candidate** meets both HH ≤ −17 dB and HV ≤ −24 dB on paired-valid pixels. These are illustrative uncalibrated cutoffs, not a trained water classifier.
- River gain/loss/retained categories compare those dark signatures to the first observed baseline on baseline-common pixels. They do not establish riverbank migration or erosion.
- Wetland brightening requires at least +3 dB in **both** channels relative to baseline, on paired baseline-common pixels. It is not a validated flooded-vegetation class.
- Dark-signature observation fraction is `dark visits / paired-valid visits`, requiring at least two valid visits per pixel. It is a full-series retrospective map; it is not continuous inundation duration, hydroperiod in days, or a seasonal climatology.
- Saved outputs distinguish current-valid candidate areas from baseline-common transition areas. Missing values remain missing rather than dry/stable.

The hydrology build branches were tested end to end with explicit small synthetic HDF5 fixtures, including extraction, maps, native rasters, and occupancy under missingness. These fixtures remain in tests and are never used as application observations. Actual Bangladesh analyses await the downloaded files and subsequent quality checks.

## Download and import

[The full guide](DOWNLOAD_AND_IMPORT.md) gives exact science-file IDs, NASA/ASF links, locations, volumes and commands. A live NASA CMR query found ten same-named-mode/release acquisitions whose catalog footprints cover **both** Bangladesh sites. Six priority files total approximately 38 GiB. Both workspaces use `database/bangladesh-shared/`; no duplicate download is needed.

```bash
make investigations
make validate-investigations
./run.sh
```

The importer checks product, track/frame, orbit/look direction, product version, bandwidth, center frequency, polarization/dither metadata, processing release, timestamp uniqueness, grid extraction and minimum coverage. It requires at least three distinct compatible observations. Files must finish downloading before import. New extra Nepal dates may be placed in `database/nepal-series/`; original outputs are not overwritten.

Ingestion stages each new case before replacing its saved assets. Existing source datasets and older case outputs are preserved. Avoid viewing a case during a rebuild. Metadata/quality rejection is explicit; the importer does not fabricate missing maps.

## API and reproduction

- `GET /api/investigations` — registry, modules and case-readiness states.
- `GET /api/cases/{case_id}/investigation` — saved manifest with measurements and provenance.
- `GET /api/cases/{case_id}/investigation-probe?row=...&col=...` — fixed-neighborhood paired measurements.
- Public assets under `/cases/{case_id}/investigation/`.
- `make investigations` — additive rebuild from source HDF5.
- `make validate-investigations` — saved raster, profile, quality, asset and preservation checks.

`make verify` now includes this additional validation target. Startup preflight checks ready investigation-case assets while allowing the two Bangladesh cases to remain explicitly awaiting data. The existing portable archive predates this implementation; rebuild it before distributing an updated package.

## Verification and remaining work

Current validation logs are in `reports/investigations_2026_10_28/`. All 187 Python tests and 35 JavaScript tests pass. The six analytical validation targets pass their stated scopes, including preservation of all 508 previously recorded analytical artifacts. Mock controller tests exercise mode switching, real saved profiles, date/layer synchronization, and the reference-aligned case. They are not browser visual QA.

Still required: Bangladesh downloads and real-case processing; independent water/shoreline/habitat corroboration; stable comparison-area analysis; more Nepal dates; empirical classification validation if any classification claims are desired; direct browser visual/accessibility checks and a physically disconnected rehearsal. Browser access remains blocked by the prior URL policy; no alternate browser route was attempted.

NASA/ASF is the provider for the requested new files. Honor the user's non-Chinese-source requirement for supplemental data too; record provider, upstream provenance and license rather than inferring eligibility solely from a hosting domain.
