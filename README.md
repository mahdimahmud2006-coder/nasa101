# TerraPulse

TerraPulse is an interactive atlas for comparing NASA–ISRO NISAR radar observations over Bangladesh and Nepal. Follow the same piece of ground across recorded visits, compare it with a fixed reference, and export an evidence dossier with the dates, measurements and source records behind the comparison.

Built by **DevAtMad** for NASA Space Apps, *Dancing with the SARs*.

## Open the Atlas

```bash
git clone --depth 1 https://github.com/mahdimahmud2006-coder/nasa101.git
cd nasa101
python3 scripts/package_atlas.py
```

Open `output/atlas/TerraPulse.html` in a desktop browser. The standalone Atlas includes all four study windows, radar playback, saved footprints, guided chapters and dossier export. It opens offline from a single file. Access to this private GitHub repository requires an invitation.

Choose **Tour → Start guided story** or open a study window directly. Use **Fit map** to restore the full radar scene, or step through the timeline to compare recorded visits. The Atlas uses a swipe comparison for full study windows and can show small saved footprints in two aligned panes.

| Study window | What to investigate |
| --- | --- |
| **Jamuna, Bangladesh** | Where radar-dark river signatures recur and where a bank survey could clarify the apparent change. |
| **Tanguar Haor, Bangladesh** | How wetland radar returns vary across visits and how they compare with dated optical evidence. |
| **Kathmandu, Nepal** | Whether a tracked footprint still differs from its reference after the change between recent visits becomes small. |
| **Rasuwa–Nuwakot, Nepal** | Where radar phase consistency differs between admitted pairs and what independent evidence to check. |

The **Context** tab links to relevant NASA Earthdata catalog records and NASA Worldview browse imagery where available. Those external checks have their own dates and coverage. The Atlas keeps observations, interpretation and simulated outcomes distinct in the interface and exports.

## Run the local edition

Use Python 3.12 or later. The local edition adds native footprint measurements and access to specialist workspaces. Restore the existing versioned runtime assets from the private release with an authenticated GitHub CLI.

```bash
gh auth login
python3 scripts/fetch_runtime.py
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Restore or build the newer Bangladesh coherence rasters and simulation grids using [Runtime and distribution](docs/REPOSITORY_AND_RUNTIME.md). The standalone Atlas above already embeds saved coherence previews.

Run `./run.sh` and open [TerraPulse on port 8000](http://127.0.0.1:8000/), or use the address printed by the server. See [Local setup](RELEASE_README.md) for Windows and runtime verification.

The **Simulations** workspace includes river surge and barrier opening, bank retreat, slope stability, radar viewing geometry, and **Be the NISAR Sensor**. These tools explore scenarios under stated assumptions. [Scenario methods and build inputs](docs/ATLAS_SCENARIOS.md)

## Repository layout

| Path | Contents |
| --- | --- |
| `web/` | Atlas, simulations, specialist viewers and compact saved evidence. |
| `src/ingest/`, `src/compute/`, `src/export/` | Data ingestion, reproducible science and exports. |
| `src/api/` | Local application and data endpoints. |
| `contracts/`, `config*.json`, `claims/`, `rules/` | Schemas, product bindings, claim ledger and interpretation rules. |
| `scripts/`, `tests/` | Build and packaging tools, checks and regression tests. |
| `data/`, `reference/`, `reports/` | Scientific provenance, frozen reference design and verification records. |
| `docs/` | Setup, methods and source attribution. |

## Verify a checkout

```bash
make test-ui
make check-web
.venv/bin/python -m pytest -q
python3 scripts/audit_repository.py
```

The JavaScript suite and offline Atlas can run without acquired satellite data. Some Python integration tests and static release checks require the processed runtime. Full reprocessing also requires the source datasets listed in [Dataset provenance](docs/DATASETS.md). See [Build and release](docs/ATLAS_RELEASE_RUNBOOK.md) and the [independent validation protocol](docs/ATLAS_VALIDATION_PROTOCOL.md).

## Scientific sources and limits

NISAR GCOV supplies L-band backscatter. NISAR GUNW supplies pairwise coherence. NASADEM, Landsat and dated optical comparisons add terrain and environmental context. The evidence dossier records the selected reference and valid footprint support. Radar signatures can guide follow-up, but establishing a physical cause or predicting a hazard requires independent evidence.

[Data provenance](docs/DATASETS.md) · [Methodology](docs/METHODOLOGY.md) · [Limitations](docs/LIMITATIONS.md) · [UI credits](docs/CREDITS_UI.md) · [AI disclosure](docs/AI_USE.md)

<details>
<summary>Claim-to-evidence ledger</summary>

<!-- CLAIMS:START -->
- **TP-DATA · measured** — Twenty unique GCOV acquisitions support four investigation study windows: ten Nepal dates and ten shared Bangladesh dates. The Bangladesh record includes all ten available nominal visits in the displayed June–October interval. Limitation: Both crops in each country share their source acquisitions. The August 5 Bangladesh slot is a permanent satellite outage. Historical products remain separately addressable.

- **TP-PERSIST · measured** — In the 199-pixel Nepal footprint, HH baseline differences remain −7.5263 and −7.0766 dB while centered-score retained alert area falls from 0.0199 km² to zero. Limitation: Alert contraction, baseline persistence and physical recovery are distinct; cause is unresolved.

- **TP-PAIR · measured** — Original nominal pair areas remain 0.0195, 0.7949 and 0.0000 km² under their original rule. Limitation: These are not the centered-score tracked-zone areas.

- **TP-CPR · measured** — The Nepal footprint has CPR baseline changes of +5.7152 dB and +4.6256 dB on the two follow-up visits. Limitation: CPR is HV−HH in dB, the sign reversal of the existing HH−HV relation; not independent corroboration.

- **TP-TERRAIN · measured** — Case-wide median slope is 1.9495° at Jamuna and 1.3598° at Tanguar. Limitation: Terrain/geometry screening and bounded hydrology are contextual models, not validated hazard or visibility classes.

- **TP-RAIN · planned** — Frozen IMERG Final-product rain totals remain unavailable. A later NASA catalog search found Late V07 candidates, but no scientific rainfall files were supplied or imported in this batch. Limitation: Exact UTC windows remain implemented. Missing rain stays null; catalog availability does not create precipitation measurements. NASA multisensor lineage still requires review before the strict source policy can accept an import.

- **TP-H1 · measured** — The August dip remains unresolved after frozen putative-control and full-source histogram tests. Limitation: Control shifts do not establish calibration error or physical cause.

- **TP-FIT · implemented** — Versioned deterministic rules show supporting, contradicting and missing evidence for competing explanations. Limitation: Uncalibrated compatibility statuses, no probability, winning cause or runtime LLM.

- **TP-DNA · measured** — Fixed-footprint Change DNA records signed channel changes, observed-visit persistence, onset/recovery brackets and censored recovery for saved or user-selected regions. Limitation: Numeric footprint records are dynamically recomputed with source/rule provenance; retrospective selection is not independent validation.

- **TP-MECHANISMS · hypothesized** — Low-return, paired brightening, moisture/roughness, vegetation, steep-source movement and radiometric explanations remain candidate hypotheses. Limitation: Signature compatibility does not uniquely identify a physical process.

- **TP-REFERENCE · measured** — The original frozen descriptive HLS comparison has eligible optical pixels in 14 of 54 footprint/date comparisons; 40 remain unavailable. The four added Bangladesh radar dates have no newly accepted optical matches. Limitation: Only the preselected geographic footprints and eligible pixels were assessed. Mixed results are retained; this is algorithmic optical context, not classification accuracy or causal validation.

- **TP-INTERFEROMETRY · measured** — Two supplied Nepal GUNW products now provide measured native 20 m and 80 m HH coherence for August 19–31 and August 31–September 12 in both Nepal crops. Limitation: Pairwise coherence measures phase consistency. Line-of-sight displacement requires corrected phase, a stable reference and independent checks.

- **TP-CONTEXT · measured** — The corridor intersects about 6.4230 km² of preliminary mapped mudflow/rockflow impact context. Limitation: This overlap does not establish detection accuracy, flood-water truth or field validation.

- **TP-METHOD · implemented** — Illustrative numerical settings describe measurements and display, not independently calibrated classes. Limitation: Configuration parameters must not be presented as validated physical thresholds.

- **TP-NAV · implemented** — Shared navigation and investigation links preserve supported case, observed date, saved or selected footprint, mode and layer state. Three Movements opens the existing measured evidence. Limitation: Nepal-only workspaces stay explicitly scoped. Unsupported legacy layers/footprints or missing dates are disclosed instead of being treated as equivalent data.

- **TP-ACCESS · implemented** — Keyboard map inspection and polygon vertices, visible focus, reduced-motion styles and live text evidence are implemented. Limitation: Source checks and mocked interactions do not establish real-browser, assistive-technology, GPU or whole-app WCAG conformance.

- **TP-LOCAL · measured** — Checked local page assets and representative reasoning requests work through the HTTP handler while Python sockets and DNS are forbidden. Limitation: This is a scoped automated backend/source check. Browser network behavior and a physically disconnected rehearsal remain unverified.

- **TP-DELIVERY · implemented** — The portable release builder includes current runtime rules, claims and local assets and checks every archive entry against its manifest. Limitation: Dependency installation, clean judging-machine startup, browser/physical rehearsal, public repository/video access and actual submission remain separate acceptance steps.

- **TP-EXTENDED-PERSIST · measured** — The original 199-pixel Nepal footprint remains common-valid across ten visits; its October 18 HH difference from August 19 is about −6.5660 dB. Limitation: This extends the measured backscatter record. Earlier visits vary relative to August 19, which is not a verified undisturbed baseline. No continuous persistence, physical damage or recovery is established.

- **TP-ATLAS-SCENARIOS · implemented** — The Atlas runs a buffered NASADEM stage screen with an assumed barrier opening in Bangladesh and an infinite-slope sensitivity calculation in Nepal. The stage screen can show observed NISAR HH below −19.5 dB and above −11.5 dB as display bins. Limitation: The bins are not a crop classification or forecast. Barrier connectivity is not flood routing. Coherence and preliminary mapped impacts do not change soil cohesion or verify modeled slope failure.

- **TP-ATLAS-SAR-LABS · implemented** — TerraPulse compares a simulated HH/HV scattering state with the observed footprint and visit, traces a Jamuna radar-dark edge across recorded visits, and tests look geometry and wavelength sensitivity on Nepal terrain. Limitation: The simulated canopy input is not measured biomass or DpRVIc. The Jamuna corridor is not a bank forecast. The opposite look and C-band responses are hypothetical; observed coherence uses the admitted NISAR pair.

- **TP-BD-RECORD · measured** — The ten-visit Bangladesh record recomputes HH/HV differences, dual-polarization signatures, observed occupancy, sensitivity, controls and fixed-footprint evidence. Only the August 5 nominal slot remains unobserved. Limitation: Added dates improve temporal sampling; they do not establish water, erosion, habitat, causal or hazard accuracy. The separate GUNW record provides paired coherence. Scientific rainfall and thermal data are separate evidence sources.
<!-- CLAIMS:END -->

</details>
