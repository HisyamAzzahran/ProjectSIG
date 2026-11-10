# Validation report

Verified on 10 November 2026, Asia/Jakarta. Evidence comes from actual supplied data, test execution, KNIME GUI execution, native export and native import. No fabricated screenshots or success logs are used.

## A. Fully implemented and tested

- **25 pytest cases passed; 0 failed.** Command: `.venv/Scripts/python.exe -m pytest tests -q --junitxml outputs/logs/pytest.xml`.
- Supplied geography: 136 valid polygons, 136 valid centroid points, 330 valid road features; spatial IDs and joins verified.
- Connected undirected augmented graph: 331 vertices, 466 edges; no artificial topology links required.
- Full 136 × 136 shortest-path matrix, 18,496 OD pairs; nonnegative, finite, symmetric; zero network diagonal and positive amended-cost diagonal.
- Original numerical baseline replayed, preserved native mathematical nodes, seven reproducible experiments, GeoPackage joins, maps, charts and offline HTML.
- Original cached population replay max error: `6.21725e-15`; service replay max error: `1.55431e-15`.
- Independently rebuilt network duration max error: `8.30592e-08` minutes.
- Actual KNIME baseline vs independent solve: population `3.55271e-15`, services `1.11022e-15`.
- **32/32 nodes executed and saved in KNIME 5.12.0**, including original nodes 1–26, native Road Network Distance Matrix, native LU scripts, Plotly chart, scenario runner, native geometry Joiner and Geospatial View.
- Native output row counts: #4 = 18,496; #24 = 136; #29 = 952; #30 = 952; #31 = 136.
- **Final archive exported by the actual KNIME GUI**: `knime/Case10_Garin_Lowry_Final.knwf`. ZIP integrity, native XML metadata, 32 saved executed nodes, embedded original inputs and current core code checked.
- **Archive imported using the actual KNIME GUI** as `Case10_Final_Reimport_Validation`.
- **Imported workflow reset and executed again: 32/32 nodes EXECUTED; Initialize Project resolved the new directory; native baseline validation passed.**

## B. Scope of unverified portability

Execution on another Windows machine, another KNIME version or a different extension version has not been tested. Portable data-area paths and the documented environment rebind helper are provided. The verified configuration uses the project .venv and the project-local compatibility copy of Geospatial Analytics 2.1.0. Starting standard KNIME without this override can reproduce the installed extension bug.

## C. Specific automation limitation

The separately installable KNIME Batch Executor is absent. Command-line batch execution was actually attempted and returned “KNIME Batch Executor is not installed”. GUI execution succeeded, so this does not block the delivered workflow. No additional batch installation, publication or paid service was used.

## Resolved execution failures

| Failure observed | Resolution | Status |
|---|---|---|
| Absent E: input paths | Initialize Project resolves paths from the imported workflow data area | Resolved |
| Old GeoPointCell / GeoLineCell cache loading | Reset execution data and recreate geometry through native readers | Resolved |
| Four missing second Python input connections in damaged workspace copy | Derive repair from untouched original archive with dynamic port configurations | Resolved |
| Missing road speed fields | Recover cached original speed and speed1 after complete key/WKB identity checks | Resolved |
| Pandas 3.1.1 Arrow large_string rejected | Pin isolated environment to Pandas 2.3.3 | Resolved |
| GeoValue is not subscriptable in KNIME | Accept native GeoValue.wkb and ordinary Arrow struct representations | Resolved |
| Native Road Network groupby tuple KeyError | One-line scalar-key fix in project-local extension copy; installed source untouched | Resolved |
| KnimePandasExtensionArray factorization unsupported | Convert cached scalar columns to ordinary Pandas dtypes before pivot/groupby | Resolved |

## Automated cases

Each case below executed without failure. Synthetic cases establish known mathematical behavior; separate integration cases establish actual supplied-data processing.

| Test | Expected / checked behavior | Actual | Status |
|---|---|---|---|
| `test_geography_counts_and_crs` | Actual supplied feature counts, CRS and valid geometries | Passed | PASS |
| `test_zone_identity_and_spatial_join` | Unique IDs, full point-in-polygon matching and CBD identity | Passed | PASS |
| `test_recovered_road_speed_and_graph` | Recovered speeds, graph connectivity and feature count | Passed | PASS |
| `test_od_dimensions_diagonal_symmetry_and_coverage` | OD coverage, symmetry, diagonal and finite travel costs | Passed | PASS |
| `test_original_workflow_mathematics_and_network_replay` | Cached baseline replay and independently rebuilt road OD | Passed | PASS |
| `test_network_scenario_is_recalculated_and_no_cost_increases` | Speed change rerouted; no cost increases; distance unchanged | Passed | PASS |
| `test_deterministic_baseline` | Exact repeatability of numerical baseline and convergence history | Passed | PASS |
| `test_export_schema_conservation_and_complete_gis_joins` | Seven scenario schemas, conservation identities and full GIS joins | Passed | PASS |
| `test_original_inputs_unchanged` | Original workflow and geographical inputs byte-identical | Passed | PASS |
| `test_archive_traversal_is_rejected` | Reject malicious ZIP path traversal | Passed | PASS |
| `test_single_zone_known_solution` | One-zone closed-form P=500, S=150 | Passed | PASS |
| `test_two_equal_cost_zones_known_solution` | Two equal-cost zones P=[250,250], S=[75,75] | Passed | PASS |
| `test_independent_allocation_with_unequal_exponents` | Correct noncommuting G@T orientation and method agreement | Passed | PASS |
| `test_invalid_cost_is_rejected[cost0]` | Reject nonpositive, nonfinite or nonsquare cost | Passed | PASS |
| `test_invalid_cost_is_rejected[cost1]` | Reject nonpositive, nonfinite or nonsquare cost | Passed | PASS |
| `test_invalid_cost_is_rejected[cost2]` | Reject nonpositive, nonfinite or nonsquare cost | Passed | PASS |
| `test_invalid_cost_is_rejected[cost3]` | Reject nonpositive, nonfinite or nonsquare cost | Passed | PASS |
| `test_unstable_feedback_is_rejected` | Reject feedback h*e >= 1 | Passed | PASS |
| `test_negative_employment_is_rejected` | Reject negative basic employment | Passed | PASS |
| `test_iteration_limit_is_enforced` | Fail safely when iteration limit is exceeded | Passed | PASS |
| `test_zero_service_feedback` | Zero feedback yields P=hB and S=0 | Passed | PASS |
| `test_gui_export_contains_executed_native_workflow_and_inputs` | Native GUI archive metadata, all executed nodes and embedded input bytes | Passed | PASS |
| `test_native_baseline_and_full_city_output_evidence` | Native baseline tolerance and saved executed-node evidence | Passed | PASS |
| `test_original_nodes_and_connections_preserved` | Preserve all original nodes and connections; valid settings XML | Passed | PASS |
| `test_original_equations_and_scripts_preserved` | Preserve original formula strings and mathematical scripts | Passed | PASS |

## Evidence files

- `outputs/logs/pytest.log` and `pytest.xml`: actual test output.
- `docs/baseline_validation.json`: original cached/rebuilt numerical comparisons.
- `outputs/logs/native_node_states.json`: all 32 saved original-session native node states and output summaries.
- `outputs/logs/final_artifact_manifest.json`: export hash, native validation and reimport status.
- `knime/validation_workspace/.metadata/knime/knime.log`: raw KNIME execution log, including failed attempts followed by fixes.
- `outputs/logs/knime_batch_help.log`: actual missing batch-extension response.
- GUI screenshots in `outputs/logs/`: real load, export, import and final workflow evidence.

## Scientific limits

No empirical forecast validation is claimed. Counts are fractional model quantities. Input historical perimeter units are retained for exact baseline reproduction; geometry lengths use projected EPSG:3857 metres. Exponents must remain equal in the untouched native transpose pipeline; unequal exponents use the tested explicit G@T core. The original workbook result fields containing zero were not used as predicted truth.
