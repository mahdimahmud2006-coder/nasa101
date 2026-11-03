# Implementation 17 — supplied-data Nepal extension

Implemented 3 November 2026, Asia/Dhaka. This extends the existing TerraPulse project; no original investigation, historical measurement or release archive is replaced.

## Inputs accepted

The supplied `database/extra datasets/` directory contains seven additional Nepal GCOV files and two GUNW files. All nine are readable. Their declared organizations are NASA / JPL / ASF (USA) and ISRO (India); GUNW auxiliary provenance names European/US/international sources. No Chinese provider is identified in the declared metadata. This is a declared-lineage review, not a certificate about every upstream contributor.

| Product | Actual acquisitions / pairs | Use |
| --- | --- | --- |
| GCOV | June 20, July 2, July 14, July 26, September 24, October 6, October 18 | Extend each Nepal crop from three to ten actual visits |
| GUNW | August 19 → August 31; August 31 → September 12 | Native 20 m and 80 m HH coherence and quality evidence |

Compatibility checks use headers, including L2 / PR / P05023 / version 1.0.11, ascending track 98 / frame 16, left-looking, frequency A, source HH/HV mode and 40 MHz range bandwidth. The single-HH GUNW output mode is checked against its original dual-polarization RSLC inputs rather than rejected by its derived filename. Both crops use their original 10 m GCOV grids. Every new HH/HV extraction exceeds the 80% minimum valid crop coverage.

Two differences are explicitly retained in `source_header_audit.json`: the July 14 filename carries an F flag while the header says nominal processing and zero input-data exception; September 24 has an urgent-observation header flag while retaining the PR/P05023 product configuration. Both have compatible measured source geometry/mode and accepted crop coverage. These flags have not been silently normalized.

## What is implemented

Open [Expanded Nepal record](http://127.0.0.1:8000/expanded.html), also linked near the top of Investigations. The new desktop workspace provides:

- Both Nepal crops, ten actual observation buttons, a date slider and playback that waits for saved frames. No outage visit is synthesized.
- Fixed-scale HH, HV, CPR (HV−HH), HH/HV/CPR differences from August 19 and HH differences from the previous actual visit. The first visit has no previous-visit difference.
- An elapsed-time HH/HV chart with the instrument outage shaded; the playback repair breaks lines across the gap. August 19 remains the explicit comparison reference even though earlier observations are now available.
- Preserved tracked/mapped footprints and a whole-crop profile. Every intensity trace uses the same pixels valid in HH and HV across all ten visits. A point inspector follows an edge-clipped 11×11 native neighborhood; keyboard arrows/Enter also work.
- Pair-specific native 20 m and 80 m coherence maps, fixed 0–1 display limits, valid support, mean and median coherence. No value is assigned to a visit without a supplied pair ending there. The subsequent playback repair enables the two available pair frames with their actual intervals, range controls and Loop; see [the playback repair](PLAYBACK_AND_GAP_FIX.md).
- Native HH/HV COG downloads, coherence/quality/phase/ionosphere COGs, exact source identities and window hashes, immutable asset checksums and an exported evidence dossier. Unwrapped phase is in uncorrected radians, never centimeters.
- Shareable crop/date/layer/footprint or neighborhood links. Responsive layouts, readable type, visible focus, text summaries and local-only assets are implemented.
- A new active claim snapshot, `claims-expanded-v2`, and an updated Nepal coherence panel in the original workspace. The historical closed-gate snapshots remain unchanged. Original Change DNA and HLS references stay scoped to their original dates and do not inherit the new coherence or new optical matches.

## What the longer record tells us

The original Kathmandu footprint remains **199 common-valid pixels across all ten visits**. Its August 31 and September 12 HH differences remain exactly the previous findings, about −7.5263 and −7.0766 dB. By October 18 the HH difference is about **−6.5660 dB relative to August 19**. Earlier dates also vary, so August 19 is not independently established as an undisturbed surface. The longer record extends a measured backscatter finding; it does not establish continuous persistence, physical damage, exact onset or recovery.

The corridor retains the same mapped footprint geometry (64,191 native pixel centers), with 62,820 pixels common-valid across the expanded series versus 62,829 in the old three-date series. Its new means use the smaller explicitly stated support. The original means and original support are preserved.

Coherence summaries describe the enclosing native crop, **not** the selected intensity footprint. Their 20 m / 80 m support and estimates differ. No damaging-process classifier, probability, calibrated coherence threshold or ground displacement is inferred.

## Quality and provenance

Coherence validity requires finite values in [0,1], valid source subswaths in both acquisitions, no reference/secondary anomaly bits and nonfill masks. The source water flag is not treated as invalid. Phase-assessable support additionally requires finite phase and nonzero/nonfill connected components. This is a quality screen, not unwrap correctness or displacement validation. Native enclosing GUNW crop extents may extend slightly beyond the 10 m investigation rectangle; grids and bounds remain explicit.

The original raw files remain intact. Full raw-file cryptographic integrity is not asserted: processing retains native extraction hashes, exact identities, file sizes and derived-asset checksums. The source audit records header flags, wavelength from center frequency, declared auxiliary lineage, correction/geolocation dataset inventories and small metadata values; large source orbit/correction arrays stay in the original HDF5. Phase sign and reference point have not been validated for displacement.

[NASA / ASF GUNW documentation](https://nisar-docs.asf.alaska.edu/gunw/) describes the native coherence/phase grids and notes that ionosphere and external phase corrections must not be assumed applied. [The availability overview](https://nisar-docs.asf.alaska.edu/availability-overview/) supports the July 27–August 10 outage; the nominal August 7 Nepal and August 5 Bangladesh gaps remain unfillable by another NISAR acquisition from that outage.

Inspect `reports/extra_2026_11_03/input_inventory.json`, `source_header_audit.json`, `validation.log`, `verification_preservation.json` and `make_verify.log`. Native source comparisons cover every coherence crop/mask and 28 independently extracted GCOV interior samples; samples are not a full raw-file audit. All generated assets are hashed. UI tests use explicit DOM/image doubles and do not establish rendered-browser acceptance.

## Remaining inputs and work

| Remaining item | Need | Effect |
| --- | --- | --- |
| River Memory / Wetland Pulse | Shared Bangladesh GCOV: June 30, July 12, September 10, October 4 | Densify both existing six-date records; these files were absent from this upload |
| Rain context | Regional scientific IMERG Late V07 subsets with precipitation, half-hour bounds, units, fill/QA and provenance | Late catalog candidates exist, but no rain measurements were supplied or imported; frozen Final/null records remain unchanged |
| Optical/thermal validation | Additional eligible dated source pixels, cloud masks and declared provenance | No new reference matches or Bangladesh thermal data in this batch |
| Ground displacement | Reviewed reference, connected-component/unwrap assessment, phase sign and corrections | Current phase/coherence alone does not satisfy this gate |
| Final acceptance | Real-browser/accessibility/GPU check, physical disconnected rehearsal and clean judging-machine startup | Still unverified under the existing recorded browser policy block |

The earlier [dataset PDF and exact download manifest](../output/pdf/TerraPulse_Data_Gaps_and_Capabilities.pdf) remain a dated request snapshot. NASA/ASF sources in that report still identify the missing Bangladesh inputs. Do not redownload the accepted Nepal files. Future Bangladesh imports must remain on track 69 / frame 14 and never be merged into the Nepal acquisition series.

## Run and reproduce

Start the existing local app with `./run.sh`; open `/expanded.html`. Restart an older running server after backend updates so the new neighborhood endpoint is loaded. No additional Python runtime dependency or Earthdata credential is needed to view saved results.

`make expanded` refuses to replace published `expanded-v1` products. A future rebuild must choose a new version. `make validate-expanded` checks published native source windows, quality values/masks, grid resolution, hashes, reference semantics and preserved original values. `make verify` includes this validator and the expanded workspace tests. Full source verification requires the separately retained raw files; portable runtime verification uses `scripts/verify_release.py`.

## Verification outcome

`make verify` passes: **255 Python tests, 80 JavaScript tests, twelve analytical validators**, runtime readiness and static checks for all six pages. The 105 existing dependency warnings remain visible. Verification preserves all 1,606 current published outputs; the original 1,379-file inventory and the 795-file baseline are checked separately. The one historical timing report rewritten by its validator is retained under the new QA directory and restored to its original bytes.

The current updated server uses **port 8001** because an older process occupied port 8000. Open [the running updated workspace](http://127.0.0.1:8001/expanded.html). The standard fresh startup remains `./run.sh` on port 8000; use `./run.sh --port 8001` if that port is occupied.

The dated portable extension package is `dist/terrapulse-1.0.0-expanded-20261103-r2.zip`, with exact build/integrity records in `reports/extra_2026_11_03/package.json` and its adjacent SHA-256 sidecar. Earlier archives predate this extension and remain immutable. A package integrity check verifies bytes, not browser or clean-machine acceptance.

The full verification checkpoint logged 77 JavaScript tests. After three final shared-link/cursor/loading regression cases were added, the complete JavaScript suite passes 80 tests in `javascript_final.log`; source/static checks and targeted release tests also pass.

The first extension archive is also retained. The `-r2` candidate includes the final guard for measurement controls during a delayed case load; its exact integrity record is `reports/extra_2026_11_03/package-r2.json`.
