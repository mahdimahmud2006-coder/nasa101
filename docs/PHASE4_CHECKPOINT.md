# TerraPulse — progress through Phase 4

2 November 2026, Asia/Dhaka. This checkpoint answers the request to finish through Phase 3, proceed with Phase 4, and report progress. It continues the existing TerraPulse project and preserves the earlier workspaces.

## Completed implementation

| Phase | Delivered | Qualification |
| --- | --- | --- |
| 0 — baseline | Repository orientation, source-schema audit and a 795-file SHA-256 freeze | The 508 historical analytical outputs are also checked separately. |
| 1 — time axis | Nominal acquisition calendars, official instrument-gap annotation, unloaded-visit markers, compatible archive candidate search and dossier provenance | Extra full radar acquisitions have not been downloaded or ingested. Missing observations remain missing. |
| 2 — dual polarization | Four-case CPR, fixed-stretch HH/HV composites, baseline/successive differences, candidate mechanism hints, footprint traces and threshold sensitivity | Inputs contain diagonal terms only; no covariance decomposition, coherence or ground displacement is claimed. |
| 3 — context and August pattern | Separate terrain for each crop, terrain derivatives, approximate geometry screening, frozen putative controls, full native Bangladesh source histograms and exact UTC rainfall windows | Scientific IMERG queries returned no matching granules for the requested dates. Rain totals are null. The August 17 cause remains unresolved. |
| 4 — investigation reasoning | Ten saved DNA footprints, native-pixel neighborhood and polygon analysis, six deterministic competing explanations, next-evidence fields, and a generated claims ledger | Explanations are uncalibrated fits, not probabilities or confirmed causes. Coherence remains null. |

Phase 3 uses NASADEM from NASA/JPL/USGS, distributed through Microsoft Planetary Computer for the small new geographic windows. Source queries, retrieval times, licensing policy and checksums are retained in `data/context/context-v2/`. No Chinese organization or site supplied accepted new datasets. Existing Nepal terrain is reused only for its own geography.

Phase 4 rules are in `rules/explanations.yaml`. The ledger is `claims/claims.yaml`; its current public snapshot is selected by `config.claims.json`. README claims, the in-app panel and the video checklist are generated from the same ledger. Runtime interpretation uses ordinary deterministic code and no LLM.

## Verification

| Checkpoint | Python tests | JavaScript tests | Analytical validators |
| --- | ---: | ---: | ---: |
| Phase 2 complete | 221 | 50 | 7 |
| Phase 3 complete | 225 | 51 | 8 |
| Phase 4 complete | 235 | 54 | 9 |

The full `make verify` command passed at each completed phase. Phase 4 evidence is in `reports/phase4_2026_11_02/summary.json` and `after/`. A fresh checkpoint run also passed with exit code 0 and is retained separately in `checkpoint/`, including its log and preservation report. All 1,315 preexisting output files covered by that run remain byte-identical; the separate baseline checks confirm all 795 frozen files and 508 historical analytical outputs unchanged. Existing validators that regenerate timing reports run against temporary backups; newly generated reports are retained separately and original historical bytes restored. No failed check is counted as passing.

The original Nepal 199-pixel footprint and prior scientific products remain intact. Tests include missing-data arithmetic, geometry masks, fixed control selection, explanation statuses, onset/persistence/recovery censoring, polygon rejection, socket-free API behavior, claim consistency and mocked UI interactions.

## Open scientific and release work

- IMERG measurements are unavailable; rainfall-based explanations cannot be tested yet.
- The August 17 pattern remains unresolved; putative control pixels are not independently verified calibration targets and no offset correction was applied.
- Thresholds and explanation rules remain uncalibrated. Observed-visit persistence does not establish continuity between acquisitions.
- Real-browser visual, accessibility and GPU checks remain unverified under the previously reported local-URL policy block. Controller tests use mocks. A physically disconnected rehearsal is pending.
- The portable archive predates these additions. Publication, competition submission and Phase 7 release work are not complete.

## Work staged beyond this checkpoint

Some Phase 5 preparation had already started under the earlier request to continue through Phase 6. The reference design and geographic comparison footprints were frozen in commit `889234019f4f3e2e919f63e5e791e69b511975bd` before new reference catalogs were examined. Small HLS optical windows have been acquired from NASA/USGS/ESA upstream through Microsoft; results are staged under `data/references/v1/hls-v2/`. Cloud and missing-data gaps are retained. These results are not yet integrated into application dossiers or accepted as completed Phase 5 validation. Their descriptive overlap is not classification accuracy or causal proof.

Phase 6 metadata searches are also staged under `data/candidates/interferometry_phase6_v1/`. Those are preliminary screening results: product-specific GUNW output polarization labels do not alone prove source-acquisition incompatibility, one archive search is incomplete, and feasible subsets have not been established. No interferometric files, coherence or displacement measurements were accepted. Phase 6 is not reported complete at this checkpoint.

## Open the updated project

From the repository directory, run `./run.sh`, then open `http://127.0.0.1:8000/investigations.html`. Restart an already-running server to load the new API handlers. Choose a case and saved footprint, inspect a map neighborhood, or use **Draw footprint** and **Inspect polygon**. The DNA, competing explanations, missing evidence, context and claims accompany the investigation and dossier export.

Detailed implementation reports: [Phase 3](IMPLEMENTATION_12_CONTEXT_BD.md), [Phase 4](IMPLEMENTATION_13_EXPLANATION_FIT.md). The project-wide history remains in [PROJECT_PROGRESS.md](../PROJECT_PROGRESS.md).
