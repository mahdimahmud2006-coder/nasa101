# TerraPulse: released-challenge review and next-level strategy

**Historical strategy snapshot, written before the subsequent build.** [Implementation 08](IMPLEMENTATION_08_INVESTIGATIONS.md) now delivers the two Nepal HH/HV cases and the three-workspace foundation. Bangladesh observations and the longer series remain pending. Statements below about proposed features describe the pre-build review.

**Review date:** 28 October 2026. **Assessment: Needs revision before a polished scientific submission.** The working application is substantial; independent event interpretation, presentation verification, and the submission narrative need further work. This is a scoped evidence review and development recommendation, not a winning-probability estimate.

## 1. Decision

Keep TerraPulse and make it an **interactive surface-change investigation workspace**. Its central question should be: **“The change alert disappeared—but did the surface recover?”** Support the answer with a corroborated local case, actual HH/HV observations, a longer temporal baseline, and an inspectable evidence dossier. Keep existing flood and landslide indices as optional exploratory context.

Proposed positioning: **“TerraPulse makes the rhythms of surface change understandable: what changed, what persisted, which explanations fit, and what observation is needed next.”** That is a proposed direction, not a claim that causal inference or all proposed capabilities are already implemented.

The project's advantage is the connection between measurement, temporal behavior, interpretation, and a reproducible next step. More layers alone will not establish that advantage. NASA OPERA already offers surface-water, disturbance, and displacement product families; a new colored change map is insufficient differentiation. [NASA JPL OPERA products](https://www.jpl.nasa.gov/go/opera/products/)

## 2. What the released statement actually asks for

The controlling requirement source is the complete statement supplied by the user, retained in `reports/2026-10-28/challenge_statement_review.json` with its SHA-256. Its requirements are reference material for this analysis, not instructions to execute every example. The official challenge URL returned HTTP 502 during this review, so the supplied text controls the analysis.

| Requirement or suggestion | Current position | Consequence |
|---|---|---|
| Interactive application using NISAR | Implemented with actual provisional L2 GCOV observations, playback, map interactions, and analytical views | Strong direct fit; make NISAR visible in the opening minute |
| Track and visualize one or more kinds of surface change | Backscatter change and temporal behavior implemented | Identify a defensible physical surface-change case; an unexplained anomaly is weaker communication |
| Broad, accessible communication | Guided story, local assets, provenance, readable desktop design exist | Current browser legibility, GPU behavior, and accessibility still need direct verification |
| Physical-driver hypotheses | Rainfall, terrain, optical/thermal, and hazard context exist | Present competing explanations and missing evidence; do not substitute an index for event attribution |
| Extra polarization, dates, sensors, locations | Optional in statement; high-value HH/HV and extra-date opportunities verified below | Expand only where it resolves a scientific question |
| Open-source, usable solution | Source, license, launcher, preflight, portable package exist locally | Public access and final submission links still need checking |

Thermal imagery, AI/ML, global processing, operational disaster prediction, and centimeter displacement are not required. The statement's centimeter-movement example does not make an intensity-only GCOV workflow a displacement measurement. GCOV provides calibrated, terrain-corrected backscatter; phase-based movement requires an appropriate interferometric workflow. [ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/)

## 3. Progress: what is real, what remains weak

**Implemented:** three same-track/frame NISAR dates; quality masking and robust change detection; temporal outputs; terrain and coarse regional rainfall; cloud-screened Landsat context; flood scenarios and escalation; Change DNA; landslide susceptibility; Evidence Studio and Change Lab; exports, preflight, and a portable release process.

**Previously recorded verification:** 169 Python tests, 25 JavaScript tests, five analytical validators, and 508 preserved earlier analytical artifacts. **This review:** all 26 JavaScript tests pass after adding a regression for a real coverage-label defect; static checks pass. These interaction tests use explicit mocks and are not browser QA. The Python suite and all five validators were not rerun in this research turn because their science logic was unchanged.

**Critical limitations:**

- Only three compatible dates currently processed; they bracket onset and persistence but do not establish normal seasonality or an exact event day.
- One retained zone of 199 native pixels, about 1.99 hectares. A one-zone catalogue cannot establish similarity-model accuracy or generalization.
- Current crop has zero overlap with the preliminary independent mudflow/rockflow impact map. The nearest mapped footprint is about 5.65 km away. This does not prove absence of impact, but prevents using that map as validation of the current zone.
- Ten nominal historical landslide reports reduce to two under the ≤1 km precision screen. They do not provide independent calibration or predictive accuracy for the 2026 case.
- POWER rain is regional, native 0.5° × 0.625°; resampling it onto a 30 m grid does not create local rain measurements.
- Four thermal scenes cover only about 5.65–25.40% of the AOI under the exploratory uncertainty screen. No matched thermal anomaly baseline exists. Keep temperature as optional observation context.
- Current browser visual/accessibility/GPU checks and a physically disconnected rehearsal remain unverified. Browser URL policy blocked access; no alternate browser route was attempted.

There is no defensible single completion percentage: software implementation, scientific corroboration, and submission readiness have different remaining work. A feature count must not be presented as a percentage of scientific validity.

## 4. Three concrete discoveries from this review

### A. A stronger event case may need a different crop, not new radar

The full three NISAR scenes cover all 37.35 km² of the archived preliminary UNITAR/UNOSAT mapped geometry. All 17 representative geometry-part sample points were inside the grid and quality-valid with positive HH on all three dates. A 24 km window centered on the independent geometry centroid, approximately 85.32010° E, 28.14442° N, intersects 6.42 km² of mapping.

**Action:** create an additional event-aligned case and preserve the original Kathmandu case. Select its extent from the independent event question before inspecting candidate detections. A centroid window is illustrative and covers only part of the mapping; choose an explicit scientifically useful extent rather than optimizing the crop to maximize apparent detection.

**Qualification:** footprint intersection and 17 point samples are feasibility evidence, not a completed crop or validation. Audit pixel-wide validity, event chronology, georegistration, source-map date/provenance and uncertainty first. The map depicts preliminary mudflow/rockflow impacts, not flood-water extent. Detection agreement alone cannot create a flood classifier.

Evidence and reproducible script: [event feasibility](reports/2026-10-28/event_aoi_feasibility.json), [script](reports/2026-10-28/check_event_aoi_feasibility.py). Run scripts from the repository root with the project virtual environment and existing raw files.

### B. Real HV observations are already in the downloaded files

All three files contain frequency-A `HVHV`, alongside the currently used `HHHH`. The existing quality-mask and median-processing path was applied to the actual HV crop. All 199 pixels of the HH-selected zone were valid in HV across dates.

| Date | Mean HH shift from first-date baseline | Mean HV shift from first-date baseline |
|---|---:|---:|
| 19 Aug | 0 dB | 0 dB |
| 31 Aug | −7.53 dB | −1.81 dB |
| 12 Sep | −7.08 dB | −2.45 dB |

These are signed means on a fixed common-valid zone, not means of absolute values. The HH-selected zone introduces selection bias. HV is another measurement, not independent event ground truth. Frequency A and B in these LSAR files are L-band subbands, not an L-/S-band pair.

**Action:** show paired HH/HV time traces, same-grid comparisons, and a carefully labeled HH–HV dB difference or linear-power ratio. Explain roughness, moisture, and scattering structure as hypotheses. Water does not always look dark: inundated vegetation can brighten through double bounce. Different polarizations help examine scattering; they do not uniquely identify a disaster. [NASA polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/), [NASA ARSET flood Q&A](https://appliedsciences.nasa.gov/sites/default/files/2022-10/Disasters_Q%26A_Part1.pdf)

Evidence: [HV feasibility](reports/2026-10-28/dual_pol_feasibility.json), [script](reports/2026-10-28/check_dual_pol_feasibility.py).

### C. The public catalog now offers a longer candidate series

A live NASA CMR query returned 17 granules on ten unique acquisition dates for track 98/frame 16: **20 Jun, 2 Jul, 14 Jul, 26 Jul, 19 Aug, 31 Aug, 12 Sep, 24 Sep, 6 Oct, 18 Oct 2026**. Each date has a candidate with the same named `4005_DHDH_A` mode and `P05023` release as the current files. Some additional entries are alternate releases; they are not extra observations.

**Action:** audit metadata and then acquire a consistent subset through NASA/ASF. Seek earlier baseline observations and later persistence/recovery observations. Do not merge processing releases blindly. Header version, calibration, bandwidth, grid, polarization and full-AOI valid coverage still require checking. Missing visits stay missing; the documented mission gap cannot be filled by interpolation. [ASF availability](https://hyp3-docs.asf.alaska.edu/nisar-docs/availability-overview/)

No additional HDF5 products were downloaded this turn. Ten catalog dates are not ten verified processable dates. Evidence: [raw CMR response](reports/2026-10-28/cmr_nepal_candidates.json), [bounded summary and metadata links](reports/2026-10-28/cmr_candidate_summary.json).

## 5. Ambitious project directions worth considering

These are strategic concepts, not implemented features or verified novelty claims. The ranking below reflects reuse and evidence feasibility for this project, not invented numerical judging scores.

| Direction | Memorable interaction and real user benefit | Required evidence / main risk | Recommendation |
|---|---|---|---|
| **TerraPulse: surface-change investigations** | Ask “recovered or merely stopped changing?”; switch consecutive-date and fixed-baseline views, compare HH/HV, open the evidence dossier. Helps researchers and local analysts select defensible inspection targets. | Event-aligned case, longer series, independent corroboration; current physical cause unresolved | **Best next step. Highest reuse; concrete existing-data opportunity** |
| **River Memory** | Follow a floodplain through wetting, recession and persistent riverbank change. Distinguish temporary coverage from a lasting alteration. Useful to river managers and communities. | Check NISAR acquisition modes/coverage for a Bangladesh river case, optical water/shoreline references and water-level records; mixed pixels and inundated vegetation complicate interpretation | Strong local second case after coverage feasibility; no claim to predict future erosion |
| **Wetland Pulse** | Explore seasonal rhythms of open water and inundated vegetation, with explanations of why some flooded surfaces brighten. Supports wetland monitoring and education. | Longer HH/HV series, independent wetland/vegetation references and hydrology; three dates cannot establish a seasonal cycle | Scientifically aligned expansion; defer until temporal evidence exists |
| **Forest Disturbance Witness** | Trace whether a documented fire/clearing leaves persistent radar structure change even after optical greenness returns. Helps distinguish observable recovery dimensions. | NASA FIRMS/USGS imagery and independent disturbance boundaries plus compatible NISAR series; radar ambiguity and phenology | Compelling second process; do not infer biomass or carbon without calibration |
| **Silent Ground** | Map gradual subsidence or eruption-related movement and compare it with infrastructure. High physical-science value. | Appropriate complex/interferometric products, coherence, phase unwrapping, atmospheric/ionospheric treatment, LOS geometry, reference and independent measurements | Larger technical pivot; current GCOV intensity pipeline cannot support it |

A crop/irrigation rhythm explorer is another useful longer-term direction, but would need field calendars or local reference data. Inferring farmer intent from radar alone would be unsound.

## 6. Recommended build sequence and acceptance gates

### Priority 1 — Establish one corroborated physical story

1. Create a separate case manifest for a reference-aligned impact corridor; retain the original case and source hashes.
2. Verify independent map provenance, label meaning, event date and spatial uncertainty. Inspect raw HH/HV quality across the full crop.
3. Freeze the reference polygons and evaluation area before threshold tuning. Include a stable comparison area and explicitly identify no-data regions.
4. Compare observed change with mapped impacts and independently reviewed non-impact/stable locations where available. Document temporal mismatch and mapping incompleteness. Only report precision/recall when positive and negative/reference assumptions are justified; overlap with a preliminary impact map alone is not complete accuracy validation.
5. If corroboration is insufficient, present a measured disturbance with unresolved cause rather than relabeling it to match the desired story.

**Done means:** a user can see the independently corroborated process, its timing bracket, measurement, registration/coverage qualifications and limits. It does not mean every changed pixel is causally classified.

### Priority 2 — Turn Change DNA into observable temporal behavior

1. Add actual HV ingestion and paired traces on a common-valid grid; show separate per-layer coverage and quality.
2. Audit and add compatible earlier/later dates. Retain missing data and exact timestamps.
3. Keep three distinct concepts: consecutive-date change, retained baseline difference, and baseline similarity over observed revisits.
4. Report observed revisit counts and onset intervals. A return toward baseline is descriptive backscatter recovery, not proof of ecological or structural recovery. Keep unobserved recovery censored.
5. Add stable-area comparison and threshold perturbation sensitivity. Call sensitivity robustness, not classification accuracy.

**Done means:** the same zone/date selection drives maps, traces, values, and exports; gaps remain visible; every reported unit and denominator is inspectable.

### Priority 3 — Build the evidence dossier and an explanation ledger

For each selected region, export: case ID, geometry, sensor/collection/granule IDs, timestamps, polarization, units, preprocessing/configuration hash, valid-area denominator, observed values, reference links, caveats and a plain-language finding.

The hypothesis panel should contain **candidate explanation → supporting observation → contradictory observation → missing evidence → suggested next check**. Example hypotheses include moisture changes, vegetation/structure disturbance and residual acquisition/terrain effects. It must allow “insufficient evidence” and overlapping explanations. Do not add unsupported confidence percentages or an LLM-generated physical verdict.

A useful next step is “inspect this cloud-free optical patch or field location”; it is not an unvalidated evacuation instruction. Optional exposure analysis can flag intersections with roads or settlements, but must state source date, spatial uncertainty and that intersection does not establish damage or people affected.

### Priority 4 — Make the first interaction unforgettable and readable

Opening screen: one large map, one plain-language question, a visible date strip and Play control, and a short evidence panel. Keep dates discrete and offer reduced motion. Selecting a region synchronizes every view. Use two clearly labeled map states: **changed since last visit** and **different from first observation**. Never silently change the reference date.

Then reveal HH/HV and independent event context on request. Put experimental hazard and rainfall scenarios in advanced analysis. Reuse existing 3D terrain where it explains topography, while preserving a clear 2D mode. Provide readable units, keyboard focus, colorblind-safe distinctions and legible desktop type; verify at 1366×768 and 1920×1080 with real browser captures.

**Done means:** a first-time viewer can name the change, location, dates, evidence and limitation after a short interaction. Actual user testing and browser inspection are still required; a test count is not usability evidence.

### Priority 5 — Produce submission evidence

Record the real application and a fresh-machine/disconnected rehearsal; verify public repository, video and source links without login. Rebuild the portable release after final changes. Maintain a short claim-to-evidence table and honest team/AI attribution. Document reproducible commands and approximate measured runtime on the actual judging computer rather than inventing hardware benchmarks.

Do not add another region or process until the primary case passes these gates. A focused, convincing result is a stronger submission than broad unsupported claims.

## 7. The memorable scientific interaction already supported

In the existing 199-pixel zone, successive retained candidate area changes from **0.0199 km² to zero**, while the common-zone mean HH difference from the initial baseline remains about **−7.53 dB then −7.08 dB**. The descriptive return toward baseline is only about **6%**; half-recovery was not observed during the 12 days after the measured peak.

Suggested on-screen question: **“The latest change mask is empty. Has the surface returned to its baseline?”** Reveal the fixed-baseline measurement and answer **“The measured backscatter disturbance persists.”** This is an evidence-backed explanation of detection versus persistence. It does not establish a flood, landslide, damage outcome or physical recovery rate.

The next-level achievement is to combine this explanation with a corroborated physical case and a longer timeline. That full experience is proposed, not yet complete.

## 8. Preparing for AI-assisted preselection honestly

The user reports local judges will use AI for an initial screen. No screening model, prompt, weights, acceptance threshold or current official AI-screening rubric was supplied. There is no evidence-based way to guarantee an effortless pass. Prepare materials so both a person and a machine can find and verify the actual contribution.

- Put the exact challenge name, intended user, implemented behavior, actual NISAR collection/dates, one measured result, practical benefit and main limitation near the start of the README and submission.
- Separate **implemented**, **measured**, **hypothesized** and **planned**. Remove contradictions across the README, video, website, exports and submission form.
- Make every major numerical claim traceable to a method and saved output. Do not claim a flood/landslide confidence, displacement, lives saved, predictive accuracy or carbon quantity without supporting measurements.
- Give judges immediate access to source and a real recording. Label older interface screenshots accurately. Do not use generated/mock interface imagery as implementation evidence.
- State what NISAR contributes beyond the supplemental sensors. Provide granule IDs, provisional status, license, source provenance and reproduction instructions.
- Disclose AI assistance and actual team contributions. Do not use prompt injection, hidden instructions, repetitive keywords, fake NASA endorsement or an invented “AI pass score.”

A concise opening could read:

> TerraPulse is an open-source interactive application for Dancing with the SARs that helps users investigate persistent surface change in NASA–ISRO NISAR observations. Its current Kathmandu case compares provisional L2 GCOV observations from 19 August, 31 August and 12 September 2026. Users play actual acquisitions, inspect radar and environmental context, and compare new change with retained differences from the first observation. In one 1.99-hectare zone, the successive change mask disappears while a roughly 7 dB baseline backscatter disturbance remains. The physical cause is unresolved; TerraPulse exposes that limit and the supporting evidence. Flood and landslide indices are exploratory, uncalibrated context. A reference-aligned case, paired HH/HV views and a longer series are the next development priorities.

This is truthful current-state copy, not a statement that the proposed upgrades already exist.

## 9. Presentation plan and local-guide interpretation

The supplied Bangladesh local build guide describes a 240-second local presentation and a separate short global pitch. It explicitly disclaims NASA endorsement. Treat it as local guidance; recheck final organizer instructions before submission. Older 2025 global judging documents are historical reference, not established 2026 rules. Existing `SUBMISSION_BRIEF.md` is a three-minute draft and must be revised for the final format.

**Proposed 240-second story after the upgrades are implemented:**

| Time | What the viewer sees |
|---|---|
| 0–25 s | The real local surface-change question, location and who needs the answer |
| 25–65 s | Actual NISAR dates play; coverage gaps remain visible; a region is selected |
| 65–110 s | Consecutive change versus retained baseline disturbance: the central reveal |
| 110–155 s | Paired HH/HV and independent event reference explain evidence and ambiguity |
| 155–190 s | Evidence dossier and a defensible inspection/research next step |
| 190–220 s | Reproducibility, data provenance and one clear limitation |
| 220–240 s | Why the contribution matters and the next validated expansion |

A 30-second version should communicate one problem, one actual interaction, one measured insight and its benefit. Do not cram the complete feature inventory into it.

## 10. Corrections made during this review

- Fixed Evidence Studio's radar coverage badge: it previously showed flood-model assessability while displaying radar. It now uses the selected radar observation's valid fraction. Regression checks cover latest radar (95.1%), latest flood assessability (94.7%), and baseline radar (99.6%).
- Corrected README statements about displacement, current route capabilities, the older screenshot, terrain range (530.63–2723.65 m), POWER source (MERRA-2 / GEOS-IT), independent validation, and disconnected-runtime verification.
- Added exact processed granule IDs and linked this strategy. Preserved the current README structure and all analytical outputs; no historical science data was rebuilt.
- Saved new raw-file feasibility checks and the live NASA catalog response. No new HDF5 acquisition or second case was implemented in this research turn.

The existing `dist/terrapulse-1.0.0.zip` predates these corrections. Rebuild and verify before distributing an updated submission package.

## 11. Data-source policy and research references

Honor the user's requirement: obtain any new data through non-Chinese organizations/sites. Use NASA/ASF for NISAR, NASA for rainfall/terrain, USGS for Landsat, ESA where useful, and UNITAR/UNOSAT for independent mapping. Check provider, upstream provenance and license per dataset; hosting on an allowed site alone does not establish upstream provenance. This review does not certify legal eligibility or reinterpret NASA restrictions.

Primary research used:

- [NASA NISAR mission](https://science.nasa.gov/mission/nisar/) — mission scope and provisional-data status.
- [ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/) — intensity/covariance interpretation, products and polarization.
- [NASA polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/) — physical scattering context.
- [ASF data availability](https://hyp3-docs.asf.alaska.edu/nisar-docs/availability-overview/) — processing releases, availability and mission gap.
- [NASA JPL OPERA products](https://www.jpl.nasa.gov/go/opera/products/) — existing capabilities and why heatmaps alone are not distinctive; product schedules are not proof of available Nepal products.
- [NASA ARSET flood Q&A](https://appliedsciences.nasa.gov/sites/default/files/2022-10/Disasters_Q%26A_Part1.pdf) — open-water/flooded-vegetation interpretation.
- [Official challenge URL](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/) — unavailable (HTTP 502) during review; supplied full statement used instead.

Scoped audit coverage and remaining checks are recorded in [review coverage](reports/2026-10-28/coverage.json) and [scorecard](reports/2026-10-28/scorecard.md). Those counts are evidence-review coverage, not software accuracy or a judging score.
