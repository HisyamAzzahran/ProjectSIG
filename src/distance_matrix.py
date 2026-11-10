"""Export measured OD and preserve the original perimeter-based model cost."""
import numpy as np
import pandas as pd
from .network_analysis import build_graph, shortest_paths


def model_cost(duration, perimeter):
    p = np.asarray(perimeter, dtype=float)
    # Original Math Formula #7; preserve legacy perimeter scaling for baseline.
    return duration + (p[:, None]+p[None, :])*0.25*1000.0/804.67


def calculate_od(roads, points, speed_column='speed'):
    graph, nodes, snaps, diagnostics = build_graph(roads, points, speed_column)
    distance, duration = shortest_paths(graph, nodes)
    return distance, duration, model_cost(duration, points.PERIMETER), snaps, diagnostics


def export_od(folder, ids, distance, duration, cost, snaps):
    folder.mkdir(parents=True,exist_ok=True)
    for name, values in [('od_distance_matrix',distance),('od_duration_matrix',duration),('model_cost_matrix',cost)]:
        pd.DataFrame(values,index=pd.Index(ids,name='zone_id'),columns=ids).to_csv(folder/f'{name}.csv')
    n = len(ids)
    long = pd.DataFrame({'Origin ID':np.repeat(ids,n),'Destination ID':np.tile(ids,n),
                         'Duration':duration.ravel(),'Distance':distance.ravel(),
                         'Origin snap distance':np.repeat(snaps,n),'Destination snap distance':np.tile(snaps,n),
                         'netwkTime':cost.ravel()})
    long.to_csv(folder/'od_distance_long.csv',index=False)
    return long
