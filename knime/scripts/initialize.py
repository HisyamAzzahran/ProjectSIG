"""KNIME Script #27: resolve workflow-relative input paths as flow variables."""
from pathlib import Path
import sys
import pandas as pd
import knime.scripting.io as knio

project = Path(knio.get_workflow_data_area_dir()) / 'case10_project'
sys.path.insert(0, str(project))
from src.data_loader import load_data, audit

audit(project)
zones, points, roads = load_data(project)
processed = project / 'data/processed'
processed.mkdir(parents=True, exist_ok=True)
# Readers use the original centroid ZIP; do not add columns to that legacy schema.
roads.to_file(processed / 'roads.gpkg', layer='roads', driver='GPKG')
zones.to_file(processed / 'zones.gpkg', layer='zones', driver='GPKG')
knio.flow_variables['case10_points_path'] = str(project / 'original/inputs/trtpt.zip')
knio.flow_variables['case10_roads_path'] = str(processed / 'roads.gpkg')
knio.flow_variables['case10_polygons_path'] = str(processed / 'zones.gpkg')
knio.flow_variables['case10_project_root'] = str(project)
parameters = pd.DataFrame({'parameter':['population_per_worker','service_per_person','residential_exponent','service_exponent'],
                            'value':[2.0,0.3,1.0,1.0]})
knio.output_tables[0] = knio.Table.from_pandas(parameters)
