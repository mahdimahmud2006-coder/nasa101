# TerraPulse — Reviewer Overview

Updated: 28 October 2026

## What the project actually does

TerraPulse is an interactive tool for investigating changes in satellite radar measurements over time. It helps a reviewer locate unusual surface-change candidates, measure their extent, and inspect supporting environmental evidence. The current demonstration covers a fixed 24 km × 24 km area around Kathmandu, Nepal, using three NASA–ISRO NISAR observations from 19 August, 31 August, and 12 September 2026.

The application reads real NISAR radar files, checks that observations are comparable, excludes invalid pixels, reduces speckle, and calculates differences in radar return strength. A statistical threshold identifies unusually large differences, which are grouped into regions with measured areas and change statistics. Saved outputs feed a local web application; ordinary Python calculations produce the scientific results.

## What a reviewer can do

- **Compare observations:** Inspect before/after radar images, change overlays, region boundaries, dates, and measured areas in Radar Comparison and Evidence Studio.
- **Follow changes over time:** Use Timeline and Change Lab to examine whether a region remains different from the first observation. Change DNA describes onset intervals, magnitude, and persistence; a smaller later change mask does not automatically mean recovery.
- **Inspect environmental context:** Explore terrain, slope, drainage-related layers, rainfall, and available Landsat optical and thermal imagery, including a 3D terrain view.
- **Explore hazard scenarios:** Adjust rainfall and assumed soil saturation to see how an illustrative flood index responds, and inspect landslide susceptibility layers.
- **Trace the evidence:** Review data sources, processing methods, threshold sensitivity, and exported raster/vector evidence. Runtime assets are stored locally.

## Main shortcomings

- **The cause of detected change is unverified.** Radar changes can reflect moisture, vegetation, roughness, terrain effects, or artifacts. The current outputs do not confirm a flood or landslide, and they do not measure ground displacement.
- **The time series and geographic scope are small.** Three observations support a retrospective case study, with limited evidence about onset or recovery. Live monitoring and arbitrary worldwide processing are unavailable.
- **Hazard models lack independent calibration.** Flood and landslide scores use illustrative weights. They are not disaster probabilities, flood-depth estimates, or operational forecasts. Available independent impact mapping does not overlap the current study crop.
- **Input resolution and processing affect results.** NISAR data are provisional; filtering and thresholds influence detected regions. Regional rainfall and partially cloud-screened Landsat coverage limit local interpretation.
- **Demonstration checks remain incomplete.** Automated checks exist, but current real-browser visual verification and a physically disconnected rehearsal remain pending. The release archive also needs rebuilding after recent corrections.

TerraPulse currently demonstrates a traceable workflow from satellite measurements to inspectable change evidence. Its strongest contribution is helping people investigate observed changes; establishing their physical cause and validating hazard predictions require further independent evidence.
