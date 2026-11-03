# TerraPulse — Phase 1 download candidates

**Prepared:** 2 November 2026 (Asia/Dhaka). **Status:** catalog-screened candidates; no radar files downloaded. Approval is required before any large transfer.

All candidates come from NASA Earthdata / ASF DAAC (USA), upstream NASA–ISRO NISAR (USA/India). Required series: ascending, GCOV PR, 4005_DHDH_A, main-band HH/HV at 40 MHz, CRID P05023. Header product version, look geometry, quality masks and canonical-grid compatibility must still pass the existing ingest audit. Catalog compatibility is not a completed scientific audit.

## Recommended first batch: Bangladesh

These four files serve **both Jamuna and Tanguar Haor**. They would raise each series from 6 to 10 loaded visits if the ingest audit succeeds. August 5 remains the official instrument gap.

| Acquisition UTC | Full HDF5 size (GiB) | Bytes |
|---|---:|---:|
| 2026-06-30T23:21:34Z | 6.1953 | 6,652,166,144 |
| 2026-07-12T23:21:34Z | 6.2266 | 6,685,720,576 |
| 2026-09-10T23:21:31Z | 6.4023 | 6,874,464,256 |
| 2026-10-04T23:21:32Z | 6.2305 | 6,689,914,880 |

**Bangladesh: track 69 / frame 14 total: 25.0547 GiB.**

- `NISAR_L2_PR_GCOV_024_069_A_014_4005_DHDH_A_20260630T232134_20260630T232209_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_024_069_A_014_4005_DHDH_A_20260630T232134_20260630T232209_P05023_N_F_J_001/NISAR_L2_PR_GCOV_024_069_A_014_4005_DHDH_A_20260630T232134_20260630T232209_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_025_069_A_014_4005_DHDH_A_20260712T232134_20260712T232208_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_025_069_A_014_4005_DHDH_A_20260712T232134_20260712T232208_P05023_N_F_J_001/NISAR_L2_PR_GCOV_025_069_A_014_4005_DHDH_A_20260712T232134_20260712T232208_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_030_069_A_014_4005_DHDH_A_20260910T232131_20260910T232206_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_030_069_A_014_4005_DHDH_A_20260910T232131_20260910T232206_P05023_N_F_J_001/NISAR_L2_PR_GCOV_030_069_A_014_4005_DHDH_A_20260910T232131_20260910T232206_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_032_069_A_014_4005_DHDH_A_20261004T232132_20261004T232206_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_032_069_A_014_4005_DHDH_A_20261004T232132_20261004T232206_P05023_N_F_J_001/NISAR_L2_PR_GCOV_032_069_A_014_4005_DHDH_A_20261004T232132_20261004T232206_P05023_N_F_J_001.h5).

[Full query, results and compatibility reasons](../data/candidates/phase1_2026_11_02_final/bangladesh_069_014.json).

## Optional second batch: Nepal

These four files would extend both Nepal crops from 3 to 7 visits if ingestion succeeds. August 7 remains an instrument gap. October 30 has only an incompatible UR product in this search; it is not a PR/P05023 candidate.

| Acquisition UTC | Full HDF5 size (GiB) | Bytes |
|---|---:|---:|
| 2026-07-26T23:39:19Z | 6.7422 | 7,239,368,704 |
| 2026-09-24T23:39:18Z | 6.5625 | 7,046,430,720 |
| 2026-10-06T23:39:18Z | 6.5586 | 7,042,236,416 |
| 2026-10-18T23:39:18Z | 6.5664 | 7,050,625,024 |

**Nepal: track 98 / frame 16 total: 26.4297 GiB.**

- `NISAR_L2_PR_GCOV_026_098_A_016_4005_DHDH_A_20260726T233919_20260726T233954_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_026_098_A_016_4005_DHDH_A_20260726T233919_20260726T233954_P05023_N_F_J_001/NISAR_L2_PR_GCOV_026_098_A_016_4005_DHDH_A_20260726T233919_20260726T233954_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_031_098_A_016_4005_DHDH_A_20260924T233918_20260924T233952_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_031_098_A_016_4005_DHDH_A_20260924T233918_20260924T233952_P05023_N_F_J_001/NISAR_L2_PR_GCOV_031_098_A_016_4005_DHDH_A_20260924T233918_20260924T233952_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_032_098_A_016_4005_DHDH_A_20261006T233918_20261006T233952_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_032_098_A_016_4005_DHDH_A_20261006T233918_20261006T233952_P05023_N_F_J_001/NISAR_L2_PR_GCOV_032_098_A_016_4005_DHDH_A_20261006T233918_20261006T233952_P05023_N_F_J_001.h5).
- `NISAR_L2_PR_GCOV_033_098_A_016_4005_DHDH_A_20261018T233918_20261018T233952_P05023_N_F_J_001` — [NASA/ASF HDF5 URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_033_098_A_016_4005_DHDH_A_20261018T233918_20261018T233952_P05023_N_F_J_001/NISAR_L2_PR_GCOV_033_098_A_016_4005_DHDH_A_20261018T233918_20261018T233952_P05023_N_F_J_001.h5).

[Full query, results and compatibility reasons](../data/candidates/phase1_2026_11_02_final/nepal_098_016.json).

## Transfer and preservation plan

Both batches together are **51.4844 GiB** of compressed HDF5 input, before extracted products and working space. These are exact catalog byte counts, not measured transfer volumes. Candidate file checksums have not been computed because no radar files were downloaded; saved metadata responses have SHA-256 checksums.

Prefer an authenticated native-window read for the crop(s), including masks and required metadata. ASF documents [GDAL/remote subset access](https://nisar-docs.asf.alaska.edu/access-overview/) and [Harmony dataset extraction](https://nisar-docs.asf.alaska.edu/harmony/). The current Harmony guide confirms variable extraction, not a guaranteed crop-sized output. Neither transfer size nor compatibility of a subset has been tested here; do not assume a cheap subset or submit a transfer job without approval.

After approval: save source inputs separately, run the existing HDF5 compatibility audit, and produce a **new versioned** canonical-COG series and manifest. Preserve the original baselines, products and tracked-zone findings. Existing `make investigations` / `make jamuna` targets replace frozen destinations and must not be used for this extension in place.

No credentials should be pasted into chat. Earthdata authentication can remain in the local authorized client.

## Availability evidence

- [Official ASF gap notice](https://nisar-docs.asf.alaska.edu/availability-overview/): 2026-07-27T22:03:25Z to 2026-08-10T00:55:27Z.

- Archive source: four bounded ASF Python searches, one per crop, with completed pagination. Queries and response hashes are retained. Alternate X05026 releases and UR configurations are recorded as incompatible. The last Nepal slot is “unavailable in the compatible archive search,” not proof that NISAR made no acquisition.

- Nepal catalog footprints partially overlap the original Kathmandu crop on several dates (July 26 ~99.96%, September 24 ~98.04%, October 6 ~99.50%). Those geographic overlap estimates do not measure valid radar pixels. The corridor crop is covered by all four candidate footprints.

## User decision

Approve the Bangladesh batch (25.0547 GiB), both batches (51.4844 GiB), a named subset of dates, or defer downloads and proceed to Phase 2 with the nine existing source granules. This approval gate comes directly from rule 15 and Phase 1 task 5 of the user’s master prompt.
