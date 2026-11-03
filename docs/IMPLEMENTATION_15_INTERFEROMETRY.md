# Implementation 15 — gated interferometry track

Phase 6 Gate A, 3 November 2026, Asia/Dhaka.

The product-aware metadata screen, bounded access check, reviewed [gate report](INTERFEROMETRY_GATE.md), case-specific **Coherence & ground motion** panel and dossier gate section are implemented. All four investigations display the actual decision and missing checks. The screen uses both GUNW acquisition endpoints and rejects unobserved dates, mismatched series/releases and urgent-response products. It no longer mistakes the derived single-polarization GUNW output configuration for the source acquisition's dual-polarization configuration.

There are 13 metadata-eligible candidates: four GUNW pairs and nine GSLC scenes. NASA returned HTTP 401 to the unauthenticated bounded data check. No interferometric science subset has been accepted; source-header compatibility and feasible crop size remain unverified. One Bangladesh GUNW search is incomplete. Coherence and LOS displacement remain null/planned, with no synthetic substitute. Gate A is complete; its conditional scientific implementation is pending authenticated data access and validated subsets.

`TP-INTERFEROMETRY` stays **planned**, now pointing to the concrete gate report and distinguishing product existence from acceptance. A new `claims-phase6-v1` snapshot preserves earlier claim snapshots. The original GCOV measurements, thresholds, rules and analytical outputs remain intact.

Phase entry: 239 Python tests, 55 JavaScript tests and ten validators. Added checks cover derived-versus-source configuration, exact acquisition endpoints, track/direction/release/PR rejection, incomplete-search meaning, raw-catalog reconciliation, null science fields and the UI's explicit planned state. `make validate-interferometry-gate` checks the reviewed decision. Full final counts and preservation evidence are in `reports/phase6_2026_11_03/final/` and `summary.json`.

No large download, extra package, runtime network dependency or LLM was introduced. Browser visual/accessibility/GPU verification and disconnected rehearsal remain pending, and the portable release archive remains older than these additions. Phase 7 has not been started. Local app use remains `./run.sh`, then Investigations; select a case and inspect the new gate panel. Authentication is needed for future acquisition only, not to run the saved investigation.

Final full verification: **243 Python tests, 59 JavaScript tests, eleven analytical validators; exit code 0**. All 795 frozen files, 508 historical analytical outputs and 56 published Phase 5 artifacts remain unchanged. The final wrapper preserved all 1,374 preexisting output files in its scope, retaining new timing QA separately. A regression test verifies that a delayed reference fetch cannot overwrite a newly selected case.
