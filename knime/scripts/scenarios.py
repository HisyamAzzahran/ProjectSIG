"""KNIME Script #29: validate native baseline, then run and export experiments."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
import knime.scripting.io as knio

project = Path(knio.flow_variables['case10_project_root'])
sys.path.insert(0, str(project))
from src.main import run
from src.data_loader import load_data

native = knio.input_tables[0].to_pandas()
od = knio.input_tables[1].to_pandas()
for column in ['Origin ID','Destination ID']:
    od[column] = od[column].astype('int64')
od['Duration'] = od['Duration'].astype('float64')
if len(native) != 136 or len(od) != 18496:
    raise ValueError('Native baseline has incomplete zone or OD coverage')
# Validate one complete native baseline before any scenario calculation.
from src.distance_matrix import model_cost
from src.garin_lowry_model import equilibrium
_, points, _ = load_data(project)
ids = points.zone_id.to_numpy()
native_duration = od.pivot(index='Origin ID',columns='Destination ID',values='Duration').loc[ids,ids].to_numpy()
population, services, _, _ = equilibrium(model_cost(native_duration,points.PERIMETER),points.BEMP_Unif)
# Appender keeps legacy column labels: service = 0, population = 0 (#1).
if not {'0','0 (#1)','TRACT0_ID'}.issubset(native.columns):
    raise ValueError(f'Unexpected native Appender schema: {list(native.columns)}')
population_error = float(np.max(abs(native['0 (#1)'].to_numpy()-population)))
service_error = float(np.max(abs(native['0'].to_numpy()-services)))
if max(population_error,service_error) > 1e-8:
    raise ValueError(f'Native baseline differs from independent solve: P={population_error}, S={service_error}')
results, summary = run(project, plots=True)
evidence = dict(native_baseline_verified=True,rows=len(native),od_pairs=len(od),
                population_max_error=population_error,service_max_error=service_error)
(project/'outputs/logs/native_baseline_validation.json').write_text(json.dumps(evidence,indent=2),encoding='utf8')
frame = pd.concat(results.values(),ignore_index=True)
knio.output_tables[0] = knio.Table.from_pandas(frame)
print(json.dumps(evidence))
print(summary[['scenario','population_total','service_total']].to_string(index=False))
