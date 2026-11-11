# TerraPulse judging quickstart

TerraPulse helps you compare dated radar observations on the same footprint and decide what evidence to check next.

## Start offline

Open `TerraPulse.html` in a desktop browser. You can open the four saved study windows, compare radar visits, use the guided chapters, and verify saved dossiers without a server.

1. Select **Kathmandu**, or start a guided story and choose chapter 3.
2. Choose **12 September 2026** in the timeline. On the tracked 1.99 ha footprint, HH increased **+0.45 dB** from the preceding visit while remaining **−7.08 dB** below the fixed reference. The comparisons use **199 paired-valid pixels**.
3. Choose **Reopen dossier**, select `examples/Kathmandu-dossier.json`, then choose **Reopen and verify**. A successful verification restores the saved footprint and view.
4. Choose **Tour → 30-second spotlight** for a timed introduction.

## Run the static preview and simulations

Extract the archive into one folder. From that folder, run:

```bash
python3 -m http.server 8017 --bind 127.0.0.1 --directory static
```

Open [the local preview](http://127.0.0.1:8017/). Keep the terminal running while using the preview. Choose **Simulations** for river surge, bank retreat, slope stability, sensor orbit, and the NISAR sensor model. Both the observations and models use assets in this archive. Native point and polygon measurements require the full project server.

The evidence ladder reports the measured support, available dated context, and held-out validation status. Simulated maps show the result under the selected assumptions. Keep the dates, units, and coverage with any screenshot or dossier.

In Jamuna, choose **Find comparison data → Compare with previous visit in NASA Worldview**. The two OPERA water maps are dated 5 and 17 October. The panel shows their offsets from the NISAR visits. The browse comparison requires internet access.

The included `release-manifest.json` lists the version, inventory, and SHA-256 checksums. The static folder contains source and UI credits, font licenses, and the preview STAC catalog.
