# Preserved and extended KNIME workflow

The repair starts from the original archive, retaining node IDs 1–26, all 34 original connections, formulas, Pivot settings and four mathematical Python scripts. It discards only old execution caches that contain incompatible historical geometry cells. `knime/setup/repair_workflow.py` produces the unpacked repair source. Execution and import status are recorded separately in `VALIDATION_REPORT.md`; a structural XML test alone is not native validation.

| Node | Input | Processing and output |
|---|---|---|
| 27 Initialize Project (new) | Workflow data area | Resolves `data/case10_project`; audits supplied files; recovers validated cached speeds; writes processed geometry; emits portable input-path flow variables and a parameter table |
| 1 GeoFile Reader | Original centroid ZIP, path from #27 | Reads 136 points and unmodified original attribute schema |
| 2 GeoFile Reader | Recovered road GeoPackage, path from #27 | Reads 330 original roads, `speed`, `speed1` |
| 3 Geospatial View | #2 | Road speed visualization; real basemap disabled |
| 4 Road Network Distance Matrix | #1 on origin and destination ports, #2 on road port | `ORIG_FID` identifiers, geometry columns, `speed` in mph; 18,496 OD records |
| 5 Joiner | #4, #1 | Matches Origin ID to ORIG_FID; attaches origin perimeter |
| 6 Joiner | #5, #1 | Matches Destination ID to ORIG_FID; attaches destination perimeter |
| 7 Math Formula | #6 | Adds original `netwkTime` perimeter-adjusted duration |
| 8 and 13 Math Formula | #7 | Original inverse-cost friction (`pow($netwkTime$,-1)`) |
| 9 and 14 Pivot | #8 / #13 | Rows from Origin ID, columns from Destination ID, First(G), numeric pivot names |
| 10 and 15 RowID | #9 / #14 | Sets RowID from Origin ID and removes that data column |
| 11 Math Formula (Multi Column) | #10 | Column normalization times 0.3, service allocation matrix |
| 16 Math Formula (Multi Column) | #15 | Column normalization times 2, residential allocation matrix |
| 12 and 17 Table Transposer | #11 / #16 | Supplies the legacy matrix orientation to #18 |
| 18 Python Script | #12, #17 | Original identity-minus-product calculation, two table inputs |
| 19 Column Filter | #1 | Keeps BEMP_Unif, the actual saved-workflow baseline |
| 20 Python Script | #16, #19 | Original residential matrix multiplied by basic jobs, GB |
| 21 Python Script | #18, #20 | Original LU solution with transpose; 136 population values |
| 22 Python Script | #11, #21 | Original service matrix multiplied by population, TP |
| 23 Column Filter | #1 | Keeps TRACT0_ID for the original transect plot |
| 24 Column Appender | #22, #21, #23 | Full 136-zone native result: `0`=service jobs, `0 (#1)`=population, TRACT0_ID |
| 25 Row Filter | #24 | Original ten-zone radial transect with TRACT0_ID 1–10 |
| 26 Line Plot (Plotly) | #25 | Original transect chart; do not mistake its ten rows for the full city |
| 28 Read Zone Polygons (new GeoFile Reader) | #27 flow variable | Reads verified polygons with unique zone_id |
| 29 Validate and Run Scenarios (new Python Script) | #24 full baseline and #7 OD records | Checks native baseline against independent solver; only then runs seven experiments, exports tables/GPKG/PNG/HTML and returns 952 scenario-zone rows |
| 30 Join Scenarios to Geometry (new Joiner) | #28 and #29 | Inner join on unique zone_id, repeated once per scenario; 952 geometric result rows |
| 31 Select Baseline Map (new Row Filter) | #30 | Keeps scenario=baseline_uniform, 136 polygons |
| 32 Population Geospatial View (new) | #31 | Native population choropleth, basemap disabled |

The original mathematics is explained in `METHODOLOGY.md`, including the limited commutation assumption behind the original transposed solver. The extension uses a separate tested core for general unequal exponents. KNIME adapters use the supported `knime.scripting.io` API; the independent core does not import KNIME.

Generated outputs inside an imported workflow are under **`data/case10_project/outputs/`**. Project-level outputs produced from VS Code are under **`outputs/`**. The workflow contains its own copies of the core code and original inputs, so importing it elsewhere does not require an absolute workspace data path. A compatible Python environment is still required; see `KNIME_SETUP.md`.
