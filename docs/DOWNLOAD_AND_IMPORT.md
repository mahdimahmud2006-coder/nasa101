# TerraPulse: download and import the next observations

**Import update, 31 October 2026:** the six priority files are present and processed for **both** Jamuna and Tanguar Haor. Do not download duplicate haor files for these dates. See [the import results](IMPLEMENTATION_09_BANGLADESH.md). To rebuild only Jamuna use `make jamuna`; only the haor use `make wetland`. The instructions below retain the original download recipe for additional installations.

Catalog checked on **28 October 2026**. Keep the TerraPulse name; Surface investigations, River Memory and Wetland Pulse are three workspaces in the same project.

## Start with one shared Bangladesh download

**The same full-scene files cover both planned sites**, according to the NASA CMR catalog polygons:

| Workspace | Planned location | Center (longitude, latitude) | Processing window |
|---|---|---|---|
| River Memory | Jamuna near Sirajganj, Bangladesh | 89.71, 24.49 | 20 × 20 km |
| Wetland Pulse | Tanguar Haor region, Bangladesh | 91.08, 25.10 | 18 × 16 km |

These are geographic investigation windows, not surveyed riverbank or habitat boundaries. Catalog footprints do not certify every pixel; raw coverage will be checked during import.

1. Sign in to [NASA Earthdata Search](https://search.earthdata.nasa.gov/) with your Earthdata account. An account is required for downloading NASA/ASF NISAR products; do not share credentials in chat.
2. Find collection **`NISAR_L2_GCOV_PROVISIONAL_V1`** (NISAR Provisional Geocoded Polarimetric Covariance, Version 1). The provider is **NASA Earthdata / ASF DAAC**. Choose GCOV `.h5` science files.
3. Search 17 June–28 October 2026. Draw the Jamuna search box (west 89.59°, south 24.37°, east 89.83°, north 24.61°), or locate the exact granules listed below. The selected full scenes also cover the wetland window; do not download a second copy for it.
4. Match **track 069, ascending A, frame 014, `4005_DHDH_A`, release `P05023`** in the filenames. Product `GCOV`, frequency-A HH/HV terms are required. Other tracks, frames, QP modes or releases are not interchangeable.
5. Download the six priority science files. Preserve the complete original filenames and `.h5` extension. Browse PNGs and metadata files do not replace the science files.

| Priority date | Expected use in the series |
|---|---|
| 2026-06-18 | Earliest selected observation; not assumed to be dry or pre-event |
| 2026-07-24 | Earlier comparison visit |
| 2026-08-17 | Mid-series observation |
| 2026-08-29 | Next repeat visit |
| 2026-09-22 | Later observation |
| 2026-10-16 | Latest selected observation |

**Exact IDs:** [six priority granules](downloads/bangladesh-priority-granules.txt). **Direct NASA/ASF links:** [six science-file URLs](downloads/bangladesh-priority-urls.txt). Authenticated browser sessions or Earthdata download workflows may be needed for those links.

Estimated catalog volume is **about 38 GiB for six files**; reserve at least **50–60 GB free** for raw data plus local processing outputs. These are approximate dataset-storage estimates, not measured PC performance requirements.

If bandwidth/storage allow, also get **30 June, 12 July, 10 September and 4 October**: [all ten IDs](downloads/bangladesh-all-granules.txt), [all ten links](downloads/bangladesh-all-urls.txt). Ten files total approximately **63 GiB**; allow additional workspace headroom. A denser series is more informative, but three compatible visits are the minimum the importer accepts. Three visits cannot establish a seasonal climatology.

The plan and metadata evidence are saved in [download-plan.json](downloads/download-plan.json) and `data/catalogs/2026-10-28/`. Full raw headers, calibration/version comparability and pixel coverage still need to pass ingestion checks. Do not mix beta and provisional data or alternate reprocessing releases.

## Save them here and build

Put all shared Bangladesh files in:

```text
/home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/database/bangladesh-shared/
```

Then run:

```bash
cd "/home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1"
make investigations
```

This checks the source metadata and quality, processes the matching files, and activates **both** Bangladesh workspaces when at least three compatible observations pass. It also rebuilds the two Nepal investigation cases. A corrupt, incompatible or insufficient-coverage file raises an error; it is not silently treated as a valid observation. An interrupted or partially downloaded `.h5` must finish before import.

Start the local application:

```bash
./run.sh
```

Open **http://127.0.0.1:8000/investigations.html**. If a server was already running before this update, stop it with Ctrl+C and start it again so it loads the new API routes. After subsequent successful imports, reload the page. Use a second terminal for building while the server runs; avoid viewing a case during its rebuild.

## Optional: extend the existing Nepal series

The three existing local files already power the two Nepal investigation cases; **no new Nepal download is needed to use those now**. For a longer timeline, prioritize these same-track/frame/mode/release catalog candidates:

- 2026-06-20 and 2026-07-26 for earlier observations.
- 2026-09-24 and 2026-10-18 for later observations.

Use collection `NISAR_L2_GCOV_PROVISIONAL_V1`, track **098**, ascending **A**, frame **016**, mode **`4005_DHDH_A`**, release **`P05023`**. Exact candidate IDs and metadata links are in [the Nepal candidate summary](reports/2026-10-28/cmr_candidate_summary.json). Save additional files, with original filenames, under **`database/nepal-series/`**, then rerun `make investigations`. The importer combines that folder with the three explicit existing files and rejects duplicate acquisition times or physical incompatibilities.

## Supplemental evidence: second priority

Do not delay the six shared radar downloads for these. The investigation can process NISAR first, while physical interpretations remain unresolved.

- **Optical context:** [NASA HLS](https://hls.gsfc.nasa.gov/data-access-and-tools/) Landsat or Sentinel-2 surface reflectance, such as `HLSL30` / `HLSS30` version 2.0, with the Fmask quality layer. Seek clear observations near the radar dates for the two Bangladesh windows. These are follow-up candidates, not yet catalog-screened granule recommendations or an implemented new HLS importer. HLS uses USGS Landsat/ESA Sentinel-2 inputs through NASA; inspect full provenance.
- **Terrain and regional rainfall:** existing NASADEM and NASA POWER acquisition code can supply appropriate context after the Bangladesh case grids are verified. Existing Nepal context is not reused as Bangladesh measurements.
- **Independent water/shoreline/habitat evidence:** cloud-free independently inspected optical observations or a trusted documented survey/reference are needed before describing signatures as confirmed water, bank erosion or inundated vegetation. A static water map alone does not validate a date-specific transition.

All new sources must meet the user's **non-Chinese organization/site** requirement. Provider, upstream data origin, license and temporal/spatial fitness should be documented per source. No competition/legal eligibility certification is implied.

References: [ASF Earthdata Search instructions](https://nisar-docs.asf.alaska.edu/earthdata-search/), [ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/), [ASF authentication and search](https://nisar-docs.asf.alaska.edu/asf-search/).
