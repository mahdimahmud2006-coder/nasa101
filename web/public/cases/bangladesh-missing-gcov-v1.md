# Four shared Bangladesh GCOV downloads

**River Memory and Wetland Pulse currently have six observed visits each.** Four additional compatible GCOV files are not in the local database. They fill June 30, July 12, September 10 and October 4 in both views. Download each once, retaining original filenames.

**August 5 is different:** its nominal visit falls inside the permanent NISAR outage, July 27 22:03:25 UTC → August 10 00:55:27 UTC. There is no August 5 NISAR acquisition to download. [NASA / ASF availability notice](https://nisar-docs.asf.alaska.edu/availability-overview/).

| Actual visit (UTC, 2026) | Size (GiB) | NASA / ASF original HDF5 |
| --- | ---: | --- |
| 2026-06-30 | 6.195 | [Download GCOV](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_024_069_A_014_4005_DHDH_A_20260630T232134_20260630T232209_P05023_N_F_J_001/NISAR_L2_PR_GCOV_024_069_A_014_4005_DHDH_A_20260630T232134_20260630T232209_P05023_N_F_J_001.h5) |
| 2026-07-12 | 6.227 | [Download GCOV](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_025_069_A_014_4005_DHDH_A_20260712T232134_20260712T232208_P05023_N_F_J_001/NISAR_L2_PR_GCOV_025_069_A_014_4005_DHDH_A_20260712T232134_20260712T232208_P05023_N_F_J_001.h5) |
| 2026-09-10 | 6.402 | [Download GCOV](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_030_069_A_014_4005_DHDH_A_20260910T232131_20260910T232206_P05023_N_F_J_001/NISAR_L2_PR_GCOV_030_069_A_014_4005_DHDH_A_20260910T232131_20260910T232206_P05023_N_F_J_001.h5) |
| 2026-10-04 | 6.230 | [Download GCOV](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_032_069_A_014_4005_DHDH_A_20261004T232132_20261004T232206_P05023_N_F_J_001/NISAR_L2_PR_GCOV_032_069_A_014_4005_DHDH_A_20261004T232132_20261004T232206_P05023_N_F_J_001.h5) |

Total: **25.055 GiB**. These are **GCOV intensity** products, not GUNW coherence. The supplied extra files are for Nepal track 98 / frame 16; Bangladesh needs ascending track 69 / frame 14, PR/P05023, HH/HV frequency A from the 40+5 MHz acquisition mode.

Save in `/home/mahdi-mahmud/Downloads/DATASET NASA/NEPALv1/database/bangladesh-shared/`. NASA Earthdata login and the ASF data-access agreement may be required. All file links use NASA’s ASF Earthdata Cloud host (USA); the mission is NASA–ISRO (USA/India). No Chinese provider/site is used.

After the files are supplied, header compatibility, source masks and native crop coverage must be audited before a new versioned import. Catalog compatibility is not accepted pixel-level science. Existing output files remain preserved. The August 5 outage stays explicit after all four downloads are imported.

Both crop searches completed in the fresh metadata snapshot `data/candidates/bangladesh_gcov_gaps_2026_11_03/`. It finds 10 catalog-compatible dates: six loaded, four not in hand, and one additional nominal outage slot with no acquisition. Exact source URLs, sizes, IDs, retrieval times and response hashes are retained in that snapshot. No science data was downloaded by this check.
