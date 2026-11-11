# TerraPulse preview asset review

The public candidate consists of TerraPulse's atlas interface, display derivatives, rounded terrain mesh samples and selected measurements from the four admitted records. The HH and HV derivatives are up to 1,100 pixels on the long edge. The release inventory maps each preview to its case, source record field and SHA-256. STAC records point to display derivatives. The code is Apache-2.0. Dataset terms and third-party notices apply independently.

| Included material | Source and basis |
| --- | --- |
| Intensity, power share, native pair coherence and signed comparison previews and measurements | NASA–ISRO NISAR provisional GCOV and GUNW, from ASF DAAC. ASF identifies the science data as open to the public. The dossier names each granule and distinguishes provisional evidence from validation. [ASF user guide](https://nisar-docs.asf.alaska.edu/) |
| Dated HLS comparisons | NASA HLS L30/S30 derived previews and descriptive overlap. Scene identifiers stay attached. [NASA HLS open data](https://science.nasa.gov/mission/landsat/open-data/) |
| Historical land-cover summaries | ESA WorldCover 2021 v200, © ESA WorldCover project 2021, CC BY 4.0. TerraPulse resamples source classes onto the radar grid and counts their overlap with paired-valid footprints. [Source DOI](https://doi.org/10.5281/zenodo.7254221) |
| Kathmandu thermal previews | USGS Landsat Collection 2 surface temperature. NASA/USGS source credit and actual scene dates stay attached. [USGS distribution policy](https://www.usgs.gov/media/files/landsat-data-distribution-policy) |
| Terrain previews and sampled elevations | NASA JPL NASADEM HGT v001, NASA EOSDIS LP DAAC. No Copernicus DEM tiles are included. [Dataset citation](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001) |
| Interactive scenario inputs | NASADEM terrain derivatives and selected NISAR intensity and coherence classes, aligned to a 30 m analysis grid. Includes terrain screening inputs and observed context, rather than source GeoTIFFs. The local UNOSAT impact rasterization is excluded from the preview bundle. |
| Radar labs | Derived NASADEM elevation samples for terrain rays, an admitted NISAR GCOV look-vector sample, packed radar-dark visit labels, and a 30 m sample of ESA WorldCover 2021 v200 cropland classes (CC BY 4.0). Simulated C-band coherence and retreat are calculated scenarios. |
| Kathmandu weather context and model previews | NASA Langley POWER model and reanalysis context. Model output is a TerraPulse sensitivity calculation. [POWER referencing guide](https://power.larc.nasa.gov/docs/referencing/) |
| Color scales | Cividis from Matplotlib and Vik from Fabio Crameri's Scientific Colour Maps. Both notices accompany the candidate. [Scientific Colour Maps](https://doi.org/10.5281/zenodo.1243862) |

The inclusion review covers project-generated, display-resolution products and their evidence metadata. The staged folder excludes raw HDF5, COGs, GeoParquet, credentials, source repository, organization logos, third-party map files, participant records and private filesystem paths. The Rasuwa–Nuwakot footprint label records a preliminary mapping context. No underlying third-party boundary file is included. The versioned local review can proceed with these assets. Public deployment still requires the account owner's authorization for the exact staged folder.
