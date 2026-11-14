# TerraPulse judging quickstart

TerraPulse helps you compare dated radar observations on the same footprint and decide what evidence to check next.

## Start offline

Open `TerraPulse.html` in a desktop browser if you received a judging bundle. From the public source checkout, run `python3 scripts/package_atlas.py` and open `output/atlas/TerraPulse.html`. Both give you the four saved study windows, recorded visits, guided chapters and dossier verification without a server.

1. Choose **Tour → Start guided story** and open chapter 3, **Kathmandu**.
2. Choose **12 September 2026** in the timeline. On the tracked 1.99 ha footprint, HH increased **+0.45 dB** from the preceding visit while remaining **−7.08 dB** below the fixed reference. The comparisons use **199 paired-valid pixels**.
3. If you have the bundle, use its `examples/Kathmandu-dossier.json`. From the source build, use **Export → Investigation dossier** after step 2. Choose **Reopen dossier**, select the JSON file, then choose **Reopen and verify** to restore the saved footprint and view.
4. Choose **Tour → 30-second spotlight** for a timed introduction.

## Run the static preview and simulations

This section applies to the separately prepared static bundle. Extract it into one folder, then serve its `static/` directory with the following command.

```bash
python3 -m http.server 8017 --bind 127.0.0.1 --directory static
```

Open [the local preview](http://127.0.0.1:8017/). Keep the terminal running while using the preview. Choose **Simulations** for river surge, bank retreat, slope stability, sensor orbit, and the NISAR sensor model. Both the observations and models use assets in this archive. Native point and polygon measurements require the full project server.

The evidence ladder reports the measured support, available dated context, and held-out validation status. Simulated maps show the result under the selected assumptions. Keep the dates, units, and coverage with any screenshot or dossier.

In Jamuna, choose **Find comparison data → Compare with previous visit in NASA Worldview**. The two OPERA water maps are dated 5 and 17 October. The panel shows their offsets from the NISAR visits. The browse comparison requires internet access.

The included `release-manifest.json` lists the version, inventory, and SHA-256 checksums. The static folder contains source and UI credits, font licenses, and the preview STAC catalog.
