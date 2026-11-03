# Interferometry Gate A — historical catalog checkpoint

**Superseded for the two supplied Nepal pairs:** [Implementation 17](IMPLEMENTATION_17_SUPPLIED_DATA.md) records accepted source headers and native coherence crops in `expanded-v1`. The report below preserves the earlier access barrier. Bangladesh remains unavailable; LOS displacement remains unresolved.

Reviewed 3 November 2026, Asia/Dhaka. **Gate not open: planned, pending authenticated source-header and subset verification.** This is not a finding that GUNW/GSLC products do not exist.

## Evidence and decision

NASA/ASF catalogs contain the following candidates matching the loaded acquisition endpoints, track/frame, ascending direction, provisional collection, PR production configuration and P05023 release at the metadata-screen level:

| Series | Product | Catalog rows | Eligible on loaded dates | Catalog complete |
| --- | --- | ---: | ---: | --- |
| Nepal 98/16 | GUNW | 15 | 2 pairs | Yes |
| Nepal 98/16 | GSLC | 15 | 3 scenes | Yes |
| Bangladesh 69/14 | GUNW | 8 | 2 pairs | **No** |
| Bangladesh 69/14 | GSLC | 10 | 6 scenes | Yes |

The Nepal GUNW pairs are August 19→31 and August 31→September 12, with full files about 2.184 and 2.172 GiB. Bangladesh's observed candidate pairs are July 24→August 17 and August 17→29, about 2.176 and 2.156 GiB. These are catalog sizes, not proposed downloads. GSLC full files are about 20.4–21.3 GiB each. No full interferometric file was downloaded. The incomplete Bangladesh query cannot establish absence of other pairs; do not treat its results as exhaustive.

The initial staged screening incorrectly treated a derived GUNW `4000_SH` label as if it had to equal the GCOV `4005_DHDH_A` acquisition configuration. The reviewed screen corrects this: GUNW uses frequency-A co-polarized HH output here. Original source identifiers, imaging mode, bandwidth and release still require inspection in the product header before physical comparability is accepted. Metadata eligibility is not scientific acceptance. Unloaded dates and mismatched releases/production configurations are excluded.

A bounded unauthenticated NASA science-file request on 3 November returned **HTTP 401**, with zero response-body bytes read. No local Earthdata authentication configuration was found during the initial probe. The earlier sandbox request returned a network error and was retained separately; it was not misreported as an authentication response. The successful external-network check establishes the current access barrier, not absence or scientific quality of the product.

No header-compatible crop subset, coherence raster or unwrapping-quality layer has been accepted. Coherence and LOS displacement remain **null**. No phase-to-distance conversion, synthetic coherence or motion simulation is supplied.

## Feasible route to reopen the gate

NASA documents actual subsetting options: [Harmony dataset extraction](https://nisar-docs.asf.alaska.edu/harmony/) exports selected GUNW datasets as GeoTIFF; [Vertex GDAL snippets](https://nisar-docs.asf.alaska.edu/vertex/) support remote geographic subsetting without downloading the entire HDF5 file. These services exist; an authenticated, bounded request for these candidates has **not** been demonstrated here. A full extracted layer is not automatically a crop-sized download.

1. Configure NASA Earthdata Login locally and accept ASF's data-access agreement, or supply the downloaded GUNW files. Never paste passwords/tokens into chat or commit them.
2. Inspect candidate source acquisition identifiers, release, mode, bandwidth, dates, direction, track/frame and processing metadata. Keep the Nepal and Bangladesh series separate.
3. Request only the crop and necessary frequency-A HH coherence/quality datasets, estimate resulting size, and use small subsets. Obtain explicit approval before any large full-file download.
4. Check geolocation, native resolution, valid masks and coherence values against actual source pixels. A coherence map is pair-based evidence, not an invented per-visit intensity measurement or automatic damage label.
5. LOS displacement additionally requires a documented reference point, connected-component/unwrapping masks, wavelength/sign convention and atmospheric/ionospheric correction caveats. It is not vertical or slope displacement without geometry.

## Inspectable records and provenance

`data/candidates/interferometry_phase6_v1/` retains the four original NASA/ASF responses and the preliminary screen. `data/candidates/interferometry_phase6_v2/gate-reviewed.json` and public `web/public/cases/interferometry-v2.json` are the reviewed decision, preserving source queries, response SHA-256, retrieval UTC, all rejections, candidate IDs/URLs/sizes, incomplete-search flags and the bounded access probe. Upstream is NASA–ISRO, USA/India; no Chinese data provider/site is involved. License context is NASA Earth-science open-data policy, subject to ASF access terms and eventual accepted-product DOI citation. No scientific dataset was acquired under this gate.

Primary references: [ASF GUNW product guide](https://nisar-docs.asf.alaska.edu/gunw/), [NASA/ASF access requirements](https://nisar-docs.asf.alaska.edu/access-overview/), [ASF Earthdata setup and agreement](https://github.com/ASFOpenSARlab/NISAR_Cookbook/blob/main/notebooks/set_up_Earthdata_Login.md). GUNW includes coherence, unwrapped phase and quality/correction layers; phase corrections must not be assumed already applied.

Gate A reporting is complete with a pending-access/subset outcome. The conditional coherence/displacement branch remains unimplemented until these conditions are met, as the master plan requires.
