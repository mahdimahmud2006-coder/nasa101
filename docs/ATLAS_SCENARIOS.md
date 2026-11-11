# Atlas terrain scenarios

Open the Atlas, select a study window, and expand **What if?** in the Evidence Inspector. The plan map shows the scenario over the radar image. **View terrain** samples the same screen on the existing 3D NASADEM mesh; all area totals use the 30 m analysis grid. The controls and results are independent of the saved evidence footprint. Closing the panel removes the overlay.

## Bangladesh: river surge and embankment

Set a relative stage from +0.0 to +10.0 m. A cell qualifies if its height above its downstream drainage cell (HAND) is at most the selected stage and its terrain slope is at most 8°. A priority-flood/D8 flow graph is calculated from locally stored NASADEM tiles, using a 1.8 km buffer and a 1 km² drainage initiation area. Heights use the original elevation rather than the filled routing surface. Open outlets, unresolved paths, negative heights and invalid terrain are excluded. The result is sensitive to the drainage threshold, DEM and buffer. The stage is relative to each cell's assigned drainage, with no gauge datum or discharge calibration. The assessed area includes valid cells that fail the slope or stage test.

Open **Test an embankment opening** and try the sample barrier, or set two barrier ends and a mapped drainage seed. Keyboard entry accepts three column,row pairs, in order, on the 30 m grid. The closed scenario blocks the full line. The open scenario unblocks its middle cell and compares four-neighbor reachability through eligible terrain. Water can go around a short barrier; the difference can therefore be zero. This exercise tests connectivity, without an embankment inventory, water depth, flow velocity, timing or actual breach prediction. The sample barriers are hypothetical.

Choose **Observed HH within screen** to see the current NISAR visit on the same terrain cells. The two user-specified cutoffs (−19.5 and −11.5 dB) divide the observed HH into display bins. The middle bin includes both endpoints. The browser requests one visit's class plane at a time. Samples are taken at terrain cell centers from the admitted radar grid. A low or high return is not a measurement of crop type or inundation. The existing radar data provide no calibrated next-pass DpRVIc or Boro rice prediction.

## Nepal: slope stability and shaking

The infinite-slope sensitivity calculation uses the supplied simplified horizontal pseudo-static term:

```text
FoS = [c′ + (γ − mγw) z cos²(θ) tan(φ′)] / [γ z sin(θ) cos(θ) + kh γ z]
```

The sliders set the saturated-depth fraction `m` (0–1) and the assumed acceleration coefficient `kh` (0–0.4, in units of g). The remaining assumptions start at cohesion 5 kPa, friction angle 32°, soil depth 2 m, and soil unit weight 18 kN/m³. Water unit weight is 9.81 kN/m³. Soil assumptions are uniform and editable. A cell lights up if its modeled factor of safety is strictly below 1.0. With level terrain and no shaking, driving stress is zero and the cell does not meet that criterion. A DEM slope is not a field survey, and the simple model does not calculate infiltration, erosion, shaking direction, failure volume or runout.

The GUNW comparison shows the sign of later-minus-earlier HH coherence for eligible, equal-duration adjacent pairs. Both pairs must be valid; nearest-center sampling aligns this descriptive sign with the 30 m grid. The Rasuwa–Nuwakot local view also shows the overlap with UNOSAT's preliminary mapped August 26 impact extent. The map is rasterized at terrain cell centers and the result is a descriptive area intersection. Neither source changes cohesion or verifies that a modeled slope failed. No physical relationship between DpRVIc, coherence and soil strength has been calibrated for these windows.

## Build and sources

With the processed case rasters and the local NASADEM source windows in place, run `make atlas-simulations`, then `make demo`. Run `make atlas-static` to build the versioned static preview; the optional scenario inputs are checked against the case identities and loaded only when opened. The single-file offline edition retains the saved investigations. It does not carry the scenario grids. The UNOSAT comparison is local only.

- [NASA JPL NASADEM HGT v001](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001)
- [NOAA repository: HAND research and its dependence on drainage sources](https://repository.library.noaa.gov/view/noaa/52493)
- [USGS TRIGRS documentation](https://pubs.usgs.gov/of/2008/1159/downloads/pdf/OF08-1159.pdf), for background on infinite-slope modeling and the distinction between this simplified screen and an infiltration model
- [ASF NISAR GUNW guide](https://nisar-docs.asf.alaska.edu/gunw/)
- [UNOSAT preliminary Rasuwa–Nuwakot mapping, via UNESCO IHP-WINS](https://ihp-wins.unesco.org/en/dataset/nepal-satellite-detected-mudflow-and-rockflow-extent-nepal)

## Be the NISAR Sensor

Open the lab on any case, choose a saved footprint or measure a polygon in the full local edition, then play or step the recorded timeline. The observation card uses paired-valid HH and HV footprint means in dB and the observed mean of the per-cell linear HV power share. The simulated card is a uniform teaching state. Both use the same RGB scaling: HH −32 to −3 dB, HV −38 to −10 dB, and cross-polarized power share 0 to 0.5, with clipping. It is a comparison swatch, not a full-polarimetric decomposition or a measured RGB image.

The surface term uses a Fresnel-inspired HH reflectivity at a fixed 38° incidence, with a simple soil dielectric mixture and attenuation by the canopy. An assumed shallow-to-deep water transition shifts the surface toward low-return smooth water. A water–stem term strengthens HH for intermediate canopy proxy values and standing water; volume scattering adds HH and HV as the proxy increases. Powers add before the logarithmic conversion. The transfer factors are illustrative. Soil roughness, wind, plant geometry and field-measured coefficients are not represented. A similar swatch is useful for exploring competing hypotheses but cannot identify a unique surface state, DpRVIc, or calibrated biomass. See the [NASA SAR Handbook](https://ntrs.nasa.gov/api/citations/20190002563/downloads/20190002563.pdf).

## Jamuna: monsoon bank retreat

Try the sample or draw a line approximately perpendicular to the radar-dark edge, starting in the main channel and ending inland. The scenario samples the admitted ten visits at 30 m centers, using a three-sample cross-track majority and the HH ≤ −17 dB display rule. Both ends must have consistent dark/bright runs, with a single sustained crossing. Missing or ambiguous crossings stay unresolved. The visit list and recurrence strip show the evidence behind the simulated distance.

The retreat distance uses the difference between the farthest and nearest resolved crossing, multiplied by mean observed radar-dark recurrence across that spread, the selected discharge multiplier and the number of cycles. It requires six resolved visits, including the selected starting visit. This uses a single season as a *distance scale*, without interpreting it as a rate or calibrating discharge. The drawn strip is 90 m wide and stops at the inland endpoint. It checks historical ESA WorldCover 2021 cropland and any user-marked asset point. A flagged cell or point is an intersection with the scenario, not a forecast of inundation or land loss. Comparative water stages, independent banklines and registration bounds would be required to establish measured movement. See the [USGS transect methods](https://pubs.usgs.gov/of/2021/1091/ofr20211091.pdf).

## Nepal: Sensor & Orbit Simulator

Open the lab in Kathmandu or Rasuwa–Nuwakot. The ascending preset uses the local geometry sampled from the admitted August 19 GCOV for Track 098; the preset receipt is in [nepal_atlas_look.json](../data/context/nepal_atlas_look.json). The alternative reverses the target-to-sensor azimuth by 180°. It is a hypothetical descending look, not a second measured orbit. Incidence is measured from vertical. The 30 m NASADEM grid is buffered by 1.8 km before a parallel-ray horizon sweep. Along each approximate range ray, a nearer terrain sample blocks a farther one when its height is above the far sample's line to the sensor. Where no obstruction is found, a steep toward-sensor range slope flags local layover. Unknown support is excluded from the reported percentages. The ray model assumes constant incidence and cannot see obstructions beyond the source DEM. The 3D mesh samples the mask for display.

The wavelength control uses the same assumed Gaussian line-of-sight scatterer motion for both bands: the phase-only coherence is `exp(-0.5 (4π σ / λ)²)`. NISAR L-band uses 24 cm and the C-band example uses 5.6 cm. This illustrates sensitivity to motion, with no prediction of local C-band observations or canopy decorrelation. The selected footprint's measured NISAR GUNW coherence is shown separately on visits ending in a measured pair. See [NASA's NISAR mission specifications](https://science.nasa.gov/mission/nisar/), [JPL SAR geometry fundamentals](https://descanso.jpl.nasa.gov/SciTechBook/series2/SAR_Polarimetry_compressed.pdf), and [NASA ARSET's wavelength comparison](https://appliedsciences.nasa.gov/sites/default/files/2023-10/SAR_2023_Part2_Final.pdf).
