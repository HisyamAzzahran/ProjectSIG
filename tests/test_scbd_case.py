"""Real-world study checks: geography, OD coverage and independent economic invariants."""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from src.data_loader import ROOT


def test_scbd_uses_jakarta_geography_and_metric_analysis_cells():
    zones=gpd.read_file(ROOT/'data/scbd_jakarta/analysis_zones.gpkg')
    assert zones.crs.to_epsg()==32748 and len(zones)==81 and zones.zone_id.is_unique
    np.testing.assert_allclose(zones.area,160000,atol=1e-4)
    bounds=zones.to_crs(4326).total_bounds
    assert 106.7<bounds[0]<bounds[2]<106.9 and -6.3<bounds[1]<bounds[3]<-6.1
    roads=gpd.read_file(ROOT/'data/scbd_jakarta/osm_roads.gpkg')
    raw=json.loads((ROOT/'data/scbd_jakarta/raw/osm_network.json').read_text(encoding='utf8'))
    osm_ids={e['id'] for e in raw['elements'] if e['type']=='way'}
    assert set(roads.osm_way_id).issubset(osm_ids) and len(roads)>1000


def test_scbd_network_costs_and_model_balances():
    folder=ROOT/'outputs/scbd_jakarta'
    costs=pd.read_csv(folder/'model_cost_minutes.csv',index_col=0).to_numpy()
    network=pd.read_csv(folder/'network_duration_minutes.csv',index_col=0).to_numpy()
    assert costs.shape==(81,81) and np.isfinite(costs).all() and (costs>0).all()
    assert np.all(costs>=network) and np.allclose(costs,costs.T)
    for scenario in ['merata','scbd_terpusat','tiga_pusat']:
        frame=pd.read_csv(folder/(scenario+'.csv'))
        assert len(frame)==81 and frame.zone_id.is_unique
        np.testing.assert_allclose(frame[['basic_employment','population','service_employment']].sum(),
                                   [1000,5000,1500],atol=1e-7)
    evidence=json.loads((folder/'provenance.json').read_text(encoding='utf8'))
    assert all(d['converged'] and d['residual_inf']<1e-8 for d in evidence['diagnostics'].values())
