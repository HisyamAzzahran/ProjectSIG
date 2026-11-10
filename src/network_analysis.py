"""Road polyline graph with continuous nearest-edge projection, not Euclidean OD."""
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

MPH_TO_METRES_PER_MINUTE = 26.8224


def build_graph(roads, points, speed_column='speed'):
    speeds = roads[speed_column].to_numpy(dtype=float)
    if not np.isfinite(speeds).all() or (speeds <= 0).any():
        raise ValueError('Road speeds must be positive mph')
    splits = {i: [0.0, line.length] for i, line in enumerate(roads.geometry)}
    projections, snaps = [], []
    for point in points.geometry:
        distances = roads.geometry.distance(point).to_numpy()
        i = int(distances.argmin())
        line = roads.geometry.iloc[i]
        position = float(line.project(point))
        projected = line.interpolate(position)
        splits[i].append(position)
        projections.append((round(projected.x, 6), round(projected.y, 6)))
        snaps.append(float(point.distance(projected)))
    graph = nx.Graph()
    for i, line in enumerate(roads.geometry):
        positions = np.unique(np.round(splits[i], 9))
        for start, end in zip(positions[:-1], positions[1:]):
            p, q = line.interpolate(start), line.interpolate(end)
            u, v = (round(p.x, 6), round(p.y, 6)), (round(q.x, 6), round(q.y, 6))
            length = float(end-start)
            if u == v:
                continue
            attrs = dict(length=length, time=length/(speeds[i]*MPH_TO_METRES_PER_MINUTE),
                         road_id=int(roads.ROAD0_.iloc[i]), road_type=str(roads.TYPE.iloc[i]))
            # No parallel-edge ambiguity is allowed in this supplied network.
            if graph.has_edge(u,v):
                if graph[u][v]['time'] > attrs['time']:
                    graph[u][v].update(attrs)
            else:
                graph.add_edge(u, v, **attrs)
    # Match the original KNIME node's connect_graph tolerance: gaps < 0.1 m
    # between separate components are treated as numerical topology gaps.
    before = nx.number_connected_components(graph)
    nodes = list(graph)
    pairs = sorted(cKDTree(np.array(nodes)).query_pairs(0.1))
    bridges = []
    components = {v:i for i,c in enumerate(nx.connected_components(graph)) for v in c}
    for i, j in pairs:
        u, v = nodes[i], nodes[j]
        if components[u] != components[v]:
            graph.add_edge(u,v,length=0.0,time=0.0,road_id=-1,road_type='topology_gap')
            bridges.append(dict(x1=u[0],y1=u[1],x2=v[0],y2=v[1],gap_m=float(np.linalg.norm(np.subtract(u,v)))))
    if not nx.is_connected(graph):
        raise ValueError(f'Road graph remains disconnected: {nx.number_connected_components(graph)} components')
    if not all(p in graph for p in projections):
        raise ValueError('Missing projected zone node')
    metadata = dict(nodes=graph.number_of_nodes(), edges=graph.number_of_edges(),
                    components_before=before, components_after=nx.number_connected_components(graph),
                    topology_bridges=bridges, speed_column=speed_column,
                    max_snap_distance_m=max(snaps), min_snap_distance_m=min(snaps),
                    directed=False, gap_tolerance_m=0.1, node_rounding_m=1e-6)
    return graph, projections, np.array(snaps), metadata


def shortest_paths(graph, nodes):
    matrices = []
    for weight in ['length', 'time']:
        values = np.array([[dist[v] for v in nodes] for dist in
                           (nx.single_source_dijkstra_path_length(graph, u, weight=weight) for u in nodes)])
        if not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values,values.T,atol=1e-8):
            raise ValueError('Invalid undirected shortest-path matrix')
        if not np.allclose(np.diag(values),0):
            raise ValueError('Nonzero network diagonal')
        matrices.append(values)
    return tuple(matrices)
