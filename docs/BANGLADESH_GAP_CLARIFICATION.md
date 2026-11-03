# Bangladesh acquisition gaps — River Memory and Wetland Pulse

Checked 3 November 2026. Both views still have six actual Bangladesh acquisitions. A fresh recursive local inventory finds no additional Bangladesh GCOV files: the newly supplied extra files belong to Nepal track 98 / frame 16. The Bangladesh cases require track 69 / frame 14. The existing results have not been reset.

## What the screenshots show

| Date, 2026 | Why missing | Action |
| --- | --- | --- |
| June 30 | Compatible GCOV candidate, file absent locally | Download the shared Bangladesh GCOV |
| July 12 | Compatible GCOV candidate, file absent locally | Download the shared Bangladesh GCOV |
| August 5 | Nominal slot inside the permanent satellite outage | No NISAR acquisition exists to recover |
| September 10 | Compatible GCOV candidate, file absent locally | Download the shared Bangladesh GCOV |
| October 4 | Compatible GCOV candidate, file absent locally | Download the shared Bangladesh GCOV |

The permanent outage is 2026-07-27T22:03:25Z → 2026-08-10T00:55:27Z, confirmed again in the [NASA / ASF notice](https://nisar-docs.asf.alaska.edu/availability-overview/). August 5 is the Bangladesh nominal visit inside it. GUNW can compare observed endpoints across an outage; it cannot restore an acquisition inside it.

The other four slots require **GCOV intensity**, not GUNW coherence and not Nepal scene files. [Exact NASA download links](BANGLADESH_GCOV_DOWNLOADS.md) total **25.055 GiB**. Download once for both Jamuna and Tanguar; retain original filenames in `database/bangladesh-shared/`. Catalog compatibility must be followed by header/native-quality checks before a new versioned import. After those four files are accepted, only the August 5 satellite slot remains missing within this nominal calendar.

## Interface repair

The shared acquisition-record card now clearly separates GCOV visits not loaded in this saved record from permanent satellite unavailability. Both Bangladesh modes display direct NASA GCOV links on the four actionable dates, file sizes, shared-folder instructions and the total. August 5 has no download button and explicitly says it cannot be recovered by download. There is no invented new observation or reclassification of a missing scene as observed.

HH/HV and CPR charts now break across the satellite outage **and** across unloaded repeat visits. Actual sample points and observed-endpoint differences are preserved. The previously used dashed connectors and their explanatory copy are replaced so they cannot look like an estimated continuous trajectory.

The “Scientific IMERG unavailable” text in the screenshot is separate rainfall context; importing the four radar files does not create missing rainfall measurements. Original frozen Final-product rain/null records remain preserved.

## Verification

The complete JavaScript suite passes **90 tests**, including both Bangladesh modes, exactly four actionable GCOV links, an undownloadable outage slot and line breaks in HH, HV and CPR without losing observed endpoint points. Source/static checks pass for all six pages. All 795 frozen baseline files pass. All historical Bangladesh scientific outputs and the original versioned calendars match their earlier saved hashes. Fresh NASA metadata searches completed for both crop polygons and returned ten compatible dated candidates: six loaded and four not in hand. No scientific raster was downloaded.

Source records: `reports/bangladesh_gap_2026_11_03/` and `data/candidates/bangladesh_gcov_gaps_2026_11_03/`. Real-browser visual acceptance remains unverified under the earlier local-URL policy block; explicit DOM/image tests are not a browser-rendering claim. No alternate browser or indirect-rendering workaround was attempted.

Open [River Memory](http://127.0.0.1:8001/investigations.html?mode=river) or [Wetland Pulse](http://127.0.0.1:8001/investigations.html?mode=wetland), then reload with Ctrl+Shift+R. The user-owned local service serves the updated source files; existing portable archives remain earlier snapshots and are not overwritten.
