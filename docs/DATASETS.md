# Dataset provenance

Primary dataset: **NASA–ISRO NISAR Provisional Geocoded Polarimetric Covariance, Version 1**, Level 2, L band. Collection identifier: `NISAR_L2_GCOV_PROVISIONAL_V1`. Product DOI from the actual identification datasets: [10.5067/NIL2GCOV-P1](https://doi.org/10.5067/NIL2GCOV-P1). Official [NASA collection description](https://data.nasa.gov/dataset/nisar-provisional-geocoded-polarimetric-covariance-product-version-1-d9e04) and [ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/). Product status: **PROVISIONAL**; partially validated.

## Supplied files

| Local filename | UTC acquisition start | Internal product version | Release | Selected |
|---|---|---|---|---|
| aug19.h5 | 2026-08-19T23:39:18 | 1.0.11 | P05023 | Yes |
| aug19(1).h5 | 2026-08-19T23:39:18 | 1.0.12 | X05026 | No |
| aug31.h5 | 2026-08-31T23:39:18 | 1.0.11 | P05023 | Yes |
| aug31(1).h5 | 2026-08-31T23:39:18 | 1.0.12 | X05026 | No |
| sept12.h5 | 2026-09-12T23:39:18 | 1.0.11 | P05023 | Yes |
| sept12(1).h5 | 2026-09-12T23:39:18 | 1.0.12 | X05026 | No |

The supplied archive `aug19.zip` contained a byte-for-byte copy of the retained and audited `aug19.h5`. Local filenames are preserved, while original granule identity comes from the file's own `identification/granuleId`.

Selected granule IDs:

```
NISAR_L2_PR_GCOV_028_098_A_016_4005_DHDH_A_20260819T233918_20260819T233953_P05023_N_F_J_001
NISAR_L2_PR_GCOV_029_098_A_016_4005_DHDH_A_20260831T233918_20260831T233952_P05023_N_F_J_001
NISAR_L2_PR_GCOV_030_098_A_016_4005_DHDH_A_20260912T233918_20260912T233952_P05023_N_F_J_001
```

Track 98, frame 16, ascending, left looking, EPSG:32645. HH and HV terms exist in both frequency A (10 m) and frequency B (80 m). Selected term **HHHH / HH / frequency A** is real-valued, dimensionless diagonal covariance. Science image shape: 33840 × 34488; coordinates are pixel centers. Actual x spacing 10 m and y spacing −10 m, first center x=126725 m, y=3347275 m. Native fill is NaN in `_FillValue`; allocation fill is zero. Both are invalid for positive-power dB conversion.

Discovered paths used:

```
/science/LSAR/identification/{granuleId,zeroDopplerStartTime,zeroDopplerEndTime,productType,productLevel,productVersion,productDoi,trackNumber,frameNumber,absoluteOrbitNumber,orbitPassDirection,lookDirection,boundingPolygon}
/science/LSAR/GCOV/grids/frequencyA/HHHH
/science/LSAR/GCOV/grids/frequencyA/mask
/science/LSAR/GCOV/grids/frequencyA/numberOfLooks
/science/LSAR/GCOV/grids/frequencyA/{xCoordinates,yCoordinates,xCoordinateSpacing,yCoordinateSpacing,projection,listOfCovarianceTerms}
```

The actual inventory includes all source datasets, not only these paths. Mask descriptions are read from the source attributes; 0 and 255 are excluded. No cloud mask, rainfall record, optical scene or event ground truth is available here.

## Obtain source data

Search [ASF Vertex](https://search.asf.alaska.edu/) for NISAR GCOV track 98/frame 16 on the dates above, selecting the matching granule IDs and product release, or find the collection in [NASA Earthdata Search](https://search.earthdata.nasa.gov/). Downloads may require an Earthdata account. Direct per-granule download URLs were not supplied and are not invented. Place the matching local files at the project root, or edit `config.json` to point to their original filenames and raw directory; then run the audit on that directory before processing.

Demo assets are included locally so judging never depends on NASA availability. NASA data and Copernicus ancillary DEMs retain their own access and licensing terms. The MIT license applies to the TerraPulse code.


## Added environmental and thermal sources

NASA POWER hourly regional precipitation and Microsoft-hosted NASADEM are documented in `docs/IMPLEMENTATION_03.md`. Four Tier-1 USGS Landsat 8/9 Collection 2 Level-2 thermal/optical scenes (August 18/26, September 11/19, 2026) were subsequently downloaded through Microsoft Planetary Computer. Raw AOI windows, STAC records, unsigned source URLs and SHA-256 checksums are saved under `data/context/thermal/`.

Thermal conversion and quality rules are recorded in `data/derived/nepal_case_01/thermal/manifest.json`. QA/uncertainty gaps remain nodata. Native TIRS detail is 100 m; delivery/analysis grids are 30 m. Thermal and optical observations are independent of the NISAR acquisition times and are not flood-score training labels. See `docs/IMPLEMENTATION_04_05.md` and `docs/RESEARCH_AND_REDESIGN_04_05.md` for source selection, restrictions and limitations.

## Change DNA and landslide reference extension (14 October 2026)

Change DNA derives only from the existing compatible NISAR series and fixed-zone measurements. Landslide susceptibility uses the existing NASADEM, NASA POWER and compatible NISAR inputs; it introduces no new radar dates or higher-resolution rainfall measurements.

The NASA/GSFC Global Landslide Catalog CSV was obtained through `data.nasa.gov` and its NASA-owned AWS distribution bucket. The downloaded file contains 11,033 historical records; only 10 nominal study-AOI records from the explicit non-Chinese report-host allowlist are retained. `data/context/landslide/references.json` records the full-download SHA-256, subset SHA-256, hosts, references and location-accuracy fields. No linked report/news host was contacted. Two reports meet the ≤1 km screening rule, in two spatial blocks; this is insufficient for empirical validation. An official USGS earthquake inventory metadata request returned HTTP 403 and contributed no data.

Citations: Kirschbaum et al. (2010), https://doi.org/10.1007/s11069-009-9401-4; Kirschbaum et al. (2015), https://doi.org/10.1016/j.geomorph.2015.03.016. The public NASA catalog is historical and media-biased, not a complete current inventory. See `docs/IMPLEMENTATION_06_07.md` for source decisions and computed results.

## Implementation 08: paired investigations and pending Bangladesh series

The new Nepal investigation cases reuse the three full NISAR files listed above, adding actual frequency-A **HVHV** to **HHHH**. Both are L-band intensity/covariance diagonals. The new reference-aligned crop is centered at approximately 85.32010° E, 28.14442° N and intersects 6.4230 km² of preliminary independent mapped impacts after native-grid snapping. The original Kathmandu case and outputs remain intact.

For the planned Jamuna and Tanguar Haor cases, public NASA CMR queries on 28 October 2026 found shared provisional GCOV candidates on track **069**, ascending **A**, frame **014**, mode **4005_DHDH_A**, release **P05023**. All ten catalog footprints contain both planned search boxes. Six priority dates: **18 June, 24 July, 17 August, 29 August, 22 September, 16 October 2026**. Exact IDs and authenticated science-file links are in [the download guide](DOWNLOAD_AND_IMPORT.md) and [download plan](downloads/download-plan.json). Raw catalog responses are retained under `data/catalogs/2026-10-28/`.

These Bangladesh files are **not yet downloaded/processed by the agent**. Raw-header comparability and pixel validity remain pending. The application explicitly reports `AWAITING_DATA`. The same files support both geographic crops; one copy goes in `database/bangladesh-shared/`. Provider: NASA Earthdata / ASF DAAC. Supplemental sources must continue to satisfy the user's non-Chinese-source requirement.

## Bangladesh raw-data import — 31 October 2026

The user supplied the **six Jamuna-requested full-scene HDF5 files**, with original catalog filenames, in `database/bangladesh-shared/`. Their embedded identities match the prior NASA/ASF request. These files are now processed for Jamuna (EPSG:32646, 2000 × 2000 at 10 m) and, because the same full scenes include the second location, Tanguar Haor (1600 × 1800 at 10 m). **No separate haor upload or download was used.** All six dates have compatible product version 1.0.11, P05023 release and 40 MHz frequency-A HH/HV data.

The previous awaiting-data descriptions record the initial 28 October build and are superseded by this import. Paired-valid coverage is 99.8001% for Jamuna and 99.7640% for the haor. These are measurement-coverage checks, not water/erosion/habitat validation. See [Implementation 09](IMPLEMENTATION_09_BANGLADESH.md) and [the source audit](reports/bangladesh_2026_10_31/source_audit.json). No new external dataset was downloaded by the agent during this import.
