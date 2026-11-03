# Implementation 16 — experience and delivery

Phase 7, 3 November 2026, Asia/Dhaka. **Implementation delivered with real-browser, physical rehearsal and publication checks pending.** Phase 7 is not declared fully accepted while those checks remain open.

## Changes

The five original workspaces remain. A shared navigation rail, skip link and `investigation-state.mjs` preserve supported case/date/footprint/mode/layer state in readable URL hash parameters. Investigations restores saved footprints, point neighborhoods and assessed polygon geometry. Only actual dates are selected; absent dates produce a visible notice. Nepal-only tools are explicitly labeled and do not reinterpret a Bangladesh crop. Legacy workspaces preserve their supported date/layer/zone or pair state; unsupported cross-workspace layers are not treated as equivalent measurements. Legacy map/pair-specific probes retain their original export behavior.

Three Movements uses the existing preserved Nepal footprint for Detect and Persist, then opens real River Memory. Wetland Pulse is linked alongside it. Narration comes from the claim ledger; no numbers or scientific products are rebuilt. Buttons drive the current views. Scroll-driven changes are opt-in, and reduced-motion users retain buttons.

Investigations adds keyboard map cursor movement, Shift steps, Enter inspection/polygon vertices and Escape cancellation. Selected evidence is mirrored as live text. Shared focus/reduced-motion styles, labeled native controls and live legacy evidence/date regions improve access. Source checks cover four theme contrast pairs and form labels; these do not establish whole-app WCAG conformance.

The release packager now includes current runtime rules, claims, reference design, scripts and shared modules. It writes a new dated archive, refuses overwriting an existing release, excludes raw granules/credentials, and streams every entry against the package manifest before accepting the archive. The original distribution remains frozen. [Portable instructions](../RELEASE_README.md) distinguish runtime integrity from full-source scientific reproduction, dependency installation from offline use, and estimated hardware from verified performance.

[The three-minute storyboard](VIDEO_STORYBOARD.md) ties narration to ledger IDs. [The offline runbook](OFFLINE_REHEARSAL.md) describes the actual human rehearsal still required.

## Verification

Entry: 243 Python tests, 59 JavaScript tests and eleven analytical validators. New tests exercise hash state, exact dates and unsupported cases, legacy scoping, actual preserved story measurements, keyboard drawing/cancellation, current runtime packaging, archive tampering and real handler requests with sockets/DNS forbidden. The existing scientific validators and output freeze remain required. Final results are recorded in `reports/phase7_2026_11_03/`.

Automated offline evidence covers the backend and local source delivery. Real-browser visual/accessibility/GPU checks remain unverified under the recorded browser local-URL policy block; no workaround was used. All pending checks and failures must remain visible in [the browser checklist](reports/browser_a11y_2026-11-03.md). A physically disconnected rehearsal requires the user to actually turn off Wi-Fi/unplug Ethernet; neither source inspection nor `OFFLINE=1` establishes that result.

## Release and optional public copy

A static zero-install public copy is not implemented: current arbitrary footprint/scenario calculations require local APIs, and the local asset tree is several GiB. Publishing an incomplete static shell would break those behaviors. The local package remains the supported delivery. Raw-data licensing/source policy and all existing limitations stay attached. No upload, deployment, repository push or competition submission is implied.

The configured Git origin is inspected read-only for public link readiness. A successful public repository page, if verified, does not establish that this uncommitted local implementation is uploaded. No finished video link has been supplied. Actual public link results are in `reports/phase7_2026_11_03/public_link_status.json`.

IMERG, the August cause and interferometric science acceptance retain their prior explicit gaps. Phase 6 remains a completed gate report with coherence/LOS measurements planned. Remaining acceptance work is real-browser/accessibility/GPU testing, a physical disconnected rehearsal, clean judging-machine startup and public repository/video verification before submission.

Final automated verification passed **246 Python tests, 67 JavaScript tests and eleven analytical validators** with exit code 0; the release allowlist changes were additionally checked by the targeted release suite. All 795 frozen files and 508 historical analytical outputs remain unchanged. The dated archive uses `terrapulse-1.0.0-phase7-20261103-r2.zip`; its build/verification result, size and SHA-256 are retained in the separate release record and sidecar, not inferred from the source-test result.
