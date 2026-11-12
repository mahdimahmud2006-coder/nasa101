# README images and measurements

The gallery uses the checked static Atlas build `cb8a034621aa7903`. The interface captures show the real browser at 1440 × 1000. The four radar figures are byte-for-byte copies of the build’s admitted display derivatives. NASA–ISRO NISAR observations were distributed through NASA Earthdata and ASF DAAC. Preview dimensions and native grid spacing are separate. [Preview asset review](ATLAS_ASSET_REVIEW.md) · [ASF product guide](https://nisar-docs.asf.alaska.edu/products-overview/)

| Figure | Source or capture state | SHA-256 |
| --- | --- | --- |
| [Atlas interface](readme-media/atlas-kathmandu.webp) | Guided Kathmandu chapter. Reference 19 August and selected visit 12 September 2026, HH backscatter. | `babd59a0b6bf46d40d0b366cdc1e3e9b3e03751926fc87e89d73c67c47e30d09` |
| [Simulations interface](readme-media/simulations-river-surge.webp) | Jamuna surge screen, +2.0 m assumed stage, with the 16 October 2026 HH backdrop. | `0066c86fa0f7717b0910c1d6c60174d02168f78d413a9125e40ad63056e033a1` |
| [Jamuna HH](readme-media/jamuna-hh.webp) | 16 October 2026, GCOV track 069 / frame 014. | `9dfd047f133c0a27cf280705d9fef6c035aa4b562079adf7222c607c7ab5556b` |
| [Tanguar Haor HV](readme-media/tanguar-hv.webp) | 16 October 2026, a separate crop from the same track 069 / frame 014 GCOV granule. | `423f576c3b3910b5c5068b98759cba4e6663d6f43e9f4ae8aa880d08ed896065` |
| [Kathmandu HH](readme-media/kathmandu-hh.webp) | 18 October 2026, GCOV track 098 / frame 016. | `dcb39026d6490e04e21df9847a206e6cf879566dec3e3cbd8c58e17a5d547991` |
| [Rasuwa–Nuwakot coherence](readme-media/rasuwa-coherence.webp) | 31 August–12 September 2026, GUNW track 098 / frame 016, 20 m grid. | `814dc5009b85bd1359d6cc91be255670abe3653c2187706a417117d133af3bfb` |

Full granule identifiers for the radar figures

```text
NISAR_L2_PR_GCOV_033_069_A_014_4005_DHDH_A_20261016T232132_20261016T232206_P05023_N_F_J_001
NISAR_L2_PR_GCOV_033_098_A_016_4005_DHDH_A_20261018T233918_20261018T233952_P05023_N_F_J_001
NISAR_L2_PR_GUNW_029_098_A_016_030_4000_SH_20260831T233918_20260831T233952_20260912T233918_20260912T233952_P05023_N_F_J_001
```

## Desktop load measurement

On 13 November 2026, the default Jamuna comparison was measured in headless Chrome `157.0.8103.38` at 1440 × 1000 with cache disabled. Each run opened a fresh browser tab on the local static preview at `/?benchmark=1`. The preview server simulated 20 Mbps aggregate downstream throughput and a 100 ms response delay. The application’s `atlas-first-usable` performance marker records when the selected and reference previews have decoded on the initial comparison. [Preview server](../scripts/serve_atlas_candidate.py) · [Browser measurement](../web/atlas-map.mjs)

| Run | Elapsed time (ms) |
| --- | ---: |
| 1 | 577.9 |
| 2 | 519.5 |
| 3 | 533.9 |
| 4 | 517.1 |
| 5 | 531.4 |
| **Median** | **531.4** |

The release manifest records **474,928 bytes** of compressed response bodies in the initial-view inventory and **8,038,780 bytes** for the standalone HTML. The desktop test describes this machine, release and preview network profile. Actual performance depends on the device, network and hosting conditions.
