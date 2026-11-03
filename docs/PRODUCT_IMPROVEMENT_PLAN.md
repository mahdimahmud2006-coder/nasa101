# TerraPulse — product improvement plan

Updated: 3 November 2026. Working scope: a polished local surface-change investigation product for **Dancing with the SARs**. This is the development tracker; the application presents capabilities and evidence, not a change log.

## Product organization

**Overview → country → investigation → footprint → evidence export.**

- **Bangladesh:** River Memory (Jamuna), Wetland Pulse (Tanguar), Surface change (either of those same study windows).
- **Nepal:** Surface & coherence (June–October record); Evidence dossiers (August–September investigations); Terrain & thermal; Change DNA & slopes; Timeline; Radar comparison.
- **Field guide:** purpose of each tool, measurement meanings, workflow and sources.

Bangladesh Surface change is a different way to investigate the existing two crops, not a third independently acquired location. Nepal's terrain, thermal, rainfall scenarios and original analysis remain separately scoped to their actual inputs. The older root Studio page is now `/studio.html`; `/` opens the overview. Earlier root links carrying a Nepal case are redirected to Studio with their selection.

## Status and acceptance

`IMPLEMENTED` means code and targeted automated checks exist. It does **not** imply rendered browser acceptance, user validation or competition readiness. `WAITING_DATA` requires accepted scientific inputs. `MANUAL_CHECK` requires a person or a permitted browser session. `PLANNED` has not been implemented.

| ID | Priority | Work | Status | Dependency | Acceptance evidence |
|---|---|---|---|---|---|
| UX-01 | P0 | Overview with actual radar comparison and country selection | IMPLEMENTED | Existing local previews | Country keyboard controls, wipe behavior, measured counts and static links checked |
| UX-02 | P0 | Shared country navigation and explicit Nepal tools | IMPLEMENTED | None | Routes, geography, active state and supported shared-state tests |
| UX-03 | P0 | Bangladesh Surface change focus for both crops | IMPLEMENTED | Existing Bangladesh record | Both cases selectable; shared focus restores; original scientific module/data retained |
| UX-04 | P0 | Concise product descriptions and Field guide | IMPLEMENTED | Existing capability audit | HTML/asset checks; source inventory; no invented science |
| UX-05 | P0 | Desktop readability and responsive theme | IMPLEMENTED; visual acceptance pending | Existing source | CSS breakpoints/reduced motion supplied; run manual matrix below |
| SCI-01 | P0 | Complete downloadable Bangladesh intensity slots | IMPLEMENTED | Four GCOV files accepted from database/new | Ten-visit active products; native checks pass; August 5 outage retained |
| SCI-02 | P1 | Additional Nepal coherence pairs | WAITING_DATA | Header-compatible GUNW | Correct native grids, pair intervals, quality masks and playback |
| SCI-03 | P1 | Bangladesh coherence | WAITING_DATA | Compatible Bangladesh GUNW | Separate paired measurements; no replacement of missing GCOV visits |
| REF-01 | P0 | Independent optical corroboration | PLANNED / additional usable references needed | Cloud-screened HLS/Landsat or independently documented reference | Precommitted sampling; dates/validity; disagreement retained; no circular accuracy estimate |
| USER-01 | P0 | Test usefulness with intended users | PLANNED | Team recruits volunteers | Observed task outcomes and feedback, not simulated testimonials |
| QA-01 | P0 | Browser and disconnected presentation rehearsal | MANUAL_CHECK | Policy-permitted browser / user | Checklist completed, failures fixed, fallback recording |
| SUB-01 | P0 | Final submission narrative and eligibility audit | PLANNED | QA + team input + current local requirements | Public access, license, AI disclosure, video and team contributions verified before submission |
| RAIN-01 | P2 | Scientific rainfall context | WAITING_DATA | Accepted rainfall product + full lineage review | Unit/time/area weighting, missingness and quality checked; no zero substitution |
| BD-THERMAL-01 | P2 | Bangladesh thermal context | WAITING_DATA | USGS Landsat temperature + QA | Separate thermal date/resolution/cloud coverage; no thermal values inferred from radar |
| RIVER-02 | P2 | Quantified bank migration | DEFERRED | Independently validated channel/bank boundaries + registration uncertainty | Defensible displacement uncertainty and repeat validation; otherwise retain radar signatures |
| WETLAND-02 | P2 | Validated wetland state / hydroperiod | DEFERRED | Habitat/water labels and sufficiently dense independent time observations | Distinguish occupancy on observed visits from actual duration; report unresolved intervals |
| LOS-01 | P2 | Ground displacement | DEFERRED | Phase unwrapping/reference/correction/geometry validation | Documented sign, reference, units, uncertainty and external checks; never convert raw phase directly into a claimed movement map |

## Completed dataset-dependent implementation: SCI-01

### Required inputs

Four shared NASA Earthdata / ASF GCOV acquisitions: **30 June, 12 July, 10 September and 4 October 2026**; track **069**, frame **014**, ascending; compatible HH/HV mode and processing release. Exact granules, direct NASA URLs and catalog sizes are in [Bangladesh GCOV downloads](BANGLADESH_GCOV_DOWNLOADS.md). Download once for both crops. Place complete files under `database/bangladesh-shared/` or identify their actual location.

The four files in `database/new/` were audited, accepted and imported into the active `bangladesh-v2` record on 3 November 2026. Both Bangladesh crops now have ten observations. See [the implementation report](IMPLEMENTATION_18_BANGLADESH_TEN_VISITS.md) and `reports/bangladesh_import_2026_11_03/native_validation.json`. The 5 August nominal slot lies in a documented satellite outage; it stays missing regardless of additional downloads. GUNW is not a substitute for the missing single-visit GCOV intensity.

### Execution sequence

1. Inventory completed HDF5 files and partial downloads. Check free space against remaining downloads, temporary files and expected output size. A storage check during this turn reported approximately 24 GiB available; recheck before processing. Do not delete source data or earlier release archives automatically.
2. Audit actual headers, acquisition time, track/frame, look direction, channel/bandwidth, processing release/version and per-crop valid coverage. Record flags and source lineage. Reject incompatible inputs with a reason.
3. Build a new Bangladesh record version. Retain the six-visit products and their original support. Preserve the stated reference date; do not silently move it.
4. Compute both crops with HH/HV, fixed-scale previews, reference and successive differences, valid support and profiles. Recompute the common-valid footprint over the longer series and disclose any support change before comparing aggregate results.
5. Rebuild dependent dual-polarization, signature occupancy, persistence, threshold-sensitivity and calendar products in the same new version. An optical match or context control must be rebound and checked against the new observation IDs; it is not automatically valid for an inserted date.
6. Update the active UI registry, probing/reasoning endpoints, exports, homepage record summaries and claim ledger together. The old `investigation_pipeline.run()` writes historical targets; do not use it to overwrite the published six-visit record. Hardcoded API paths require explicit version binding.
7. Validate native samples, masks, finite values, common support, source hashes, observed chronology and exports. Run controller tests covering all Bangladesh modes and shared links. Keep August 5 explicitly unavailable; chart lines stop at the outage.
8. Publish the new **local** active record only after acceptance. Report completed dates and unresolved evidence needs in development documentation. Produce a new release archive once the submission candidate is stable.

**Done means:** both Bangladesh crops display all accepted acquisitions, playback and exports agree, source provenance is inspectable, and the absence of an acquisition is never portrayed as recovery or zero change.

## Next dataset-dependent work: coherence (SCI-02 and SCI-03)

Use [the additional GUNW guide](NISAR_ADDITIONAL_GUNW_DOWNLOADS.md). Prioritize the Nepal July 26–August 19 bridge and the later September–October adjacent pairs. Bangladesh pairs must match the Bangladesh series, not Nepal.

No additional GUNW files were present in this upload. The existing importer accepts 12-day pairs. A 24-day bridge needs explicit interval support in a new version plus tests; it must remain labeled as an endpoint comparison across the outage. Validate referenced RSLC identities, channel, native resolution, quality masks, component labels and footprint alignment. Use only available pairs for playback. Coherence does not identify a cause; raw uncorrected phase remains in radians unless a separately validated displacement workflow is implemented.

## Work that does not need another dataset

- Finish the manual navigation/readability matrix and make fixes against concrete observations.
- Rehearse one complete evidence journey per country using existing measurements.
- Ask intended users to locate a changing footprint, explain baseline versus recent change and export evidence. Record time, errors and explanation quality.
- Refine the submission story around a persistent disturbance and two Bangladesh applications. Link every quantitative assertion to its source or dossier.
- Keep the README, AI-use disclosure, source guide and recorded presentation aligned with actual capability.

Do not keep adding dashboards while the core story, usability and independent validation remain unresolved.

## Manual acceptance matrix

| Check | Required result | Status |
|---|---|---|
| 1920×1080 and 1366×768 desktop | Country and purpose are visible; controls readable; page has no unintended horizontal scroll | Pending |
| 200% browser zoom | Navigation wraps; tools and labels remain usable | Pending |
| Phone-width layout | Cards stack; country tabs and controls remain accessible | Pending |
| Keyboard-only | Country tab arrow keys, visible focus, selects, map inspection, Play/Pause and export work | Pending |
| Reduced motion | No decorative transition; deliberate playback still controlled by the user | Pending |
| Bangladesh journey | All three focuses select correct data; case/date/footprint preserved in shared link | Automated controller checks pass; browser pending |
| Nepal journey | Full radar record, coherence, dossiers and environmental tools clearly scoped | Automated checks pass; browser pending |
| Physical network disconnected | Restart, all views, probes and export work; record fallback video | Pending |

Browser rendering remains unverified under the previously recorded local-URL policy restriction. Source checks and DOM/controller tests do not substitute for these manual checks.

## Release discipline

Track statuses here and in [the machine-readable tracker](PRODUCT_IMPROVEMENT_TRACKER.json). Keep scientific products versioned, thresholds explicit and historical results intact. A new downloaded file is not an accepted observation until header and quality checks pass. Any public deployment or competition submission is a separate user-authorized action. Existing release archives predate this presentation revision.
