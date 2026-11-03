# H1 — Bangladesh 17 August dark-signature dip

Status: **unresolved**. Recorded 2 November 2026 (Asia/Dhaka). The six shared source scenes were reused for separate Jamuna and Tanguar crops; these crops are not independent acquisitions.

The original uncalibrated dark-candidate areas remain unchanged. Putative control targets were selected by a fixed rule using only the first-date HH 85th percentile, median DEM elevation and slope below 10 degrees. The mask and its SHA-256 were written before calculating later-date control statistics. These targets have not been independently established as stable or built-up; prior project dates were already known, so this is an algorithmic freeze, not a claim of blinded prospective validation.

| Crop | Common control pixels | 17 Aug HH median shift from 18 Jun | HV shift |
|---|---:|---:|---:|
| Jamuna | 489,210 | about +0.44 dB | about +0.44 dB |
| Tanguar | 329,104 | about +1.53 dB | about +1.57 dB |

The controls differ substantially between crops. Tanguar also shows substantial control drift on later dates. A spatially varying physical change, putative-control instability or a measurement/processing effect remains possible; the observations do not establish a scene-wide calibration correction. No offset was subtracted or threshold retuned.

**Tests run:** frozen first-date/DEM control selection, common-valid controls across every visit, full crop filtered HH/HV histograms, and streaming histograms of every native pixel of all six full Bangladesh source scenes (both channels, source quality masks and valid looks). Full-source histograms use raw log-power and are explicitly separate from filtered crop histograms. Histogram count/tail totals reconcile to valid pixels.

**Rain test:** scientific GPM_3IMERGHH V07 catalog queries returned zero matching granules over every requested case/time window. CMR collection metadata currently ends on 30 September 2025. The earlier rejected GIS zero artifacts and Nepal POWER data are not used as IMERG. The exact UTC 24/72/168-hour and prior-visit windows are exported, with totals null and source/query evidence attached. The rainfall explanation therefore remains untested, not disproved.

**Next evidence:** independently stable targets/optical inspection, accepted date-matched scientific rainfall and instrument/processor QA. The official acquisition gap is temporal context; it does not prove the dip was instrumental. No physical cause is selected.

Sources: `web/public/cases/{jamuna_river,tanguar_wetland}/context-v2/`, `data/context/context-v2/h1_source_histograms.json`, `rain_availability.json` and retained source queries. Existing NASADEM context has separately documented US provider/upstream provenance; no Chinese source supplied new data.
