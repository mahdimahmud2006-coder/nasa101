# TerraPulse implementation plan

Planning baseline: 7 November 2026. Revised against the follow-up *TerraPulse Implementation Plan: Problems Found*. [Parts 1–3 are implemented and verified](../reports/development/parts-01-03-handoff.md). [Parts 4 and 6 are implemented and verified](../reports/development/parts-04-06-handoff.md). Part 5 is implemented with open browser zoom and assistive-technology acceptance checks. [Part 7 is implemented and verified](../reports/development/part-07-handoff.md). [Parts 8–10 are implemented with data and method gates](../reports/development/parts-08-10-handoff.md).

The [evaluation follow-through](EVALUATION_FOLLOW_THROUGH.md), [improvement tracker](PRODUCT_IMPROVEMENT_TRACKER.json), and [earlier development plan](PRODUCT_IMPROVEMENT_PLAN.md) record the starting point. **Research** below refers to the user-supplied *TerraPulse Space Apps Evaluation.md*, cited by section title. The evaluation identifies product and scientific gaps; its proposed algorithms, scores and assumptions are hypotheses to test, not acceptance evidence.

The starting product has four study windows, ten recorded visits per country series, a portable atlas, local native probes, preliminary explanations, two Nepal coherence pairs, and limited environmental context. Preserve that working baseline. No Part may silently replace an accepted observation, add a synthetic acquisition, reinterpret an uncalibrated score as a probability, or treat the same acquisition cropped twice as independent evidence.

**Event path.** Use the event cuts below. The [official 2026 NASA Space Apps timeline](https://www.spaceappschallenge.org/2026/) lists November 14–15; verify the actual local event hours, submission deadline, format, and eligibility of pre-existing TerraPulse work first. An [official-platform local-event page](https://www.spaceappschallenge.org/2026/local-events/santiago-dominican-republic/) distinguishes permitted preparation from building the competition entry. That page is not a Bangladesh ruling. Treat November 7–13 as a preparation window unless the applicable organizers confirm what additional work is allowed. Keep and disclose the true work history. If eligibility is unresolved, do not submit the project as eligible.

| When | Event scope and Parts | Time box and stop rule |
| --- | --- | --- |
| Nov 7–13, within allowed preparation | Confirm event/reuse rules; inventory accepted inputs; identify an authorized static host; prepare the storyboard, claims list and device checklist. | 2–4 hours plus organizer/host response time. No dependency on fresh downloads or a new runtime. |
| At the confirmed permitted start | Light baseline (1), minimal state contract (2), audit only inputs actually used (3). | 2–3 hours. Freeze the saved footprints, dates and claim list. Defer unrelated data discovery. |
| First build block | Single-workspace tour (4), headline persistence and hypothesis evidence (7), existing dated context (8), saved-footprint export/reopen (16). | 6–8 hours. Reuse the current atlas controller and measurements; skip a broad rewrite. A draft tour and recording shot list are ready in this block. |
| First review block | Focused desktop/phone/keyboard/DOM parity checks (5); build and verify the static bundle (17). | 4–6 hours. Fix blocked journeys and misleading states first; no new scientific layers. Run these checks alongside story/caption review once the selected cases are frozen. |
| As soon as a reviewed static artifact is ready | Obtain deployment authorization, deploy the approved static artifact, verify the live link logged out and on a phone (17). | 2–3 hours of work, excluding access and approval delays. Aim to pass by six hours before the verified submission cutoff. Keep the last known-good deployment and portable HTML ready. |
| Final six hours before the verified cutoff | Freeze, record the continuous workflow, verify links and prepare the submission package (19). | 3–4 hours, reserving the remainder for fixes. Cut optional visuals before cutting playback, export, accessibility of the core journey, or live-link verification. |

These are planning estimates, not observed completion times. The event cut is **1 → 2/3 → 4 → 7/8/16 → 5/17 → 19**; design/story review, source verification and hosting preparation can run independently after the baseline. Native geometry expansion (6), new data backfill (8), advanced science/application work (9–15), hosted native streaming (17), and the full user pilot (18) move to post-event. Keep the existing exploratory river/wetland chapters. Drop a missing science layer from the event scope as soon as its inputs fail the gate. If the live URL cannot be approved or verified by the freeze, report the hosted gate as blocked; the offline HTML and recording are fallback review material, and count for submission only if the applicable rules allow them.

**Event acceptance checklist.** Verify these bounded outcomes to use `EVENT_ACCEPTED`. Keep omitted full-scope criteria unchecked. Within the first build block, Parts 7 and 8 can proceed independently once Part 4's selection is stable; Part 16 comes after both.

| Event cut | Required evidence before advancing |
| --- | --- |
| Parts 1–3 | One baseline receipt, known results for the guided cases, a case/date/footprint round-trip and an allowlist tying every deployed data asset to its version and redistribution review. |
| Parts 4 and 7 | Three same-workspace chapters, each selecting the correct real data; the Kathmandu recent/reference values match the baseline; evidence rows and next check stay aligned with the selected footprint. Verify missing rows and the keyboard Next/Back flow. |
| Part 8 | Verify one supported Kathmandu date, one Kathmandu date with missing context, and a Bangladesh date; inspect actual source dates, labels and scenario scope. |
| Part 16 | Export and reopen a saved Bangladesh and a saved Nepal selection in fresh sessions; compare IDs and values; reject a mismatched version without silently substituting inputs. |
| Part 5 | Complete the guided flow on desktop and phone, keyboard and reduced motion. Check visible focus, legend/contrast and DOM parity, including an unavailable value. |
| Part 17 | Checksummed approved bundle, authorized live URL, logged-out desktop/phone results, cold-load traces, and disconnected offline fallback. The public link is required for hosted acceptance. |
| Part 19 | Checked claims, current format and eligibility, verified release links and one continuous walkthrough. Reserve final submission for a separately authorized action. |

**Full product path.** After the event cut, follow the numbered Parts and their dependencies to finish the full runtime, independent validation and user pilot. Part 12 remains optional. An event acceptance does not close the full Part.

**Release scope.** The first complete release can use the supported exploratory River Memory and Wetland Pulse workflows, descriptive coherence and existing dated context. Publish stronger claims only after their independent validation. For Parts 11, 14 and 15, build and verify the descriptive workflow first, register its validation protocol in Part 13 before tuning, then return for the optional validated layer. This avoids making the base workflow and validation wait on each other.

**Gate rule.** Mark a Part `ACCEPTED` only when all of its applicable acceptance boxes have evidence. Use `EVENT_ACCEPTED` for a verified event cut with the unfulfilled full-scope checks listed separately. Record `WAITING_DATA`, `WAITING_VALIDATION` or `BLOCKED` when needed; record a narrowed scope or deferred extension explicitly. A test plan, metadata listing, or successful fixture test does not prove real inputs, rendered usability or measured impact. At each handoff, record the exact revision/input versions, artifacts, verification commands, observed results, unresolved items and the next eligible Part. For the event cut, use one short shared handoff log: Part/scope, revision and data version, checks and actual outcomes, unresolved items, next eligible Part. Reuse evidence across Parts rather than producing duplicate reports. Part 17 explicitly includes deploying the inspected static bundle after authorization; that does not authorize publishing the repository, raw data or backend. Submission is a separate action.

| Part | Deliverable | Likely external dependency |
| --- | --- | --- |
| [1](#part-1-freeze-the-baseline-and-confirm-the-gaps) | Verified baseline and gap register | None for source/runtime audit |
| [2](#part-2-define-the-investigation-state-and-evidence-contracts) | Versioned investigation contract | None |
| [3](#part-3-audit-inputs-and-stage-only-the-data-the-science-needs) | Accepted data inventory and acquisition queue | Archive access for additional products |
| [4](#part-4-consolidate-the-core-tools-into-one-workspace) | Unified investigation workspace | None for implementation |
| [5](#part-5-finish-responsive-design-and-verify-accessibility-in-a-browser) | Real browser and accessibility acceptance | Permitted browser and test devices |
| [6](#part-6-complete-native-spatial-inspection-and-map-comparison) | Native spatial selection and comparable maps | Accepted native rasters |
| [7](#part-7-separate-recent-change-persistent-difference-and-recovery) | Temporal measurements and change interpretation | Accepted visit series |
| [8](#part-8-integrate-dated-environmental-context-and-scenarios) | Date-bound context and scenario workflow | Additional context where available |
| [9](#part-9-add-terrain-and-radiometric-quality-gates) | Terrain and radiometric quality gates | Suitable DEM, drainage and product QA |
| [10](#part-10-improve-dual-polarization-analysis-within-the-available-channels) | Dual-pol analysis and descriptor evaluation | Channel-compatible inputs |
| [11](#part-11-expand-coherence-and-gate-any-damage-proxy-product) | Coherence analysis and conditional damage-proxy study | Matched GUNW pairs and independent evidence |
| [12](#part-12-evaluate-displacement-as-an-optional-research-extension) | Optional displacement research | Suitable phase stack and independent controls |
| [13](#part-13-validate-against-independent-evidence-and-report-area-honestly) | Held-out scientific validation and area reporting | Independent references and review |
| [14](#part-14-turn-river-memory-into-a-bank-review-workflow) | River Memory decision workflow | Validated banks for migration claims |
| [15](#part-15-turn-wetland-pulse-into-a-repeat-visit-review-workflow) | Wetland Pulse decision workflow | Suitable water/habitat references |
| [16](#part-16-make-evidence-exports-reopenable-and-reviewable) | Reproducible evidence dossier | None for local export and replay |
| [17](#part-17-build-and-verify-a-live-zero-install-demo) | Live demo, offline fallback and optional native delivery | Hosting only if separately authorized |
| [18](#part-18-run-a-real-user-pilot-and-fix-the-workflow) | User pilot and workflow revisions | Real participants |
| [19](#part-19-freeze-the-release-and-verify-submission-readiness) | Release and submission readiness | Current rules, eligibility, access and authorization |

# Part 1: Freeze the Baseline and Confirm the Gaps

## Problem
Research, “Executive Diagnosis” and “Eight-Route Fragmentation Problem,” describes an earlier snapshot. Some remedies now exist in the atlas, while native delivery, real-browser acceptance and scientific validation remain unfinished. Counting all reported flaws as current would cause rework.

## Goal
Produce a reproducible starting snapshot and a verified backlog against which every later Part can be reviewed.

## Acceptance Criteria
- [x] A baseline receipt identifies the Git revision, working-tree changes, active case registry, source manifests, runtime edition and portable artifact digest.
- [x] Each research finding maps to observed behavior, a code/data location, a status and a numbered Part.
- [x] Saved example links and expected outputs are recorded for all four windows, including one native probe, one Nepal pair, one optical match and one known unavailable input.
- [x] Test failures and unrun browser checks are listed with their actual status.

## Constraints & Assumptions
- Event cut: one baseline receipt, saved examples and a short confirmed-gap list. Defer a full inventory of legacy screens.
- Preserve current uncommitted work and accepted historical artifacts. Do not freeze by committing, resetting or rebuilding over existing outputs.
- Source checks, controller rehearsals and browser verification are separate evidence types.

## Implementation Steps
1. Read `config.records.json`, the atlas builder and current API/route definitions. Inventory observations, scopes, support, versions and existing outputs.
2. Run current checks and preserve logs outside scientific output directories. If a legacy verifier rewrites incidental timing metadata, isolate that side effect.
3. Produce `reports/development/part-01-baseline.md` and a compact machine-readable receipt. For each finding distinguish missing, partly implemented, implemented but unverified, and scientifically blocked.
4. Record reproducible fixtures and nominate the first user journey: select a case, compare visits on one footprint, read the dated evidence, export.

## Dependencies
- Requires: none.
- External assumptions: local checkout and installed baseline dependencies; browser access is needed only to classify rendered checks as observed.

## Verification
1. Run `git status --short`, `make verify`, and `.venv/bin/python scripts/generate_claims.py --check`; record exits and scope.
2. Run `make atlas-portable` followed by `node scripts/verify_portable_atlas.mjs`; compare the generated digest to the receipt.
3. Check that each cited file or active manifest exists and all research findings have a destination. Review the example outputs before accepting the baseline.

# Part 2: Define the Investigation State and Evidence Contracts

## Problem
Research, “Eight-Route Fragmentation Problem,” identifies route-specific state and incompatible records. The current atlas still couples multiple controls to one large controller, and not all legacy views or exports represent selection the same way.

## Goal
Define one versioned contract for selecting, measuring, sharing and restoring an investigation across editions.

## Acceptance Criteria
- [x] A case manifest identifies record version, grid, observations, pair intervals, context sources and capabilities by stable IDs.
- [x] State round-trips case, layer, reference/current observations, footprint and applicable context without changing meaning.
- [x] Mismatched case, grid, observation, or footprint IDs fail with an explicit reason; old links have a documented migration path.
- [x] Missing, out-of-scope, invalid and zero values have distinct representations.

## Constraints & Assumptions
- Event cut: preserve the current saved-footprint state, add only the IDs/version fields required to share and restore it, and test the release examples. Defer the wider legacy/API migration.
- Use actual UTC timestamps, immutable observation IDs and explicit dataset versions. A date label alone is not a join key.
- Maintain compatibility adapters for existing links and results; do not repurpose an ID for different input data.

## Implementation Steps
1. Define schemas in a dedicated contract directory. Model view state as `{schemaVersion, caseId, recordVersion, currentId, referenceId, layerId, footprint, contextSelections}`; represent a coherence layer with `pairId` and both endpoints.
2. Give footprints an explicit type (saved, native point, polygon), coordinate reference, grid identity and sampling rule. Separate product geometry from display coordinates.
3. Specify result fields: quantity, units, source IDs, mask/support, status, method and permitted interpretation. Use a typed status plus null for unavailable measurement.
4. Implement adapters from the active atlas record, local endpoints and legacy URL formats. Keep schema migration isolated from rendering.

## Dependencies
- Requires: Part 1.
- External assumptions: none.

## Verification
1. Test round trips for all four windows and a legacy URL, including an independent thermal selection and paired radar view.
2. Reject a foreign-case date, unknown record version and stale footprint using negative fixtures. Confirm a valid measured zero survives serialization.
3. Re-run atlas controller and link checks; compare the baseline examples from Part 1.

# Part 3: Audit Inputs and Stage Only the Data the Science Needs

## Problem
Research, “Critical Gaps in the Current Science Implementation,” identifies missing rainfall, compatible interferometry and reference coverage. Archive listings, downloads and scientifically accepted records are different states.

## Goal
Produce a per-case inventory and prioritized, actionable acquisition queue. Feed only accepted inputs to downstream builders.

## Acceptance Criteria
- [x] Every current and candidate product has a case/date or pair binding, source ID, provider and upstream lineage, expected size, validation status and reason.
- [x] Candidate data needed by Parts 8–15 are ranked by the question they unlock and have exact spatial, temporal and product requirements.
- [x] The rainfall queue accounts for all 20 distinct recorded country-series visits and all four footprints; it records which IMERG windows are covered, unavailable, or excluded by lineage.
- [x] The known unavailable August slots and incompatible products are represented as unavailable in the inventory.
- [x] Rejected inputs cannot enter the active registry; accepted updates require a new version and validation report.

## Constraints & Assumptions
- Event cut: audit the already accepted records and redistribution rights for the release bundle. New rainfall or reference acquisition stays off the critical path.
- Honor the user's provider and upstream lineage restrictions. NASA hosting alone is insufficient for a merged product.
- Check free space before downloading or processing; preserve raw inputs. Do not download a listed product merely to complete a count.
- Existing observations are usable for the core workflow while extra data are pending.

## Implementation Steps
1. Inventory current GCOV, GUNW, DEM, POWER, optical/thermal and reference records; inspect actual headers, footprints and QA where present.
2. For each missing capability list required dates, ROI, band/channel, track/frame/look, product version, compatible grid, QA requirements and reference purpose.
3. Validate sizes/hashes, lineage, geometry, timestamps, masks and coverage before acceptance. Record `listed → downloaded → audited → accepted/rejected`.
4. Evaluate [NASA GES DISC GPM IMERG Final half-hourly V07 (GPM_3IMERGHH 07)](https://disc.gsfc.nasa.gov/datasets?keywords=GPM_3IMERGHH_07&page=1) for the trailing 48-hour windows ending at each recorded acquisition time. Use [earthaccess catalog search](https://earthaccess.readthedocs.io/en/latest/user/howto/search-granules/) to verify actual run/version, coverage and native HDF5 availability before downloading. Deduplicate overlapping bins across visits and footprints. Check the [V07 algorithm and input documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-atbd) plus per-granule input lineage against the user's restriction. Do not assume a NASA-distributed blend qualifies; if Final is unavailable, assess any other run separately and do not silently mix them.
5. Create a download shortlist for user-provided data, separated from candidates that need catalog discovery or permission. Bind accepted files to a new version; retain historic inputs.

## Dependencies
- Requires: Parts 1 and 2.
- External assumptions: catalog access, credentials, storage and new downloads only for the extra inputs being considered.

## Verification
1. Trace one accepted input per active case to its manifest, and one GUNW pair to both endpoint identities.
2. Try a wrong track, incomplete file, unknown upstream lineage and out-of-coverage reference; confirm rejection with a reason.
3. Audit the 20-visit rainfall coverage table against actual UTC intervals and source/run metadata. Leave unapproved or unverifiable lineage excluded, even if a catalog result exists.
4. Cross-check the shortlist against current coverage and the documented outage. Confirm no missing nominal visit is labeled acquired.

# Part 4: Consolidate the Core Tools into One Workspace

## Problem
Research, “Eight-Route Fragmentation Problem,” calls for one investigation loop. The atlas is now the main entry, but advanced tools still rely on separate screens and controller logic is hard to extend.

## Goal
Complete the common investigation flow in one workspace, with clear access to any specialist tools that remain separate.

## Acceptance Criteria
- [x] Users can choose a window, layer and dates; inspect a footprint; review context; and reach export without navigating to another page.
- [x] Both country groups, River Memory, Wetland Pulse and Surface Change are discoverable from the same entry.
- [x] A guided tour in the same canvas selects actual Jamuna, Tanguar and Nepal examples, updates map/timeline/evidence together, and supports Next/Back and exit without scroll trapping.
- [x] A lightweight Field Guide is reachable from the current observation. “Analyze in Python” offers a tested downloadable notebook with a redistributable sample and a clearly optional ASF OpenSARLab link.
- [x] The timeline, map, profile and inspector consume one validated selection; changing cases cannot briefly show stale results from the last case.
- [x] Supported legacy links open their intended view or a clearly documented equivalent.

## Constraints & Assumptions
- Event cut: extend the existing guided selections with three short chapters, the core evidence panels and contextual guide. Defer a broad module rewrite, automatic scroll-linked animation, and notebook hosting if they threaten the release. A button-driven tour must remain usable with reduced motion.
- Reuse accepted science, URLs and the offline edition. A frontend framework migration is optional and requires a demonstrated need.
- Detailed scenario computation and specialist tools may be linked when their data or methods do not fit the shared view.

## Implementation Steps
1. Split `web/atlas.mjs` by responsibility: state, data access, map, timeline, context and inspector. Keep the existing public entry point.
2. Model changes as atomic state transitions. Cancel or discard stale loads when case, footprint or date changes.
3. Define a capability matrix per case and edition. Use it to enable controls and explain why an unavailable tool cannot run.
4. Add a VEDA-inspired guided tour driven by explicit case/date/footprint IDs. Each chapter has a question, a measured answer and a next check. Keep it within the same canvas and make scrolling optional. In the full Part, add opt-in scroll-synchronized chapters with the same state transitions as the buttons. Fold the relevant Field Guide content into the inspector.
5. Add an “Analyze in Python” notebook that reopens a small approved dossier and recomputes one statistic. Link the [ASF OpenSARLab access guide](https://opensarlab-docs.asf.alaska.edu/user-guides/opensarlab/) for eligible researchers; access requires separate approval. Do not make account access part of the demo journey.
6. Bring comparison, time-series and scenario entry controls into the shared shell. Migrate legacy links with an adapter and preserve the direct tools where needed.

## Dependencies
- Requires: Part 2; uses available records inventoried in Part 3.
- External assumptions: none for controller implementation.

## Verification
1. Run `make test-ui` and `.venv/bin/python scripts/check_web.py`.
2. Exercise all four windows and back/forward navigation; switch cases while a probe is loading and confirm the previous result is discarded.
3. Run all three guided chapters on keyboard and pointer; verify that returning to a chapter restores the same evidence and that exiting restores manual controls. Run the notebook from a clean environment using only the documented sample.
4. Run the portable rehearsal and reopen the legacy examples saved in Part 1.

# Part 5: Finish Responsive Design and Verify Accessibility in a Browser

## Problem
Research, “Chromatic Ergonomics, Perceptual Color Science, and Accessibility Engineering,” identifies visual hierarchy and accessibility weaknesses. Keyboard controls and semantic markup exist; rendered and assistive-technology acceptance is still pending.

## Goal
Make the core atlas readable and operable with a pointer, keyboard and screen reader at the agreed test sizes.

## Acceptance Criteria
- [ ] The core journey passes at 1920×1080, 1366×768, phone width and 200% zoom without clipped primary controls.
- [ ] Keyboard-only users can select observations, compare views, inspect or select a footprint, read values and export, with visible focus and no trap.
- [ ] A screen reader announces control labels, errors, selected dates and tabular measurements; essential values do not rely on canvas or color alone.
- [ ] Reduced motion is respected; comparison and timeline controls have button or keyboard alternatives; palette scales, units and missing states remain clear.
- [x] The palette suite checks Crameri `vik` for signed change and `batlow` for ordered magnitude (or the pinned `cividis` where retained), under normal vision, grayscale, protan, deutan and tritan simulations.
- [x] `make verify` runs DOM mirror parity checks for selected dates, units, values, missing-state and interpretation labels; rendered checks are recorded separately.
- [x] Browser evidence records device, browser, viewport, task result and any unresolved defect.

## Constraints & Assumptions
- Event cut: desktop and phone core journey, keyboard/focus, reduced motion, text/DOM parity and contrast/legend smoke checks. Keep the full matrix and assistive-technology review open if not completed.
- Use a policy-permitted browser or user-operated device. A blocked visual check remains pending.
- The agreed matrix is product acceptance evidence; it does not establish a blanket WCAG certification.

## Implementation Steps
1. Establish the visual hierarchy: geographic context, active acquisition, map, controls and evidence. Move secondary details into reachable panels.
2. Pin palette version, license and checksum from [Crameri Scientific Colour Maps](https://www.fabiocrameri.ch/colourmaps/) for `vik` and `batlow`; keep existing `cividis` provenance if used. Test monotonically ordered lightness for sequential legend stops, and a centered zero with monotonic lightness on each signed branch. Inspect fixed legend swatches under the five stated viewing conditions; verify that sign and missingness remain distinguishable by text or pattern even when colors coincide.
3. Provide semantic DOM equivalents for map results, pointer alternatives and status announcements. Check contrast, reflow and focus order.
4. Add a deterministic DOM mirror parity target to `make verify`. Drive the same observation through map/chart and semantic HTML table/status; assert date, unit, value, mask/status and sign match, including a missing-data fixture. Use [W3C non-text alternatives guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html) for review; automated parity is not a WCAG conformance claim.
5. Capture rendered screenshots and run the matrix; fix prioritized defects. Repeat the matrix after Parts 6–8 for their changed controls.

## Dependencies
- Requires: Part 4 for initial acceptance; Parts 6–8 add final regression checks.
- External assumptions: permitted real browser, phone-size viewport and an available screen reader.

## Verification
1. Complete the Part 4 journey at each viewport, 200% zoom, keyboard-only and reduced motion. Save screenshots and failure notes.
2. Use a screen reader to identify a date, read an unavailable value, compare measurements and find export.
3. Check legend text, focus visibility and contrast with tooling plus manual inspection. Keep the Part open if a required environment cannot be exercised.

# Part 6: Complete Native Spatial Inspection and Map Comparison

## Problem
Research, “Eight-Route Fragmentation Problem” and “Grounding in NASA Data and Microwave Physics,” calls for a continuous spatial workflow. The atlas supports preview clicks and local measurements, but native geometry, overlays and comparable sampling need fuller coverage.

## Goal
Let users select and revisit a geographic footprint consistently across compatible radar views, with the native sampling and area basis inspectable.

## Acceptance Criteria
- [x] A selected footprint maps consistently between display and native grid at each tested zoom, viewport and comparison position.
- [x] Supported point and polygon selections return native values, bounds, masks, valid counts and a stated pixel-inclusion rule.
- [x] Reference/current swipes use compatible alignment and fixed scale, or a declared reprojection; unsupported pairs are unavailable.
- [x] Boundary area, sampled valid area and any later class/exposure area have distinct fields and labels.
- [x] A shared 3D mode drapes the accepted layer on the correct terrain for each of the four windows, locks vertical exaggeration to 1×, and preserves case/date/footprint when returning to 2D.
- [x] An out-of-grid or self-intersecting selection cannot return measurements for another location.

## Constraints & Assumptions
- Event cut: reuse the existing 1× terrain and saved footprint previews; defer geometry and rendering changes that could break the story.
- Preview pixels and terrain drape are for orientation. Compute measurements on accepted rasters. Do not infer native values from rendered colors.
- Support Nepal polygon sampling only after its native endpoint and masks are validated; explicitly identify where an edition only supports saved footprints.

## Implementation Steps
1. Centralize affine and CRS transformations. Document `col,row` versus `row,col` at UI/API boundaries and pixel center versus corner conventions.
2. Add draw/edit/reset, footprint overlays and a text/keyboard alternative. Resolve bounds, coordinate validity, server limits and request cancellation.
3. Bind sampling to grid identity, common support and compatible native layers. Compare outputs with an independent raster-window read.
4. Consolidate the sampled relief display using the correct case DEM, declared horizontal/vertical units and locked 1× vertical scale. Verify layer alignment with control points and retain 2D/text alternatives; no GPU dependency for the first guided case.
5. Reuse WGS84 boundary accounting in `src/compute/atlas_measurements.py`; add holes/multipart handling only if tested and explicitly supported. Keep ellipsoidal boundary area separate from valid sampled area.

## Dependencies
- Requires: Parts 2–4.
- External assumptions: approved native rasters and compatible grids for the selected windows.

## Verification
1. Use known cells and independently computed coordinates at center, edges and a non-axis-aligned test grid. Verify zero-based row/column and no-data handling.
2. Submit valid, out-of-bounds, self-intersecting and over-limit polygons. Compare valid support and areas against raster/GIS reference computations.
3. Toggle 2D/3D for all four windows and confirm the same footprint, layer and date. Check control points and a known-height fixture against the intended scale.
4. Reopen a saved geometry and compare its identity, shape, sampled values and display position. Verify the portable edition's supported selections separately.

# Part 7: Separate Recent Change, Persistent Difference and Recovery

## Problem
Research, “Native Ingestion and Longitudinal Persistence Pipeline,” identifies TerraPulse's strongest insight: a small recent difference can coexist with a large reference difference. Gaps and changing masks can distort that reading.

## Goal
Provide a reproducible chronology that distinguishes observed change, persistence and what remains unresolved between acquisitions.

## Acceptance Criteria
- [x] Each trace identifies comparison endpoints, sign, units, footprint, valid count and support policy.
- [x] The prior-visit and reference comparisons are separately visible, use explicit support, and reproduce the saved Kathmandu example under the same baseline and footprint.
- [x] Missing acquisitions and missing measurements are not treated as zero or inserted as playback frames.
- [x] The main view leads with paired cards for recent change versus persistent reference difference; the same selected footprint drives a visible six-hypothesis compatibility matrix wherever rule evidence exists.
- [x] The matrix states which evidence supports, contradicts or cannot test each hypothesis; unsupported case/dates show “insufficient evidence,” with a next check instead of an invented classification.
- [x] Onset, persistence and recovery language is tied to observable bounds and declared rules.

## Constraints & Assumptions
- Event cut: promote the current measured differences and existing rule outputs into the main view. No new scientific metric, threshold or recovery label is required.
- Use a fixed footprint. Where visit-pair support differs, disclose and quantify it; a cross-comparison on unequal support cannot be advertised as fixed-common-support evidence.
- “Last observed” does not mean continuous monitoring; a quiet recent difference does not establish recovery.

## Implementation Steps
1. Define `recent = value(t) - value(previous_observed_t)` and `reference = value(t) - value(reference_t)`. Document whether values are mean dB or dB of mean power.
2. Offer common support for direct comparison and expose valid counts/coverage. Separate an unsupported estimate from a small measured difference.
3. Implement elapsed-time chronology, observed-date playback and configurable persistence/recovery rules with rule version and threshold. Bound onset between observed visits; mark right-censored cases.
4. Place a headline “Recent change / Difference from reference” comparison and a six-row compatibility matrix next to the map, bound to the same case, footprint and dates. Where existing evidence does not support all rows, preserve missing entries. Show a short “What to check next” recommendation and one clearly placed scope note; keep detailed assumptions in the inspector and export.
5. Link plot points, tabular values, map and explanation to the same selected IDs. Design a hypothetical NDRRMA review: examine whether a slope footprint still differs from its reference, check independently dated context, and request a field visit or event inventory. This describes a decision workflow, not hazard diagnosis or agency adoption.

## Dependencies
- Requires: Parts 2 and 4 for the event cut using accepted saved profiles; Part 6 for full native spatial integration.
- External assumptions: accepted co-registered acquisitions. Extra visits are optional; actual gaps remain represented.

## Verification
1. Check the Part 1 Kathmandu September example on its exact support and reference; independently recompute the two differences.
2. Test a missing visit, same-day product distinctions, all-invalid support, true zero and a synthetic time series with known onset and incomplete recovery.
3. Play both countries and export one case; compare the order, dates, endpoints and valid counts to the manifest.

# Part 8: Integrate Dated Environmental Context and Scenarios

## Problem
Research, “Eight-Route Fragmentation Problem” and “Critical Gaps in the Current Science Implementation,” notes that rainfall, thermal and scenario coverage is uneven. The atlas exposes selected Kathmandu context; other dates and locations cannot inherit it.

## Goal
Provide one consistent context inspector that reports measured inputs and model scenarios only for their valid place, time and support.

## Acceptance Criteria
- [x] Context items expose actual acquisition/aggregation time, coverage, resolution, units, source and match status.
- [x] Kathmandu scenarios reopen with the same observed anchor, model version, parameters and output; dates or cases without inputs cannot run the model.
- [x] A missing rain bin, invalid QA cell or incompatible thermal scene remains unavailable rather than becoming a zero.
- [x] An IMERG backfill, if eligible, produces traceable rainfall windows for the accepted subset of the 20 visits with explicit per-footprint coverage; missing or excluded dates remain unavailable.
- [x] Additional Bangladesh context is enabled only for inputs accepted in Part 3, with an explicit coverage report.

## Constraints & Assumptions
- Event cut: use the current dated Kathmandu POWER, thermal and saved scenario context; Bangladesh rainfall remains unavailable until accepted. Defer new ingest and scenario computation.
- Keep POWER and any approved alternative rainfall products identifiable at native support. Do not present resampled rainfall as a radar-pixel measurement.
- Thermal observations retain independent dates. Scenario sensitivity is conditional on model assumptions, not a forecast or measured flood extent.

## Implementation Steps
1. Build a context index by case, product, observation/pair and source timestamp. Define exact joins and allowable time offsets per source; expose the offsets to the user.
2. Verify rainfall unit semantics. For rate bins integrate `sum(rate_i × overlapping_hours_i)`; for accumulated products account for native bins explicitly. Report expected/valid temporal coverage and footprint overlap.
3. Implement the approved IMERG V07 HDF5 path from Part 3 with versioned source manifests, bin coverage, quality screening and area-weighted crop overlap. Start with one independently checked rainfall window, then backfill the approved subset. Keep POWER and IMERG labeled separately.
4. Render QA-screened thermal, optical, terrain and rain records separately with their own masks. Label unmatched records without auto-selecting the nearest date.
5. Move the scenario controls into the atlas inspector or shared panel. Reuse the existing model endpoint, constrain parameters, version inputs, and use cached results only when the parameters and input digest match. Label offline presets as saved scenarios.

## Dependencies
- Requires: Parts 2–4; uses Part 7 for timeline binding.
- External assumptions: accepted additional products and QA for any expansion beyond existing Kathmandu coverage.

## Verification
1. Check an existing Kathmandu date and its available context, a later Kathmandu date with gaps, and a Bangladesh date. Verify each against source records.
2. Use a known-rate fixture with a partial interval and one missing bin; check totals and coverage. Check cloud/thermal QA and timestamp mismatch rejection.
3. Change case/date while a scenario is pending; confirm the result cannot appear under the new selection. Replay a saved scenario and verify input identity and output equality within the declared tolerance.

# Part 9: Add Terrain and Radiometric Quality Gates

## Problem
Research, “Critical Gaps in the Current Science Implementation” and “Upgrade the Dual-Pol Rules to … HAND Masking,” proposes terrain screening. A terrain preview does not establish radar visibility or dependable drainage, and a universal threshold can create false confidence.

## Goal
Publish auditable per-layer quality and terrain masks. Enable a HAND-based exploratory layer only where drainage and DEM checks support it.

## Acceptance Criteria
- [x] Input masks are decoded for the actual product version, aligned to the correct grid and reported separately from environmental classifications.
- [x] Terrain indicators identify DEM source, vertical datum, grid, resolution, support and boundary limitations.
- [x] Any HAND output has a documented drainage definition, downstream link, datum and nodata handling; unsupported cells remain masked.
- [x] Masked, excluded and assessed areas are counted separately. No terrain-only gate is described as proof of water or damage.

## Constraints & Assumptions
- Use the existing sampled NASADEM view for orientation. Scientific terrain calculations require accepted elevation data and drainage coverage beyond crop edges where necessary.
- Distinguish product-provided radar QA, modeled visibility and topographic screening. Do not infer look geometry from color.

## Implementation Steps
1. Create a per-product QA policy for valid data, saturation/noise and visibility flags where supplied. Test QA precedence before joining masks.
2. Audit vertical datum, DEM voids, flat areas and crop-boundary drainage. Record any fill/breach procedure and its parameters.
3. Where supported, trace each valid cell to a downstream drainage cell and calculate `HAND = z_cell - z_connected_drainage`. Keep unresolved flow paths unavailable and document grid/resampling choices.
4. Combine masks only for explicitly defined analyses; report the support change and run sensitivity checks for drainage and threshold choices.

## Dependencies
- Requires: Parts 2, 3 and 6.
- External assumptions: usable DEM, QA metadata and drainage context. An unsupported HAND extension stays gated.

## Verification
1. Exercise known QA bits and a synthetic slope/valley with a known downstream elevation, nodata and boundary outlets.
2. Inspect representative mapped terrain, compare modeled drainage against an independent drainage reference where available, and quantify invalid and boundary-affected support.
3. Check that inputs masked for one product do not automatically mask an unrelated layer or change historical totals.

# Part 10: Improve Dual-Polarization Analysis Within the Available Channels

## Problem
Research, “Upgrade the Dual-Pol Rules to …,” proposes richer descriptors and interpretation. TerraPulse has HH, HV and cross-polarized power share; additional decomposition or vegetation claims need product-specific inputs and validation.

## Goal
Deliver traceable dual-pol quantities and evidence rules that use only measured channels and distinguish physical observations from hypotheses.

## Acceptance Criteria
- [x] HH, HV, power share and every enabled descriptor have documented inputs, units, valid domain, mask and scale.
- [x] New descriptors pass published formula/assumption checks for the available polarization, or remain unavailable with the missing requirement documented.
- [x] Rule output cites supporting and conflicting observations, coverage and next evidence; it does not assign cause or probabilities without validation.
- [x] Baseline dual-pol outputs and their provenance checks remain unchanged.

## Constraints & Assumptions
- [Mandal et al. (2020), sections 3.1–3.2](https://forum.step.esa.int/uploads/short-url/r4jFVNVhsM2vI1zb1Ufr7NBMDP4.pdf) uses full complex dual-pol covariance: the determinant and eigenvalues depend on the off-diagonal term. Two powers alone do not determine that DpRVI. [Bhogapurapu et al. (2022)](https://doi.org/10.1016/j.rse.2022.112900) proposes DpRVIc for detected GRD data, a separate quantity. Its applicability to the actual NISAR inputs is a post-event method check, not established by the paper's title or by having two channels.
- Never assume absent off-diagonal covariance terms are zero to justify a decomposition. No DpRVI, crop-loss or vegetation-fraction label for power share.
- Preserve paired support and distinguish linear-power averaging from averaging dB.

## Implementation Steps
1. Verify existing `P = 10^(dB/10)` and `share = P_HV / (P_HH + P_HV)` on paired valid samples, including HV greater than HH and masked inputs.
2. For each proposed descriptor, obtain the exact published definition and match the available channels, calibration, product and domain. Implement only the supported formulas in an additive module.
3. For DpRVIc specifically, obtain the exact equation and preprocessing assumptions from Bhogapurapu et al.; document power/ratio convention, valid domain, calibration and transfer from the studied data to this HH/HV record. Compare against independently calculated fixtures, including cross-pol greater than co-pol. If a requirement cannot be reproduced, retain the current power share and mark DpRVIc unavailable.
4. Use stable calculations and fixed display scales; report out-of-domain samples and support changes. Wire summaries into the footprint inspector.
5. Make the explanatory rules versioned and explicit. Calibrate thresholds only against the Part 13 design; keep the pre-validation layer exploratory.

## Dependencies
- Requires: Parts 2, 3, 6 and 9.
- External assumptions: suitable channel data and method references for additional descriptors; independent labels for performance claims.

## Verification
1. Test equal powers, asymmetric powers, zero/invalid support and extreme valid dB inputs; compare raster/footprint summaries with independent calculations.
2. Try a descriptor that needs unavailable covariance and confirm it is not displayed as measured.
3. Review paired HH/HV support and validate the updated presentation with existing dual-pol provenance checks.

# Part 11: Expand Coherence and Gate Any Damage-Proxy Product

[Implementation and verification](../reports/development/parts-11-15-handoff.md)

## Problem
Research, “Critical Gaps in the Current Science Implementation,” proposes ARIA-style coherence change. The current Nepal atlas shows two measured pairs and a crop-wide difference; these do not establish a clean pre-event reference or independent damage evidence.

## Goal
Support comparable pair and footprint measurements, and make any damage-proxy layer contingent on a suitable design and held-out references.

## Acceptance Criteria
- [x] Every enabled pair shows both endpoint IDs/dates, native posting, channel, orbit/look, pair interval and valid support.
- [x] Comparable pairs use joint valid support and declared grid policy; unsupported pairs cannot be differenced.
- [x] Map and footprint statistics use the same signed delta and mask. Pair chronology does not masquerade as single-visit chronology.
- [x] A damage-proxy layer is enabled only after event timing, pre-/co-event pairing, control selection and independent validation gates pass.

## Constraints & Assumptions
- Same track and similar interval alone do not establish comparability. Account for baseline, temporal decorrelation, geometry and coverage.
- A 24-day bridge, if accepted, remains a distinct interval. It cannot replace the missing observation.
- Explicit decision: the two existing Nepal pairs remain descriptive. A histogram-matched map or phase conversion may be technically computable, but the record does not establish a clean reference plus independent evidence for a release damage or LOS claim. Accept that scope trade-off; keep the ARIA-style method under the scientific gate.

## Implementation Steps
1. Extend the pair registry for additional accepted GUNW inputs; validate both endpoint IDs, polarization, quality, grid, coverage and interval.
2. Produce common-valid coherence rasters and footprint summaries. Define `delta = coherence_later - coherence_earlier` on common support; if using loss-positive display define the sign explicitly.
3. If a credible pre-/co-event design exists, freeze control regions and comparison method before looking at validation labels. If normalization or histogram matching is proposed, validate it on stable controls and keep raw differences available.
4. Bind interpretation and export to the chosen pairs, event chronology, reference/control evidence and validation report.

## Dependencies
- Requires: Parts 2, 3, 6 and 9. A validated proxy also requires Part 13.
- External assumptions: compatible new pairs and independent dated damage evidence for the proxy extension.

## Verification
1. Compare one real pair and the current Nepal joint support against independent native-window calculations.
2. Reject incompatible grids/endpoints, invalid masks and mismatched interval classes. Check a controlled fixture for sign, range and valid counts.
3. For the proxy extension, compare held-out locations, quantify false positives and uncertainty, and have a reviewer check the event chronology. Otherwise record the descriptive-only scope.

# Part 12: Evaluate Displacement as an Optional Research Extension

[Implementation and verification](../reports/development/parts-11-15-handoff.md)

## Problem
Research, “Critical Gaps in the Current Science Implementation,” proposes quantitative motion. Raw phase or coherence alone does not supply corrected, referenced or validated displacement.

## Goal
Determine whether an evidence-backed line-of-sight (LOS) displacement study is feasible, and publish a displacement product only if all scientific gates pass.

## Acceptance Criteria
- [x] A feasibility report checks phase, connected components, geometry, wavelength/sign, corrections, reference stability and independent motion evidence.
- [ ] If feasible, the result exposes reference area/date, valid support, corrections applied, uncertainty and LOS direction.
- [x] If not feasible, no displacement values or motion maps are enabled; the report lists the missing inputs and tests.

## Constraints & Assumptions
- Optional; the core release can proceed without this Part. A failed feasibility gate is an explicit no-go decision, not a completed displacement implementation.
- Do not claim vertical movement or millimeter precision from a single LOS geometry or unresolved phase.

## Implementation Steps
1. Inventory phase components, product correction status and independent benchmarks. Document what has already been corrected and avoid double correction.
2. Predefine stable reference/control areas and reject disconnected or unreliable phase. Model correction uncertainty and missing terms.
3. For validated corrected and referenced phase, use `d_LOS = s × wavelength × delta_phase / (4π)`, with sign `s` and wavelength taken from the verified product convention and metadata.
4. Compare against independent displacement references with matching time and geometry. Release values only where uncertainty and bias support the claim.

## Dependencies
- Requires: Parts 3, 9 and 11; field claim requires Part 13.
- External assumptions: suitable phase stack, corrections, stable controls, independent benchmark and expert review.

## Verification
1. Inject known phase/reference offsets and test sign, units and component masking against an independent calculation.
2. Check residuals on stable controls and agreement at independent benchmark points. Report errors and support, including failures.
3. Verify the UI, dossier and public claims omit displacement if any gate fails.

# Part 13: Validate Against Independent Evidence and Report Area Honestly

[Implementation and verification](../reports/development/parts-11-15-handoff.md)

## Problem
Research, “Epistemic Honesty Versus Actionable Decision-Support Paradox,” asks for defensible outputs. Existing dated optical matches are useful comparisons but do not by themselves validate water, vegetation, damage or exposure estimates.

## Goal
Establish an independent validation process and release only claims supported at the stated geography, dates and uncertainty.

## Acceptance Criteria
- [x] Before tuning, a written protocol freezes target classes, reference requirements, sampling design, exclusions, split units, metrics and claim thresholds.
- [ ] Held-out evidence is independent of calibration and avoids overlapping footprints/scene leakage. Reference date offsets and unusable labels are recorded.
- [ ] The validation report includes support, failures, suitable uncertainty and performance by relevant geography/date or subgroup.
- [x] Area-adjusted totals, exposure estimates and intervals appear only when a defensible sampling design and validated class/exposure layers support them.

## Constraints & Assumptions
- An optical match, an exploratory control and a human-confirmed reference are distinct. Do not infer crop damage, erosion or inundation duration from threshold overlap.
- Do not select validation thresholds after seeing the held-out scores. If references are insufficient, report descriptive agreement and retain exploratory labels.

## Implementation Steps
1. Define one claim at a time, its unit of analysis and independent reference source. Freeze blocks by site and/or date and label rules before calibration.
2. Create the reference table with observation/footprint IDs, date offset, QA, source and adjudication. Document excluded and ambiguous samples.
3. Fit or choose thresholds on development data only. Evaluate on held-out blocks with suitable precision/recall, error magnitude, confusion and coverage metrics. Use uncertainty methods consistent with sampling and dependence.
4. For area claims, separate projected/ellipsoidal boundary area, valid support, raw mapped class area and any sampling-adjusted estimate. Report weighting, uncertainty, coverage and assumptions.

## Dependencies
- Requires: Parts 2, 3 and 6 for protocol; the relevant science Part for scoring (Parts 7–12, 14 or 15).
- External assumptions: independent reference data, enough usable samples and a reviewer. The protocol can start before all data arrive.

## Verification
1. Audit calibration versus holdout IDs for leakage and reproduce metrics from raw match tables with a separate calculation.
2. Check area accounting against a known-mask fixture and, for adjusted area, independently recompute from the published design and weights.
3. Match each proposed product claim to its metric, threshold and scope. Disable or downgrade claims that fail or lack evidence.

# Part 14: Turn River Memory into a Bank-Review Workflow

[Implementation and verification](../reports/development/parts-11-15-handoff.md)

## Problem
Research, “Problem-Solution-Vision-Execution” and “Hometown Story Advantage,” calls for a useful river investigation. Jamuna radar-dark recurrence can suggest where to look, but does not establish bank displacement or erosion.

## Goal
Let a river reviewer locate persistent changes, compare them with independent dated bank evidence when available and decide where field checks are needed.

## Acceptance Criteria
- [x] A reviewer can select a reach, compare dated images, inspect the same footprint and identify a specific next field check.
- [x] Any bank line or transect has a source, date, registration uncertainty and stable identity. A radar signature without a validated line remains a candidate.
- [x] Numeric movement is displayed only for validated bank lines and interpretable transect crossings, with direction, uncertainty and time interval.
- [x] Missing, ambiguous or below-resolution movement is identified without a false zero or precise rate.

## Constraints & Assumptions
- Jamuna is the initial release scope. Do not infer engineering exposure or erosion cause from a channel outline.
- Dates, water level, season and observation geometry may affect apparent boundaries.

## Implementation Steps
1. Define a hypothetical BWDB reviewer journey: select a reach, compare dated evidence, flag a site for inspection, and export the location and question. This is a design persona, not agency adoption or endorsement. Add a guided reach and fixed footprint selection with recent/reference evidence and a dated reference panel.
2. If accepted bank lines exist, co-register them and create stable transects. Define outward/inward sign, orientation and ambiguity rules for split channels or multiple intersections.
3. Compute signed distance between valid transect intersections on a suitable metric grid. Include positional, registration and delineation uncertainty; label unresolved movements.
4. Save a review packet with map, measurements, alternatives and the next observation needed. Link supported claims to Part 13.

## Dependencies
- Requires: Parts 4, 6 and 7 for the workflow; Parts 3 and 13 for validated bank movement.
- External assumptions: independently dated bank boundaries or field checks for migration claims.

## Verification
1. Measure synthetic bank lines with known shifts, multiple crossings and zero/near-resolution differences; verify sign, units and rejection.
2. Complete one real Jamuna investigation. Compare it with an independent dated reference if available and log discrepancies.
3. Verify the UI/export distinguishes a change candidate from a validated migration measurement.

# Part 15: Turn Wetland Pulse into a Repeat-Visit Review Workflow

[Implementation and verification](../reports/development/parts-11-15-handoff.md)

## Problem
Research, “Empirical Inventory” and “Hometown Story Advantage,” identifies a wetland use case. Repeated radar darkness, water classification, habitat condition and inundation duration are different quantities.

## Goal
Let a reviewer compare observed wetland signatures across valid visits and identify where independent water or habitat checks are most useful.

## Acceptance Criteria
- [x] A selected Tanguar footprint shows both channels, the observed-visit denominator, valid/unknown counts and dated reference evidence.
- [x] The display and export label the fraction of valid observed visits and preserve the actual chronology and outages.
- [x] Any water, flooded-vegetation or habitat class is enabled only for the validated class and scope from Part 13.
- [x] Continuous hydroperiod and crop/habitat damage claims remain unavailable without the reference coverage and methods to support them.

## Constraints & Assumptions
- Shadows, wind, vegetation and acquisition geometry can change radar response. Use the approved quality policy and report competing explanations.
- No interpolation of missing visits into observed occupancy.

## Implementation Steps
1. Define a hypothetical DAE reviewer journey: locate a changed crop/wetland signature, check coincident observations, and request water-depth or crop-stage evidence. This is a design persona, not an impact finding. Add a guided wetland footprint and synchronized HH/HV/reference traces. Bind each optical comparison to the exact frozen footprint and date.
2. Define `observed occupancy = matching valid visits / valid assessed visits`; return unavailable when the denominator is zero. Show the threshold, valid dates and support.
3. Calibrate and test a water-state classifier only when accepted independent labels exist. Separate clear water from ambiguous vegetation or unsupported classes.
4. Add a field-check output: select a footprint, identify a disagreement, name the missing observation and export the chronology.

## Dependencies
- Requires: Parts 4, 6, 7 and 10 for the workflow; Parts 3 and 13 for validated classes.
- External assumptions: suitable date-matched water/habitat labels for validation and denser independent observations for any duration claim.

## Verification
1. Test a known series containing matching, nonmatching, invalid and missing visits; verify numerator, denominator and unavailable state.
2. Complete a Tanguar investigation at a valid reference match and a date with no match. Confirm the reference cannot migrate to another footprint.
3. For any validated class, reproduce the held-out results and verify legends and dossiers use the exact permitted claim.

# Part 16: Make Evidence Exports Reopenable and Reviewable

[Implementation and verification](../reports/development/parts-16-19-handoff.md)

## Problem
Research, “Problem-Solution-Vision-Execution” and “Collapse the Eight HTML Routes,” calls for evidence that survives handoff. Current exports preserve useful measurements, but replay and independent review need explicit version and capability handling.

## Goal
Create a portable dossier that another reviewer can reopen and use to reproduce the same investigation on the same accepted inputs.

## Acceptance Criteria
- [x] The dossier stores schema/data versions, case, exact observations or pairs, footprint geometry/grid, units, method, masks/support, source IDs, hashes and scope limits.
- [x] Import reproduces the selected state and applicable numbers within declared tolerance on a matching runtime.
- [x] Incompatible schemas, stale records and unavailable native data show a precise reason, with a readable summary retained where possible.
- [x] The dossier includes a next verification action and separates observations, model output, hypotheses and review notes.
- [x] The full four-component record carries distinct support and reference metadata for every component; unavailable components are null.

## Constraints & Assumptions
- Event cut: round-trip a saved footprint and its actual evidence from the static demo. Native-polygon recomputation and broader import compatibility are post-event.
- Treat imported JSON as untrusted data. Bound geometry and file sizes, validate before use, and avoid executable content or implicit network access.
- Offline saved measurements can be reviewed without the full runtime; native recomputation requires the declared rasters.

## Implementation Steps
1. Extend `observationPacket` or its successor with the Part 2 contract, provenance and explicit tolerances. Include context selections and pair endpoints where applicable.
2. Add a reviewable summary and import/reopen action. Restore the source state only after matching dataset versions and capabilities.
3. Add deterministic test bundles for saved and native selections, a paired product, and a dated scenario. Log version mismatch instead of substituting the current dataset.
4. Specify the research-proposed four-component record `[Δγ⁰_HH(dB), ΔDpRVIc, Δcoherence, ΔLOS]` with a per-component reference, endpoints, grid/support, units, method and status. Keep unavailable components null and distinguish pair-wise coherence intervals from single-visit dates. Do not compute a composite score or imply a common aligned footprint until the scientific gates in Parts 10–13 pass. Show power share as its own measured field, not a substitute for DpRVIc.
5. Add optional reviewer notes and next field action as separate metadata that cannot alter the measurements.

## Dependencies
- Requires: Parts 2, 4, 7 and 8 for the saved event edition; Part 6 for full native selection replay. Incorporate Parts 11–15 only for products included in the release scope.
- External assumptions: matching local runtime and data for native recomputation.

## Verification
1. Export a Bangladesh saved footprint, a native polygon, and a Nepal pair or scenario. Reopen each in a fresh session and compare IDs, geometry, timestamps and numbers.
2. Try wrong hashes, an unsupported version, oversized geometry and an offline edition missing native data. Confirm explicit handling and no silent substitutions.
3. Confirm an unavailable DpRVIc or LOS is null, not zero or substituted; check pair endpoints and support for any coherence component.
4. Give the dossier to a second reviewer and verify they can locate its sources and understand the next check without an explanation from the author.

# Part 17: Build and Verify a Live Zero-Install Demo

[Implementation and verification](../reports/development/parts-16-19-handoff.md)

## Problem
Research, “Eliminate the Private Localhost Barrier via Hybrid Zero-Install Cloud Delivery,” and the follow-up review identify an access barrier. A 2.54 GiB runtime download, a local server, and even a hostable artifact do not give a judge an immediately usable URL.

## Goal
Deliver a real HTTPS link that opens the core atlas without login, installation, or a backend, with a separately tested offline fallback. Retain an explicit post-event track for browser-native analysis.

## Acceptance Criteria
- [x] A reproducible build produces checksummed static and portable artifacts containing only approved redistributable assets.
- [ ] The approved static artifact is deployed and its exact live URL passes the three-chapter guided journey and saved-footprint export/reopen from a logged-out desktop and a phone on a separate network.
- [ ] The live UI and video describe “Saved observations and footprints.” Custom native probes/polygons are identified as full local runtime features; hosted controls never promise unavailable work.
- [ ] Five cold desktop runs on the stated profile each reach a usable first case in under 3 seconds, with no native raster, WASM analytics bundle or other case on the first-view path.
- [x] The portable HTML fits the 8 MiB event budget and completes the guided flow and export with the network disconnected.
- [ ] Post-event native delivery, if included, passes strict COG validation, actual byte-range tests, raster/query parity and failure handling. Its availability is documented separately from the static demo.

## Constraints & Assumptions
- Event cut: static saved evidence, with no dependency on client-side COG probing or DuckDB. The user's GitHub repository stays private. Public access to this demo does not expose the repository, full backend, source HDF5 or credentials.
- Preferred publish route: [Cloudflare Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) or an approved equivalent that accepts the audited build folder without connecting the private repository. The host account, live URL and exact publish scope must be authorized after the artifact is reviewable. No live link counts as complete until it actually passes acceptance.
- Performance target: under 3 seconds from navigation start until the first meaningful map, selected-date values and working Next control. Test a named desktop/browser, 20 Mbps downstream and 100 ms latency, empty browser cache and five runs. Record actual timings, transfer size and test settings. A missed target remains a failure or documented exception, never a measured success.
- Start with a first-view transfer budget of 1 MiB compressed. Defer other chapters, secondary layers, terrain and expensive analysis until needed. The portable file remains self-contained.

## Implementation Steps
1. Create a static entry and versioned release assets: shell, first-case preview and first-case measurements; load other chapter assets on demand. Use the Part 2 contract, relative paths, real error/fallback states, and no localhost/API dependency for saved investigations.
2. Preserve the one-file build using `scripts/package_atlas.py`. Generate an artifact manifest with digests, sizes, sources, redistribution status and feature limits. Check the deploy folder against an allowlist; remove unpublished native files, private metadata and credentials. Review the exact folder that will be uploaded.
3. Deploy that folder using Pages Direct Upload in the authorized account, or the equivalent approved static host. Record the canonical HTTPS URL, immutable deployment ID or equivalent, artifact digest and rollback method. Confirm rollback to a known-good bundle or document how to unpublish a first deployment. Leave repository visibility unchanged.
4. From a fresh logged-out browser, open the live link and run each chapter plus export/reopen. Repeat on a phone over mobile data. Verify no credential prompts, private redirects, local URLs, missing relative assets or mixed content. Record the link and successful runs before handing it to a judge.
5. Post-event: prototype one browser-native window query over COG using byte ranges and a pinned reader; prototype one filtered GeoParquet evidence query in DuckDB-WASM. Lazy-load each engine only on request. Benchmark bounded transfer, responsiveness and mobile memory against static previews and compare results to native reference outputs. Ship the prototype only if it provides usable performance and correct results; document the measured go/no-go.
6. Add a release-manifest-driven COG check to `make verify`. For every asset advertised as a COG, use pinned [rio-cogeo `cog_validate(path, strict=True)`](https://github.com/cogeotiff/rio-cogeo/blob/main/rio_cogeo/cogeo.py); fail on invalid results and retain errors/warnings. Report “not applicable: no COGs in this edition” for the preview-only bundle. A streaming edition must additionally pass actual HTTP/reader checks.

## Dependencies
- Requires: event cuts of Parts 4, 5, 7, 8 and 16 for the saved demo; Part 6 for browser-native analysis. The event cut does not depend on new data or the user pilot.
- External assumptions: permitted desktop and phone checks, throttling controls, authorized static hosting, redistribution rights for the reviewed assets and deployment approval. A missing authorization blocks publishing, not preparation or offline verification.

## Verification
1. Run `make atlas-portable` and `node scripts/verify_portable_atlas.mjs`. Verify release hashes and replay the portable edition from a clean profile with the network disconnected.
2. Verify the actual public URL with the logged-out desktop and phone runs from step 4. Test shared state and export/reopen, and record exact device, browser, network and deployment ID.
3. Record five throttled cold-load traces and timing from navigation to the specified readiness event. Assert the first-view asset list and check the performance target; report regressions or exceptions explicitly.
4. For the post-event COG path, verify HEAD and correct 206 Content-Range/content length, invalid-range handling, allowed origins and preview fallback. Compare a sampled real window, nodata mask and known GeoParquet query with native reference results; record bytes transferred and prove a query does not download the entire dataset.

# Part 18: Run a Real User Pilot and Fix the Workflow

[Implementation and verification](../reports/development/parts-16-19-handoff.md)

## Problem
Research, “Problem-Solution-Vision-Execution,” raises the question of whether TerraPulse helps anyone make a better next decision. Current automated verification cannot answer it.

## Goal
Observe real users investigating the records, measure where the workflow helps or fails, and fix the most serious problems before release.

## Acceptance Criteria
- [ ] At least three intended users complete the agreed scripted tasks, with role, device, assistance, time and outcome recorded using non-identifying IDs.
- [ ] The pilot records whether each user can distinguish recent from reference change, assess an alternative explanation and identify the next field check.
- [ ] At least one independent reviewer successfully reopens an exported dossier and verifies the stated selection and result.
- [ ] Blocking failures are fixed and retested or removed from the release scope. Report sample size and observed outcomes without generalizing beyond the pilot.

## Constraints & Assumptions
- Recruit actual participants with consent; no simulated testimonials or invented success rates. If recruitment fails, mark this Part waiting.
- User usefulness is separate from classification accuracy. Field evidence still requires Part 13.

## Implementation Steps
1. Freeze a short protocol: one Bangladesh guided task, the Kathmandu persistence task and evidence handoff. Define correct answers and what counts as facilitator assistance.
2. Record task completion, interpretation errors, effort and whether the packet changed or clarified the user's next check.
3. Rank issues by severity and fix the largest sources of confusion. Retest the affected task with evidence.
4. Record limitations and translate only observed benefits into release claims.

## Dependencies
- Requires: Parts 5, 7, 14, 15 and 16 in at least their exploratory scope; use the Part 17 candidate for the final trial.
- External assumptions: real river, wetland or surface-change reviewers and a reviewer who can repeat the dossier task.

## Verification
1. Audit anonymized task records and compare claimed successes with the scoring rubric.
2. Re-run each repaired task and record the outcome and edition used.
3. Verify the release narrative distinguishes observed workflow benefit from scientific validation.

# Part 19: Freeze the Release and Verify Submission Readiness

[Implementation and verification](../reports/development/parts-16-19-handoff.md)

## Problem
Research, “Strategic Roadmap” and “Hometown Story Advantage,” calls for a coherent presentation. Earlier observations about rules, judging preferences and access do not establish current eligibility or that a submission has been made.

## Goal
Prepare a reviewable release candidate and presentation package whose claims, links, data and verification evidence agree.

## Acceptance Criteria
- [x] A release manifest binds revision, accepted Part outcomes, versioned inputs, claims, checksums, limitations and rollback instructions.
- [ ] The agreed user journey works in the actual release edition and every proposed link opens with the intended audience's permissions.
- [ ] The final narrative, recording and instructions show real evidence, disclose contributions/data and match the claim ledger.
- [x] Current official rules and any organizer-dependent eligibility or access question are resolved or clearly recorded as blocking submission.

## Constraints & Assumptions
- The release can be a private local candidate. Public visibility, third-party deployment and submission are separate actions that require applicable authorization.
- Keep the true development history. Do not claim that unfinished or deferred scientific work was completed during the event.
- Use the currently confirmed submission format; the earlier 180-second storyboard is a draft, not a rule.

## Implementation Steps
1. Review the Part register. Require accepted evidence for every feature in the release scope; label omitted or unavailable capabilities consistently.
2. Freeze the exact live deployment plus its matching portable artifact. Record repeatable build commands, checksums, sizes and rollback procedure. Confirm the live URL is still the one verified in Part 17.
3. Start from the shot list drafted in Part 4. Record one continuous walkthrough of the same live workspace: a Bangladesh question, the Nepal persistence distinction, the six-hypothesis evidence where available, and a dossier handoff. State the saved-demo/native-runtime boundary once, use clear captions and report measured findings confidently with their limits. Do not imply real-user impact, independent damage validation or complete hosted native tools.
4. Verify current rules, event eligibility, data attribution, contribution disclosure and viewer access. Prepare any public artifact or submission for separate review.

## Dependencies
- Requires: the verified event cuts of Parts 1–5, 7, 8, 16 and 17 for the event package. Part 18 and the full scientific extensions are post-event; no pilot benefit or advanced science claim is allowed unless its corresponding Part is accepted.
- External assumptions: current official requirements, organizer clarification where needed, permitted recording/access and approval for publication or submission.

## Verification
1. Run `make verify`, the portable rehearsal and the claim-ledger check against the frozen candidate. Confirm the artifact digest and record the actual result.
2. Repeat the logged-out live link, mobile and disconnected fallback walkthroughs on the final builds; inspect the recording and presentation for unsupported claims and broken links. If the URL or authorization is missing, keep public-demo acceptance open and use the fallback only if the rules allow it.
3. Compare the release manifest to the Part acceptance evidence and the confirmed requirements. Report local readiness and any unresolved publication/submission gate separately.
