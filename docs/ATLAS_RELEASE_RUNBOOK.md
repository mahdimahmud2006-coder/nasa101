# Build and verify the Atlas release

## Build and inspect

Run `make atlas-portable` for the standalone Atlas. Run `make check-atlas-static` once the processed runtime is installed. Read `output/atlas/release.json` for the versioned manifest and its `static/` folder. The matching `TerraPulse.html` lives beside the manifest. Preview locally with `.venv/bin/python scripts/serve_atlas_candidate.py` and open `http://127.0.0.1:8017/`. Open the offline HTML in a browser or use `/offline/` for an isolated rehearsal that denies fetches and external images.

The public candidate serves saved observations and footprints. It loads the default study window and its initial HH comparison on entry. Other windows, layers and terrain load on demand. Download field-check GeoJSON or the replay notebook from **Fieldwork and reproducibility**. The preview STAC catalog is at `stac/catalog.json`. See [asset review and credits](ATLAS_ASSET_REVIEW.md) and [AI contributions](AI_USE.md).

The full local edition supports native footprints and custom Kathmandu scenarios. Build the native catalog with `make atlas-native-stac` and open `/atlas-catalog/catalog.json` on the local server. Its links point to the 144 GeoTIFFs in the full runtime. To rebuild the historical land-cover summaries, run `.venv/bin/python scripts/fetch_atlas_worldcover.py` and `.venv/bin/python scripts/build_atlas_contracts.py`.

Build the **What if?** scenarios with `make atlas-simulations` before staging the static preview. The two Bangladesh cases offer a stage and barrier opening screen; the two Nepal cases offer a slope and shaking screen. The single-file edition retains the observation workflow, and the separate UNOSAT comparison stays local. [Scenario methods and inputs](ATLAS_SCENARIOS.md).

## Publication approval and checks

Once the account owner approves the exact manifest and identifies the Cloudflare project, use [Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) with only the manifest's versioned `static/` folder. Record the canonical HTTPS URL, deployment ID, the static inventory SHA-256 and a rollback deployment if there is one. To roll back, reinstate the previous approved production deployment. If the first public release must be withdrawn, unpublish that project with the account owner.

On the exact public URL, use a fresh logged-out desktop browser and a phone on mobile data. Run all four guided chapters, export a Bangladesh dossier, and reopen it in a fresh session. Check the expected results, share link and approval scope. Repeat the five cold-load benchmark runs with the agreed browser and network profile. Open the matching portable file while disconnected. Record devices, versions, timings and any link or access failure. Use [the pilot protocol](ATLAS_PILOT.md) for participant results.
