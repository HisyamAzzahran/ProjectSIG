# Scenario analysis

The actual saved original workflow uses uniform basic employment; this is the reference scenario. The manual introduces a CBD baseline instead. Both are represented without confusing their provenance. Every experiment conserves the stored source total of 99.999984 basic jobs. CBD employment is rescaled from the supplied BEMP_CBD total of 100 by a factor of 0.99999984 solely to preserve this controlled comparison.

| Scenario | Employment | Equal friction exponents | Speed | CBD population | Population-weighted radius, projected m |
|---|---|---:|---|---:|---:|
| baseline_uniform | Original BEMP_Unif | 1 | 30 mph | 5.429510 | 2764.184367 |
| cbd_employment | Original CBD pattern, total conserved | 1 | 30 mph | 9.150670 | 2543.428486 |
| low_friction | Original BEMP_Unif | 0.5 | 30 mph | 4.452146 | 2960.008872 |
| high_friction | Original BEMP_Unif | 2 | 30 mph | 7.987321 | 2382.965159 |
| beltway | Original BEMP_Unif | 1 | Ring 7: 75 mph, other roads: 30 mph | 5.178644 | 2841.269286 |
| cbd_high_friction | CBD | 2 | 30 mph | 21.865265 | 1894.648706 |
| cbd_beltway | CBD | 1 | Ring 7: 75 mph, other roads: 30 mph | 8.969388 | 2593.220443 |

Each scenario totals approximately **499.999920 model persons**, **149.999976 service jobs**, and **249.999960 total jobs**. These totals are determined algebraically by the fixed demographic multipliers and basic employment total. Scenario effects therefore concern spatial allocation rather than total city growth. Precise diagnostics and additional indicators are in `outputs/tables/scenario_comparison.csv`.

## Controlled effects

Concentrating basic jobs in the CBD increases CBD population and reduces the population-weighted radius by about 221 m relative to the saved uniform baseline. Uniform basic jobs still produce a nonuniform residential distribution because network accessibility and local impedances vary spatially.

With uniform jobs, reducing both friction exponents from 1 to 0.5 increases the weighted radius by about 196 m; raising them to 2 reduces it by about 381 m. The model places more residents near accessible locations when travel impedance is penalized more strongly. With CBD jobs and friction 2, CBD population reaches about 21.865 model persons, compared with 9.151 under CBD jobs and friction 1. This extra CBD case follows the manual's intended sensitivity comparison.

The beltway experiment uses the original recovered `speed1` attribute, changing 20 real supplied road features on ring 7. Shortest paths are recalculated on this modified graph. No shortest network duration increases. Under uniform basic employment the weighted population radius increases by about 77 m, while CBD population decreases by about 0.251. The additional CBD beltway case also shifts population outward relative to the CBD-employment case (about 50 m in weighted radius). These are specific results of this model and parameterization, not a universal claim about real beltways.

## How to read the figures

`05_scenario_population.png` uses the same continuous colour range across all seven panels. `06_population_change.png` uses a common symmetric change range about zero relative to the saved uniform baseline. `07_beltway_change.png` explicitly uses a separate smaller symmetric scale to make the relatively small beltway effect visible. Do not compare colour intensity across these different figure scales without reading the legends.

The offline `interactive_scenarios.html` provides actual polygon geometry, scenario selection and zone-level values. GeoPackage files retain EPSG:3857 geometry for GIS review. Maps represent counts per polygon, not population density. Radial means are a summary of all zones, while the preserved original Plotly line chart shows only the ten labelled transect zones.

## Limitations

The model has uniform attraction weights, no housing capacity constraint, no endogenous congestion, and no migration dynamics. EPSG:3857 metre lengths and legacy perimeter attributes are intentionally kept consistent with the original calculation rather than recalibrated. The low-friction value 0.5 is an explicitly added sensitivity experiment; the higher value 2 and ring-7 speeds are documented in the supplied manual. Original POP/SEMP fields containing zeros were never treated as reference predictions.
