# Case 10 data and workflow audit

Audit date: 10 November 2026 (Asia/Jakarta). Original inputs remain read-only. Machine-readable details, complete fields, missing values, bounds and SHA-256 hashes are in `data_audit.json`. Complete original node settings and connections are in `original_node_configurations.json` and `original_workflow_configuration.json`.

## Discovered sources

All paths below are relative to `SIG/Studi Kasus KNIME/` unless stated otherwise.

| Actual source | Findings | Use |
|---|---|---|
| `Case10-Implementing the Garin-Lowry Model in a Hypothetical City.knwf` | Original saved workflow, created with KNIME 5.1.0; 26 nodes, 34 connections; includes executed Arrow tables | Preserved in `original/`; primary workflow source and numerical reference |
| `Data/Lousiana/tract.zip` | 136 valid Polygon features, EPSG:3857 | Zone polygons |
| `Data/Lousiana/trtpt.zip` | 136 valid Point features, EPSG:3857 | Supplied centroids, unique `ORIG_FID` values 1–136 |
| `Data/Lousiana/road.zip` | 330 valid LineString features, EPSG:3857 | Actual transport network |
| `Data/SimuCity/I-GTmatrix.py` | Computes identity minus a matrix product using `knime.scripting.io` | Inspected, preserved |
| `Data/SimuCity/Matrixdot.py` | Matrix multiplication | Inspected, preserved |
| `Data/SimuCity/SLE.py` | LU factorization and solution of the transposed input coefficient matrix | Inspected, preserved |
| `Data/SimuCity/ODVillage.csv`, `ODhosp41.csv` | Dimensions/identifiers do not match the 136-zone case | Audited but excluded from city calculations |
| `SIG/Lingbo Liu Lab Manual.pdf` and the longer similarly titled PDF in `SIG/` | Case 10, printed pp. 196–203, PDF pp. 215–222 | Supplied primary methodological reference |

No replacement geographical dataset was downloaded. The source folder called `Lousiana` contains the correct hypothetical geometry despite its misleading name. The original `SimuCity` folder does not contain the expected three geographic archives.

## Schema, identifiers and geometry

The polygons contain `AREA`, `PERIMETER`, `TRACT0_ID`, `Shape_Leng`, `Shape_Area`, `BEMP_Unif`, `BEMP_CBD`, four `POP_*` and four `SEMP_*` fields. Centroids have corresponding attributes and `ORIG_FID`, but no `Shape_*` fields. All input population/service result fields are zero; these are empty result slots, not validated reference outputs.

`TRACT0_ID` is a ten-zone radial transect label: 126 records contain zero, and ten records contain 1–10. It must never be used as a unique geographical key. `ORIG_FID` is unique on centroids. Each polygon contains exactly one supplied centroid; this verified spatial correspondence gives the polygon its `zone_id`. The CBD is zone **71**, with `TRACT0_ID = 1`. Sorted polygon and centroid employment, perimeter, area and transect attributes agree.

There are no missing geometries or invalid features. Road `TYPE` contains 140 missing labels; the graph uses geometry and speed, so these do not prevent routing. Nonmissing labels include 130 `ring` and 20 each of `r7`, `r8`, `r9`. The 330 road features should not be interpreted as 330 independent ring roads. The city geometry represents one CBD and nine outer rings divided into 15 sectors, giving 136 zones.

## Units and speed recovery

All three geographic sources declare EPSG:3857, whose planar unit is metre. This is a hypothetical placement, not evidence of a real city near those coordinates. No real-world basemap is used. Calculations use projected polyline length; `LENGTH`, `LENGTH1` and `Shape_Leng` are legacy attributes and are not substituted for measured geometry length.

The manual describes `PERIMETER` as kilometres and `AREA` as square kilometres. The projected road lengths divided by legacy `LENGTH` are approximately 1003–1010, rather than exactly 1000. The original perimeter-based correction is preserved explicitly to reproduce the case; its cost is a model impedance in minutes, not calibrated observed journey time.

The supplied road archive omits `speed` and `speed1`, even though the workflow requires them. Both are recoverable from the **original workflow's cached GeoFile Reader #2**. All 330 `ROAD0_` keys and all cached WKB geometries are checked against the supplied SHP before joining speeds. Baseline `speed` is 30 mph everywhere. `speed1` changes the 20 `TYPE=r7` features to 75 mph, leaving other roads at 30 mph. This exactly matches the supplied manual's beltway experiment. These values were recovered, not invented.

## Network and cached reference

The road graph uses an undirected model, continuous nearest-edge centroid projection, and splitting at projected points. The augmented graph has 331 vertices and 466 edges and is connected. No topology bridges were required. Snap offsets range from about 115.47 to 317.76 projected metres. As in the original workflow, snap offsets are recorded separately; the perimeter correction supplies local access costs.

The original Road Network Distance Matrix #4 cache contains all 18,496 OD pairs, with zero network diagonal. The reconstructed duration matrix differs by at most `8.31e-8` minutes. The corrected model impedance has strictly positive diagonal due to the perimeter term. Distance and time are calculated independently as shortest paths with their respective edge weights, consistent with the native node.

## Original nodes and faults

Section A retains GeoFile Reader #1–2, Geospatial View #3, Road Network Distance Matrix #4 and Joiner #5–6. Section B retains Math Formula #7–8/#13, Pivot #9/#14, RowID #10/#15, Math Formula (Multi Column) #11/#16, Transposer #12/#17, Python #18/#20–22, Column Filter #19/#23, Appender #24, Row Filter #25 and Plotly Line Plot #26.

The original readers reference absent paths `E:\KNIME\CMGISV3\Chp10\data\trtpt.zip` and `simroad.shp`. Old saved geospatial cell types fail to reload in the installed version. The user's pre-existing KNIME log records four missing Python second-port connections: 17→18, 19→20, 20→21 and 21→22. Saving that damaged imported copy removed dynamic port settings. Repair therefore starts from the untouched original archive, not from the damaged workspace copy.

Installed platform: KNIME 5.12.0, user-local installation at `C:\Users\Muhammad Fatih\AppData\Local\Programs\KNIME`. Installed plugins include Geospatial Analytics 2.1.0, Python Integration, JEP Math Formula, Base Nodes, and JavaScript/Plotly Views. Original geospatial caches are reset in the repair copy so modern nodes can recreate geometry cells. The original equations, all 26 node IDs and all 34 connections are retained. Workflow-relative input paths are resolved by initialization flow variables. Batch execution was actually attempted and refused because the separately installed **KNIME Batch Executor** extension is absent; see logs and the final validation report for GUI validation status.

## Baseline decision

The manual's introductory baseline is monocentric (`BEMP_CBD`). The actual supplied saved workflow selects **`BEMP_Unif`** in Column Filter #19. The required original-workflow baseline therefore uses `BEMP_Unif`, totalling **99.999984** model jobs because of stored rounding. Its population is **499.999920**, service employment **149.999976**. CBD experiments conserve this exact stored employment total. The original cached population and services reproduce to approximately `6.22e-15` and `1.55e-15` when using the cached OD; independently rebuilt network results agree to approximately `2.95e-8` and `9.85e-9`.
