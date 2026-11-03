# Implementation 10 — Acquisition calendar and archive candidates

**Date:** 2 November 2026, Asia/Dhaka. Phase 1 of the user's master implementation plan. This extends the existing TerraPulse workspaces. Historical scientific outputs and their original baselines are preserved.

## 1. What changed

- `src/ingest/nisar_slots.py`: nominal 12-day calendars anchored to actual first-acquisition UTC times, with ±120-second matching for small acquisition-clock drift. Actual timestamps are retained separately from nominal timestamps.
- `scripts/nisar_slot_search.py`: search-only ASF client. Four crop-polygon searches, one for each case; candidates are deduplicated into two physical series. Records requested and effective polygons, retrieval time, provider, origin, license context, raw JSON checksum, size and rejection reasons. Explicitly checks ASF's `searchComplete`; failed/incomplete queries cannot prove absence. Existing snapshot directories cannot be overwritten.
- `config.time-axis.json`: crop polygons transformed from the existing native grids, series criteria and loaded observations. Two cases share each series. Configured ranges are explicit; this is a saved snapshot, not a live monitoring service.
- `scripts/publish_time_axis.py`: offline publication of verified metadata to the new `web/public/cases/time-axis-v1/` directory. Checks raw-response hashes and timestamps against each existing case manifest. Original manifests remain untouched.
- `web/time-axis.mjs` and `web/time-axis.css`: shared readable calendar, shaded gap span, hatched unloaded slots, textual status labels, actual acquisition times, source details and candidate downloads. Four investigation cases and the Nepal time-series page show it. A stale/missing calendar displays an explicit notice while saved radar maps still work.
- Investigation traces shade the gap and use dashed lines for long or gap-crossing intervals. Selected successive-difference maps and footprint readouts state the actual comparison interval. Playback still visits only actual observations. Exported dossiers include calendar provenance and the selected interval.
- The optional `requirements-search.txt` / `.venv-search` environment isolates `asf-search==14.1.0` from the scientific runtime. Running TerraPulse needs no new runtime dependency, credentials or network request.

Commands from the repository root:

```bash
./run.sh
# Open /investigations.html?mode=river or /timeseries.html in your usual browser.
make check-baseline

# Optional fresh archive search (metadata only, no raw download):
make setup-search
make search-slots SLOT_OUTPUT=data/candidates/my-new-search
```

`make search-slots` defaults to the completed snapshot and deliberately refuses replacement. Choose a new path for a new search. `make publish-time-axis` also refuses replacement of the published sidecar; future versions need a new destination and explicit UI pointer update. Update the series configuration from newly audited data before publishing a later calendar.

## 2. Verification

Before implementation, `make verify` passed: 189 Python tests, 37 JavaScript tests, six analytical validators, readiness and static page checks. Its generated timing report was saved under the new Phase 1 evidence directory and the historical report bytes restored.

New tests cover official-gap classification, observed/candidate/absent statuses, incomplete searches, clock drift, interval boundaries, conflicting observations, incompatible releases/configurations/bandwidth/polarizations/track/frame, partial crop coverage, actual saved query replay, checksums, no-download behavior and overwrite refusal. JavaScript tests cover all calendar labels, stale sidecars, clipping, case switching, selected-date interval notes, dashed traces and observed-only playback. Controller tests use explicitly mocked DOM/canvas/images; they do not establish browser rendering quality.

**Final verification passed: 207 Python tests, 42 JavaScript tests, all six analytical validators, readiness and static page checks. All 795 frozen files and all 508 historical analytical outputs match their recorded SHA-256 checksums.**

Final results and preservation checks are recorded in `reports/phase1_2026_11_02/summary.json` and `after/make_verify.log` after completion. `make verify` still writes historical reports, so use the phase preservation wrapper to retain fresh QA evidence and restore historical report bytes. Scientific changes must never be hidden or restored to mask a failed validator.

## 3. Data used and availability

| Source | Provider / upstream | Use | Provenance / license |
|---|---|---|---|
| Existing nine GCOV inputs and four saved manifests | NASA Earthdata / ASF DAAC (USA); NASA–ISRO (USA/India) | Real acquisition times, original grids and loaded dates | Phase 0 raw inventory; no new radar input |
| Official NISAR availability notice | ASF DAAC, University of Alaska Fairbanks (USA) | Confirm permanent instrument gap | `reports/phase1_2026_11_02/instrument_gap_source.json`: URL, retrieval timestamp, GET request and saved HTML checksum; cited factual notice, no separate documentation license asserted |
| ASF/CMR GCOV archive metadata | ASF DAAC / NASA Earthdata (USA); NASA–ISRO (USA/India) | Candidate availability and full-file sizes | `data/candidates/phase1_2026_11_02_final/`: four saved raw responses plus queries and SHA-256. NASA open-data policy context; DOI 10.5067/NIL2GCOV-P1 |

No Chinese provider, website or upstream agency supplied the new metadata. Only official ASF/NASA sources were used for the calendar and candidate records.

The official notice confirms **2026-07-27T22:03:25Z → 2026-08-10T00:55:27Z**. Source: [ASF NISAR availability guide](https://nisar-docs.asf.alaska.edu/availability-overview/).

| Series | Nominal slots | Loaded | Instrument gap | Compatible but unloaded | No compatible archive result |
|---|---:|---:|---:|---:|---:|
| Bangladesh 69/14 (both crops) | 11 | 6 | Aug 5 | Jun 30, Jul 12, Sep 10, Oct 4 | 0 |
| Nepal 98/16 (both crops) | 9 | 3 | Aug 7 | Jul 26, Sep 24, Oct 6, Oct 18 | Oct 30 |

The Nepal October 30 query returns a UR product, which fails the active PR/provisional configuration requirement. The calendar reports absence of a **compatible** candidate for this query and retrieval time, not permanent absence or absence of an acquisition. X05026 alternatives also remain incompatible with P05023. All rejected rows and reasons are retained.

Each Bangladesh case still has six real visits. Reusing a full scene for a second crop is not a second independent acquisition. Nominal slots never contain zero measurements or interpolated observations. A difference spans its two actual endpoints; exact onset inside that interval remains unknown.

ASF simplifies/reverses crop polygons during search; both the input polygon and effective search polygon are recorded. Screening uses the original densified native-grid polygon. Partial catalog overlap is allowed and its fraction recorded: geographic overlap is not valid-pixel support. Earlier exploratory screening snapshots (`phase1_2026_11_02` and `_v2`) remain diagnostic only; the **`_final` snapshot alone** feeds the UI. The first prototype required complete geometric coverage and was too strict for several already-loaded Nepal scenes; this was corrected before publication.

## 4. Claims and status tags

These report IDs are provisional identifiers for the later Phase 4 claim ledger; the ledger generator is still planned.

| ID | Status | Claim and limitation |
|---|---|---|
| P1-CALENDAR | implemented | Two nominal calendars cover all four cases; gaps, observed visits, unloaded visits and bounded archive absence have distinct text and styling. |
| P1-GAP | measured | Gap timestamps are confirmed against the saved official ASF notice; this is a documented mission fact, not TerraPulse measurement of a physical cause. |
| P1-ARCHIVE | measured | Completed recorded queries yielded eight additional catalog-compatible PR/P05023 candidates: four Bangladesh and four Nepal; actual headers and pixel quality remain unaudited. |
| P1-INTERVAL | implemented | Long or instrument-gap-crossing successive intervals are labeled in the investigation UI and dossier. Missing dates do not imply no change. |
| P1-INGEST | planned | Additional scenes can be ingested to new versioned destinations after explicit download approval and compatibility audit. |

No new surface-change cause, accuracy, water class, displacement, coherence, environmental context or polarimetric decomposition is claimed. The protected Nepal fixed-zone result remains unchanged.

## 5. Limitations and user decision

[Candidate approval sheet](PHASE1_DOWNLOAD_CANDIDATES.md) lists exact IDs, UTC times, sizes and official links. Bangladesh totals **25.0547 GiB**; Nepal **26.4297 GiB**; combined **51.4844 GiB** of full compressed HDF5 files. No radar download was made. These are catalog sizes, not measured transfer volumes. Subsequent processing needs additional disk space.

Prefer crop-window access if it preserves the required quality/header evidence. [ASF Harmony documentation](https://nisar-docs.asf.alaska.edu/harmony/) confirms variable extraction, not a guaranteed spatial subset or transfer budget. A feasible authenticated subset must be checked before assuming reduced transfer size. No Earthdata credentials were requested or used for metadata search.

Real-browser visual/accessibility/GPU checks remain unverified because of the prior browser URL-policy restriction. No alternative browser or automation bypass was attempted. A physical disconnected rehearsal and a refreshed portable release remain Phase 7 work. Existing startup and scientific results remain available.

## 6. Next phase

Await the user's go-ahead for Phase 2: diagonal-only HH/HV proxies, CPR, reproducible false-colour composites and carefully qualified mechanism hints. Phase 2 can use existing scenes if downloads are deferred. Download/ingestion remains gated separately by rule 15 and Phase 1 task 5 of the user's master prompt. No DpRVI or m–χ decomposition is supported by the active diagonal-only covariance inputs.
