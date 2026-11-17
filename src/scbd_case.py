"""SCBD Jakarta: actual OSM geography with explicitly assumed model employment."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString, box
from .data_loader import ROOT
from .garin_lowry_model import equilibrium, Parameters

CENTER = (106.80966, -6.22651)  # longitude, latitude; SCBD reference point, not a legal boundary
CRS = 32748  # UTM 48S, metres
SPEED_KPH = {'trunk':40,'primary':30,'secondary':30,'tertiary':25,
             'unclassified':20,'residential':20,'living_street':10,'service':15}


def run(root=ROOT):
    root=Path(root); folder=root/'data/scbd_jakarta'; output=root/'outputs/scbd_jakarta'
    output.mkdir(parents=True,exist_ok=True)
    raw=folder/'raw/osm_network.json'; data=json.loads(raw.read_text(encoding='utf8'))
    project=Transformer.from_crs(4326,CRS,always_xy=True)
    nodes={e['id']:project.transform(e['lon'],e['lat']) for e in data['elements'] if e['type']=='node'}
    graph=nx.Graph(); segments=[]
    for way in (e for e in data['elements'] if e['type']=='way'):
        tags=way['tags']; kind=tags['highway']; speed=SPEED_KPH.get(kind.replace('_link',''),20)
        for u,v in zip(way['nodes'][:-1],way['nodes'][1:]):
            if u==v: continue
            line=LineString([nodes[u],nodes[v]]); length=line.length
            if length<=0: continue
            minutes=length/(speed*1000/60)
            if not graph.has_edge(u,v) or minutes<graph[u][v]['minutes']:
                graph.add_edge(u,v,minutes=minutes,length_m=length)
            segments.append({'osm_way_id':way['id'],'osm_u':u,'osm_v':v,'name':tags.get('name',''),
                             'highway':kind,'oneway_original':tags.get('oneway','no'),
                             'assumed_speed_kph':speed,'geometry':line})
    component_count=nx.number_connected_components(graph); original_nodes=len(graph)
    graph=graph.subgraph(max(nx.connected_components(graph),key=len)).copy()
    roads=gpd.GeoDataFrame([s for s in segments if s['osm_u'] in graph and s['osm_v'] in graph],crs=CRS)
    cx,cy=project.transform(*CENTER); cells=[]
    # A 3.6 km x 3.6 km analysis window; grids are NOT administrative or SCBD boundaries.
    for row in range(9):
        for col in range(9):
            x=cx+(col-4)*400; y=cy+(row-4)*400
            cells.append({'zone_id':row*9+col+1,'grid_row':row,'grid_col':col,
                          'geometry':box(x-200,y-200,x+200,y+200)})
    zones=gpd.GeoDataFrame(cells,crs=CRS); centroids=zones.copy();centroids.geometry=zones.centroid
    node_ids=list(graph); node_xy=np.array([nodes[n] for n in node_ids])
    snaps,indices=cKDTree(node_xy).query(np.array([(p.x,p.y) for p in centroids.geometry]))
    targets=[node_ids[i] for i in indices]
    duration=np.array([[dist[t] for t in targets] for dist in
                       (nx.single_source_dijkstra_path_length(graph,s,weight='minutes') for s in targets)])
    # First/last access is assumed walking at 5 km/h. Positive 0.5 min cell-internal cost.
    access=snaps/(5000/60); cost=duration+access[:,None]+access[None,:]+0.5
    assert np.isfinite(cost).all() and (cost>0).all() and np.allclose(cost,cost.T)
    ids=zones.zone_id.to_numpy(); pd.DataFrame(cost,index=ids,columns=ids).rename_axis('zone_id').to_csv(output/'model_cost_minutes.csv')
    pd.DataFrame(duration,index=ids,columns=ids).rename_axis('zone_id').to_csv(output/'network_duration_minutes.csv')
    centroids['snap_distance_m']=snaps; centroids['osm_snap_node']=targets
    employment={}; uniform=np.full(81,1000/81); employment['merata']=uniform
    single=np.full(81,400/80); single[40]=600; employment['scbd_terpusat']=single
    three=np.zeros(81);three[[40,37,43]]=[400,300,300];employment['tiga_pusat']=three
    results={}; diagnostic={};summary=[]
    for name,basic in employment.items():
        pop,service,diag,_=equilibrium(cost,basic,Parameters())
        frame=zones[['zone_id']].copy();frame['scenario']=name;frame['basic_employment']=basic
        frame['population']=pop;frame['service_employment']=service
        frame['population_change']=pop-(results['merata'].population.to_numpy() if results else pop)
        results[name]=frame;diagnostic[name]=diag
        summary.append({'scenario':name,'basic_jobs_assumed':float(basic.sum()),'population_model':float(pop.sum()),
                        'service_jobs_model':float(service.sum()),'scbd_population_model':float(pop[40]),
                        'max_population':float(pop.max()),'iterations':diag['iterations']})
        frame.to_csv(output/(name+'.csv'),index=False)
        joined=zones.merge(frame,on='zone_id');joined.to_file(output/(name+'.gpkg'),layer='zones',driver='GPKG')
    zones.to_file(folder/'analysis_zones.gpkg',layer='zones',driver='GPKG')
    roads.to_file(folder/'osm_roads.gpkg',layer='roads',driver='GPKG')
    centroids.to_file(folder/'centroids.gpkg',layer='centroids',driver='GPKG')
    pd.DataFrame(summary).to_csv(output/'scenario_summary.csv',index=False)
    provenance={'title':'SCBD Jakarta: geografi nyata, ekonomi simulasi','center_lon_lat':CENTER,
                'center_reference':'https://www.wikidata.org/wiki/Q30590531',
                'scbd_profile':'https://www.scbd.com/menu/page/profile','crs_projected':'EPSG:32748',
                'raw_osm_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                'osm_snapshot':data.get('osm3s',{}),'attribution':'© OpenStreetMap contributors, ODbL 1.0',
                'zone_count':81,'cell_size_m':400,'window_size_m':3600,'graph_nodes':len(graph),
                'graph_edges':graph.number_of_edges(),'road_segments':len(roads),'original_components':component_count,
                'discarded_nodes_outside_largest_component':original_nodes-len(graph),
                'max_snap_distance_m':float(max(snaps)),'assumed_speeds_kph':SPEED_KPH,
                'limitations':['Grid analisis buatan, bukan batas administrasi atau batas resmi SCBD.',
                  '1.000 pekerjaan dasar adalah asumsi, bukan data ketenagakerjaan aktual.',
                  'Jaringan disederhanakan dua arah; tidak memodelkan oneway, turn restrictions atau kemacetan.',
                  'Kecepatan berdasarkan asumsi kelas jalan; akses centroid berjalan 5 km/jam, biaya internal 0,5 menit.',
                  'Hasil penduduk dan jasa adalah keluaran model; bukan statistik atau prediksi terkalibrasi.',
                  'Peta dasar online, sedangkan jaringan dan keluaran model menggunakan snapshot tersimpan.'],
                'diagnostics':diagnostic}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False),encoding='utf8')
    payload={'zones':json.loads(zones.to_crs(4326).to_json()),'roads':json.loads(roads.to_crs(4326).to_json()),
             'results':{k:v.to_dict(orient='records') for k,v in results.items()},'summary':summary,'provenance':provenance}
    template=(root/'src/scbd_map.html').read_text(encoding='utf8')
    (output/'SCBD_Jakarta_Live.html').write_text(template.replace('__STUDY_DATA__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
    print(json.dumps({'output':str(output),'zones':81,'roads':len(roads),'graph_nodes':len(graph),'max_snap_m':max(snaps)},indent=2))
    return provenance


if __name__=='__main__':run()
