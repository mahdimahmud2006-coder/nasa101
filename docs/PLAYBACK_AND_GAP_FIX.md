# Playback and satellite-gap repair — 3 November 2026

The user reported the “Instrument outage” shading and inability to play the expanded record. NASA / ASF currently confirms a **permanent NISAR data gap from 2026-07-27T22:03:25Z to 2026-08-10T00:55:27Z**. This includes the nominal August 7 Nepal and August 5 Bangladesh visits. No additional GUNW file can recreate an acquisition inside that interval. [Official availability notice](https://nisar-docs.asf.alaska.edu/availability-overview/).

## Repairs

- Replaced the short chart label with **Satellite data gap** and an explicit dated source explanation. Chart lines now break across the gap rather than drawing a dashed connector that could look like an estimated path.
- Removed the deliberate coherence-mode playback restriction. The player builds its sequence from available saved measurements: ten intensity visits, two supplied coherence pairs, or nine available preceding-visit differences. It never animates a missing source frame as an observation.
- Added synchronized Play/Pause controls immediately above the map and in the timeline, Previous/Next, a visible frame/date status, playback range and Loop. Coherence playback labels actual pair endpoints.
- Added bounded frame loading and a local retry message if a source preview is missing or stalls, preventing an endless loading state. Existing actual-date selection, common footprints and evidence export remain available.

The old source directly disabled Play and speed controls for coherence. For HH/HV, a real-browser failure was not independently reproduced under the existing local-URL policy block; the added visible transport, error messages and actual timer-driven controller regressions address the observable workflow and loading risks without claiming a confirmed browser-specific cause.

## Additional data

No additional dataset is necessary for playback. [The download guide](NISAR_ADDITIONAL_GUNW_DOWNLOADS.md) provides exact original NASA HDF5 URLs, interval dates, sizes and priority. Four recommended Nepal candidates total **8.785 GiB**: July 26→August 19 (24-day observed endpoint comparison), September 12→24, September 24→October 6 and October 6→18. Three earlier Nepal pairs and two known Bangladesh pairs are optional. Download each shared scene once and retain original filenames in `database/extra datasets/`.

The 24-day bridge is useful additional endpoint evidence; it does not fill the satellite gap and needs explicit long-interval support and header/quality checks before import. Catalog screening alone is not accepted science. Nepal search completed; Bangladesh returned incomplete results, so the two returned candidates are not an exhaustive list. Exact responses, timestamps and hashes are saved under `data/candidates/additional_gunw_2026_11_03/`. No science file was downloaded. Hosts are NASA / ASF (USA), mission NASA–ISRO (USA/India); no Chinese provider/site is used for these links.

## Verification and delivery

The complete JavaScript suite passes **86 tests**, including button-driven traversal of all ten visits, both coherence pairs, crossing from July 26 directly to August 19, selected ranges, looping, pause, missing files and stalled loads. Static source checks pass for all six pages. All 795 frozen baseline files pass, and every expanded scientific asset reconciles with its saved hash. No raw dataset, original result, processing threshold, observation timestamp or release archive was modified.

Evidence: `reports/playback_2026_11_03/{javascript.log,static_web.json,baseline.log,summary.json}`. Controller tests use explicit DOM/image doubles and controlled timers. Real-browser visual/interaction acceptance remains unverified under the previously recorded policy block; no alternate browser or indirect rendering workaround was attempted.

The live source at [port 8001](http://127.0.0.1:8001/expanded.html) serves this repair. **Reload once with Ctrl+Shift+R** to replace already loaded scripts. Click **Play visits** above the map; choose a coherence layer for **Play pairs**, or use range and Loop. Existing portable archives remain dated snapshots and predate this UI repair; they were preserved rather than overwritten.
