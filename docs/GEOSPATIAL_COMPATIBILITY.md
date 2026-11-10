# Scoped native Geospatial Analytics compatibility repair

The installed `sdl.harvard.geospatial` bundle is version 2.1.0.202610271233. During real KNIME execution, Road Network Distance Matrix #4 failed with:

```text
KeyError: 'key of type tuple not found and not a MultiIndex'
```

The traceback leads to `src/nodes/spatialnetwork.py`, in the construction of `line_pps_dict`. With current Pandas, a single-column list grouper produces tuple group keys. The following code then attempts to index a normal edge series with that tuple.

The project contains a licensed copy of the installed extension's Python source under `knime/setup/geospatial_compat/`. Exactly one semantic line changes:

```diff
- k: MultiPoint(list(v)) for k, v in POI.groupby(["kne_idx"])["pp"]
+ k: MultiPoint(list(v)) for k, v in POI.groupby("kne_idx")["pp"]
```

The scalar grouper preserves grouping by the same nearest-edge ID and returns the scalar index expected downstream. There is no change to the road graph, speed conversion, snapping, shortest-path algorithm or returned output schema. This repaired native node was actually executed within KNIME and the resulting baseline passed an independent equilibrium comparison.

`launch_knime.py` uses KNIME's supported custom Python-extension source configuration, supplied as a JVM property for that process. The source and configuration files live entirely inside this project. The installed `knime.ini`, installed extension files and the user's original workspace are unchanged. The extension continues to use its existing bundled geospatial Python environment; the Garin–Lowry Script nodes use the isolated project `.venv`.

The official registration and custom executable mechanism is documented in [KNIME's Python node extension guide](https://docs.knime.com/developers/latest/create_a_node_with_python/). The exact test environment is KNIME 5.12.0, native Geospatial Analytics 2.1.0 and project scripting Pandas 2.3.3. Other combinations require their own validation. A future fixed extension may eliminate the need for this local source override, but that was not assumed or tested.

License and provenance: the copied source includes its original `LICENSE.TXT`, `knime.yml`, source files and required icons. The project does not claim authorship of the extension. `repair_workflow.py` does not create or install a replacement node. Original Road Network Distance Matrix #4 remains a genuine geospatial node with its original identity, ports and workflow connections.
