# 🛰️ TerraPulse

**Transparent Radar Surface-Change Investigation & Environmental Context**  
*NASA Space Apps Challenge 2026 · Challenge: Dancing with the SARs · Team: DevAtMad*

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Submission%20Candidate%20(v1.0.0)-success.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-189%20Python%20%7C%2037%20JS%20Passed-brightgreen.svg)](#verification-and-testing)
[![Data](https://img.shields.io/badge/Data-NASA--ISRO%20NISAR%20L2%20GCOV%20(Provisional)-orange.svg)](docs/DATASETS.md)
[![Offline](https://img.shields.io/badge/Runtime-Local%20Assets-darkgreen.svg)](#key-features--architecture)

---

## 🌍 Overview

**TerraPulse** transforms complex, cloud-penetrating synthetic aperture radar (SAR) measurements from the NASA–ISRO NISAR satellite into an interactive, mathematically rigorous, and fully transparent surface-change investigation platform.

Rather than presenting an ungrounded black-box classification or false disaster confidence, TerraPulse connects **radar backscatter physics**, **antecedent environmental context**, **temporal behavioral fingerprinting (Change DNA)**, and **explainable hazard models**—using local runtime assets and cryptographic data provenance. A physically disconnected browser rehearsal remains pending.

![Earlier TerraPulse Radar Comparison interface](docs/demo.png)
*Figure 1: Earlier Radar Comparison interface for the Kathmandu case; this image does not show the current Evidence Studio. Current browser visual verification remains pending.*

> [!IMPORTANT]
> **Scientific Integrity & Disclaimers:**
> - **NISAR Data Status:** Earth observation inputs are **PROVISIONAL** (collection `NISAR_L2_GCOV_PROVISIONAL_V1`).
> - **Physical Causation:** All identified backscatter change causes remain **UNVERIFIED** (backscatter changes can reflect moisture, roughness, or vegetation/structure changes; these GCOV intensity measurements do not establish ground displacement).
> - **Model Calibration:** Susceptibility and counterfactual scenario indices remain **UNCALIBRATED** demonstration models. Local completeness does not constitute an operational early-warning forecast or emergency response system.

## Three investigation workspaces

Open **[TerraPulse investigations](http://127.0.0.1:8000/investigations.html)** after starting the server.

| Workspace | Current state |
|---|---|
| **Surface investigations** | Two measured Nepal cases: original Kathmandu footprint and an additional reference-aligned Rasuwa–Nuwakot crop. HH/HV maps, baseline/successive differences, first/selected swipe, discrete-date playback, fixed-neighborhood probes, paired traces and evidence dossiers. |
| **River Memory** | Six actual Jamuna observations processed, with HH/HV playback, dark-signature gains/losses and observed-visit fractions. These exploratory signatures are not validated bank erosion. |
| **Wetland Pulse** | The same six files also power Tanguar Haor: observed dark-signature fractions, paired brightening and HH/HV traces. These are not calibrated habitat or inundation classes. |

The six priority NASA/ASF files were imported on **31 October 2026** and pass coverage checks for both Bangladesh windows. No separate haor download is needed for these dates. Open [River Memory](http://127.0.0.1:8000/investigations.html?mode=river) or [Wetland Pulse](http://127.0.0.1:8000/investigations.html?mode=wetland). See [Bangladesh import results](docs/IMPLEMENTATION_09_BANGLADESH.md), [exact download instructions and import commands](docs/DOWNLOAD_AND_IMPORT.md), [granule names](docs/downloads/bangladesh-priority-granules.txt), and [implementation details](docs/IMPLEMENTATION_08_INVESTIGATIONS.md).

```bash
# Rebuild Jamuna without changing the other cases
make jamuna
make validate-investigations
```

The new corridor intersects about **6.42 km²** of preliminary independent mudflow/rockflow mapping. This is spatial context, not proven detection accuracy. Earlier sections and reports about zero overlap apply to the original Kathmandu crop.

---

## ⚡ Quick Start

### 🚀 1. Run with Existing Environment

The local workspace already includes pre-built analytical assets and the verified Python virtual environment:

```bash
# Launch the application (binds to http://127.0.0.1:8000/)
make run
```

Or run directly via the startup script:

```bash
./run.sh --port 8000
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in any modern web browser. Use `Ctrl+C` in your terminal to shut down the server.

### 💻 2. Setup on a Fresh Machine

```bash
# Clone the repository
git clone https://github.com/mahdimahmud2006-coder/nasa_space-apps_challenge.git
cd nasa_space-apps_challenge

# Create and activate virtual environment (Python 3.12+; 3.14 tested)
python3 -m venv .venv
source .venv/bin/activate

# Install verified dependencies
pip install -r requirements.txt

# Verify preflight and start server
make check-ready
./run.sh
```

> [!TIP]
> **Zero Network Dependency at Runtime:**  
> Once dependencies are installed, TerraPulse requires **no internet access**, no API keys, no Earthdata credentials, and no external CDNs or map-tile servers. All scripts, fonts, WebGL shaders, raster layers, and GeoJSON boundaries load directly from localhost.

---

## 🔬 Key Features & Architecture

```mermaid
graph TD
    A[Raw NISAR L2 GCOV HDF5<br/>10m Gamma-0 HH Backscatter] --> B[Deterministic Science Pipeline<br/>MAD Thresholding & Filtering]
    C[NASADEM 30m Topography<br/>Slope, TWI, Drainage, Relief] --> D[Environmental Context Engine]
    E[NASA POWER Hourly Rain<br/>Precipitation Windows] --> D
    F[USGS Landsat 8/9<br/>Thermal TIRS & Optical QA] --> D
    
    B --> G[Multi-Temporal Change DNA<br/>Onset, Magnitude & Persistence]
    B --> H[Evidence Studio<br/>Acquisition Playback & Scenario Comparison]
    D --> I[Explainable Flood Model<br/>Counterfactual Scenarios]
    D --> J[Landslide Susceptibility<br/>NASA GLC Historical Reference]
    
    G --> K[Interactive Local Web Workspace<br/>Vanilla JS / Modern CSS / WebGL]
    H --> K
    I --> K
    J --> K
```

### 🎛️ 1. Interactive Application Interfaces

| View | Route | Description & Key Capabilities |
|---|---|---|
| **Evidence Studio** | [`/`](web/index.html) | Radar-led primary workspace with discrete acquisition playback, radar/terrain/optical/thermal context, geographic evidence checks, and a baseline/counterfactual slider for applied scenarios. |
| **Change Lab** | [`/change-lab.html`](web/change-lab.html) | Deep-dive forensic analytics. Features Change DNA behavioral profiles, onset brackets, backscatter-change magnitude, contraction vs. persistence analysis, and censored recovery tracking. |
| **Timeline View** | [`/timeseries.html`](web/timeseries.html) | Longitudinal time-series playback of radar observations without artificial date interpolation. Compares transition intervals against baseline references. |
| **Radar Comparison** | [`/comparison.html`](web/comparison.html) | Radar before/after swipe and scan reveal, histogram inspection, threshold sensitivity adjustment (±10%), and raw vs. robust mask overlays. |

### 🧬 2. Change DNA: Temporal Behavioral Profiling
In real-world SAR investigations, an anomaly mask may shrink even while the underlying baseline disturbance remains. TerraPulse distinguishes between:
- **Baseline Disturbance Persistence:** Retained backscatter difference from the first observed baseline; the baseline is not independently established as pre-event.
- **Transition Mask Contraction:** Immediate temporal delta between consecutive revisit passes.
- **Onset & Recovery Bracketing:** Explicit right-censoring rather than interpolated daily recovery curves.

### 🏔️ 3. Environmental & Topographic Context
- **NASADEM Topographic Derivatives:** 30 m native elevation, slope, aspect, curvature, roughness, relative elevation, D8 flow accumulation, Topographic Wetness Index (TWI), and modeled Euclidean drainage proximity.
- **3D Terrain Canvas with 2D Fallback:** GPU-accelerated WebGL terrain rendering with keyboard navigation (`Arrow keys` to pan, `+`/`-` to zoom, `Enter` to probe coordinate, `Esc` to reset) and standard 2D canvas fallback.
- **NASA POWER Precipitation:** Hourly liquid-equivalent rainfall integrated across 24 h, 72 h, and 168 h windows preceding each radar pass.
- **USGS Landsat 8/9 Context:** Independent Tier-1 thermal surface temperature (TIRS Band 10) and optical RGB reflectance screened for cloud obscuration.

### 🌊 4. Transparent Hazard & Scenario Engines
- **Explainable Flood Escalation:** Additive component weighting combining terrain wetness, drainage proximity, low slope, antecedent precipitation, and NISAR backscatter decrease.
- **Counterfactual Scenario Studio:** Fast offline simulation engine exploring alternative rainfall multipliers (0.5×–3.0×) and soil saturation states using a compact 17 MB component cube.
- **Landslide Susceptibility Index:** Coupled static topography, dynamic rainfall triggers, and radar modifiers. Historical NASA/GSFC Global Landslide Catalog coverage was audited; independent calibration remains unavailable.

![Multi-Layer Scientific Map Comparison](docs/reports/implementation_06_07_maps.png)
*Figure 2: Model-output comparison of flood attention, static landslide susceptibility, and combined landslide susceptibility. These maps are not independent event validation.*

---

## 📊 Study Case Specifications

The Kathmandu surface-change case uses three 2026 observations. Its detected change has no independently established event cause; the separate preliminary UNITAR/UNOSAT mudflow/rockflow mapping does not overlap this crop.

| Dimension | Specification | Source Provenance |
|---|---|---|
| **Geographic AOI** | 24 km × 24 km (2,400 × 2,400 pixels at 10 m native resolution) | Centered at 85.33° E, 27.80° N; UTM Zone 45N (EPSG:32645) |
| **Radar Acquisitions** | 2026-08-19, 2026-08-31, 2026-09-12 (12-day & 24-day intervals) | NASA–ISRO NISAR L2 GCOV (Track 98, Frame 16, 40 MHz, HH) |
| **Terrain Elevation** | 30 m grid; 530.63 m to 2,723.65 m elevation range | NASADEM HGT tiles (`n27e085`, `n28e085`) via Microsoft Planetary Computer |
| **Precipitation** | Hourly liquid-equivalent precipitation; native 0.5° × 0.625° regional grid | NASA POWER PRECTOTCORR (MERRA-2 / GEOS-IT) |
| **Thermal / Optical** | 30 m delivery grid; 4 cloud-screened scenes | USGS Landsat 8/9 Collection 2 Level-2 Surface Temperature/Reflectance |
| **Historical Reference Audit** | 10 nominal study-AOI reports; 2 meet ≤1 km precision screen | NASA/GSFC Global Landslide Catalog (GLC) subset |

The three processed radar granules are:

```text
NISAR_L2_PR_GCOV_028_098_A_016_4005_DHDH_A_20260819T233918_20260819T233953_P05023_N_F_J_001
NISAR_L2_PR_GCOV_029_098_A_016_4005_DHDH_A_20260831T233918_20260831T233952_P05023_N_F_J_001
NISAR_L2_PR_GCOV_030_098_A_016_4005_DHDH_A_20260912T233918_20260912T233952_P05023_N_F_J_001
```

Collection: `NISAR_L2_GCOV_PROVISIONAL_V1`; the original analysis uses frequency-A `HHHH`. The new investigation workspace also processes actual `HVHV`; additional catalog dates remain candidates until downloaded and accepted by the importer. See [dataset details](docs/DATASETS.md).

---

## 🛠️ Verification and Testing

TerraPulse checks numerical consistency, software behavior, and export agreement. These checks do not establish event attribution or predictive accuracy. All 189 Python tests and 37 JavaScript tests pass in the 2026-10-31 Bangladesh import. JavaScript controller checks use explicit DOM/canvas/terrain mocks, not a real browser. The six analytical validation targets check saved measurements and consistency, not event attribution.

```bash
# 1. Run fast local runtime preflight (verifies dependencies and assets)
make check-ready

# 2. Run Python automated unit and numerical test suite (189 tests)
make test

# 3. Run JavaScript interaction, math, and UI controller test suite (37 tests)
make test-ui

# 4. Run static HTML/CSS/DOM asset integrity verification
make check-web

# 5. Run full verification suite (all tests + 6 analytical validators)
make verify
```

### Test Coverage Highlights

- **189 Python Tests:** Verifies pixel area determinants, signed delta dB math, median filter speckle reduction, MAD threshold calculations, geometry alignment, Parquet schema, and API route responses.
- **37 JavaScript Tests:** Verifies swipe slider math, 3D/2D coordinate transformations, timeline state transitions, keyboard controls, and DOM event listeners.
- **6 Analytical Validators:**
  - `validate` (Primary NISAR radar delta and vector geometry)
  - `validate-timeseries` (Cloud-Optimized GeoTIFFs, transition frequencies, and Parquet continuity)
  - `validate-context` (Terrain derivatives, drainage routing, and rainfall consistency)
  - `validate-flood` (Monotonicity under rainfall scaling, scenario cache integrity)
  - `validate-change-lab` (508 byte-for-byte prior historical artifacts preserved)
  - `validate-investigations` (new HH/HV case rasters, profiles, coverage and pending-data states)

---

## 📦 Portable Release Packaging

TerraPulse can be compiled into a standalone, reproducible zip package containing all application code, public COG rasters, and runtime scenario cubes (excluding multi-gigabyte raw HDF5 files):

```bash
# Build standalone release package
make release
```

This generates (the existing archive predates the 2026-10-28 audit corrections; rebuild before distributing updated source):
- `dist/terrapulse-1.0.0.zip` (local runtime assets; install Python dependencies first)
- `dist/terrapulse-1.0.0.zip.sha256` (cryptographic verification hash)

To verify an extracted release bundle, then install dependencies as in the fresh-machine instructions above before starting it:
```bash
python3 scripts/verify_release.py
bash run.sh
```

---

## 📂 Project Structure

```text
NEPALv1/
├── Makefile                          # Build, verification, and execution targets
├── run.sh                            # Preflight check and local server launcher
├── config.*.json                     # Modular configurations (project, flood, context, etc.)
├── requirements.txt                  # Pinned Python dependencies
├── pyproject.toml                    # Package metadata & build definition
│
├── src/                              # Core Python Science & API Modules
│   ├── api/                          # Local standard-library HTTP server & preflight
│   ├── compute/                      # Deterministic radar math, terrain, flood & landslide pipelines
│   ├── ingest/                       # HDF5 inspection, STAC metadata, and reference readers
│   └── export/                       # GeoTIFF COGs, GeoJSON, and evidence JSON serializers
│
├── web/                              # Offline User Interface
│   ├── index.html                    # Evidence Studio interface
│   ├── change-lab.html               # Change Lab (DNA & Landslide forensic view)
│   ├── timeseries.html               # Multi-temporal playback timeline
│   ├── comparison.html               # Direct swipe comparison view
│   ├── studio.mjs / studio.css       # Studio modular components and design tokens
│   ├── change-lab.mjs / change-lab.css
│   ├── terrain-view.mjs              # WebGL 3D terrain & 2D fallback renderer
│   └── public/cases/nepal_case_01/   # Public Cloud-Optimized GeoTIFFs, WebP, & GeoJSON
│
├── tests/                            # Automated Testing Suites
│   ├── test_science.py               # Radar and analytical tests
│   ├── test_flood_model.py           # Flood escalation and monotonicity tests
│   ├── test_landslide.py             # Terrain and susceptibility tests
│   ├── test_timeseries.py            # Time-series persistence tests
│   └── *.test.mjs                    # Node.js UI logic and controller tests
│
├── scripts/                          # Packaging & Verification Utilities
│   ├── check_web.py                  # Static HTML/CSS validator
│   ├── package_release.py            # Release bundler with SHA-256 manifests
│   └── verify_release.py             # Zero-dependency release integrity verifier
│
└── docs/                             # Comprehensive Documentation & Reports
    ├── DATASETS.md                   # Complete data provenance and access rules
    ├── METHODOLOGY.md                # Scientific formulations and processing steps
    ├── VALIDATION.md                 # Verification protocols and criteria
    ├── LIMITATIONS.md                # Scientific constraints and edge cases
    ├── FINAL_PROJECT_READINESS.md    # Readiness diagnosis and audit matrix
    ├── SUBMISSION_BRIEF.md           # 3-minute presentation script and challenge brief
    └── reports/                      # QA test logs, prior artifact hashes, and figures
```

---

## 📚 Documentation Directory

For in-depth architectural, scientific, and challenge details, explore the complete documentation suite:

- 🔎 [**Released Challenge Review & Next-Level Strategy**](docs/CHALLENGE_STRATEGY_2026-10-28.md): Evidence audit, alternative project directions, data feasibility, prioritized upgrades, and review preparation.
- 📖 [**Submission Brief & Narrative**](docs/SUBMISSION_BRIEF.md): Executive summary, 3-minute presentation script, and challenge alignment.
- 📋 [**Final Project Readiness Diagnosis**](docs/FINAL_PROJECT_READINESS.md): Audit table of identified gaps, solutions, and verification results.
- 🛰️ [**Dataset Provenance & Ingestion**](docs/DATASETS.md): Exact granule IDs, bounding coordinates, and download procedures.
- 📐 [**Methodology & Algorithms**](docs/METHODOLOGY.md): Mathematical formulations for dB conversion, robust MAD cutoffs, and terrain metrics.
- ⚠️ [**Scientific Limitations**](docs/LIMITATIONS.md): Transparent disclosure of radar ambiguity, spatial resolution, and validation constraints.
- 🤖 [**AI Assistance Record**](docs/AI_USE.md): Disclosure of code-generation assistance and deterministic runtime separation.
- 📈 [**Progress & Milestones**](PROJECT_PROGRESS.md): Full chronicle from raw HDF5 discovery to implementation 07.

---

## ⚖️ License & Attribution

- **Code License:** [Apache 2.0](LICENSE) © 2026 DevAtMad.
- **NASA Data:** Distributed under NASA Earth Science Open Data Policy.
- **USGS Landsat:** USGS/NASA Landsat data distributed via USGS Public Domain.
- **DEM Data:** NASADEM courtesy of NASA JPL.
- **Landslide Catalog:** NASA/GSFC Global Landslide Catalog courtesy of Kirschbaum et al. (2010, 2015).
