"""Supplied-data tests: these assert actual GIS and cached workflow agreement."""
import json
import hashlib
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import pytest
from src.data_loader import ROOT,load_data,cached_table,safe_extract
from src.distance_matrix import calculate_od,model_cost
from src.network_analysis import build_graph
from src.garin_lowry_model import equilibrium,Parameters
from src.validation import validate_original,validate_result


@pytest.fixture(scope='module')
def data():return load_data()


@pytest.fixture(scope='module')
def od(data):return calculate_od(data[2],data[1])


def test_geography_counts_and_crs(data):
    z,p,r=data
    assert (len(z),len(p),len(r))==(136,136,330)
    assert all(f.crs.to_epsg()==3857 for f in data)
    assert all(f.is_valid.all() and not f.geometry.is_empty.any() for f in data)


def test_zone_identity_and_spatial_join(data):
    z,p,_=data
    assert z.zone_id.is_unique and p.zone_id.is_unique
    assert np.array_equal(z.zone_id,p.ORIG_FID)
    assert all(poly.covers(pt) for poly,pt in zip(z.geometry,p.geometry))
    assert (p.TRACT0_ID==0).sum()==126
    assert int(p.loc[p.BEMP_CBD.idxmax(),'zone_id'])==71


def test_recovered_road_speed_and_graph(data):
    _,p,r=data
    assert r.speed.eq(30).all()
    assert (r.speed1==75).sum()==20
    assert r.loc[r.TYPE=='r7','speed1'].eq(75).all()
    graph,nodes,snaps,meta=build_graph(r,p)
    assert nx.is_connected(graph) and len(nodes)==136
    assert meta['nodes']==331 and meta['edges']==466
    assert not meta['topology_bridges'] and (snaps>=0).all()


def test_od_dimensions_diagonal_symmetry_and_coverage(od):
    distance,duration,cost,snaps,_=od
    for matrix in [distance,duration,cost]:
        assert matrix.shape==(136,136) and np.isfinite(matrix).all()
        assert (matrix>=0).all() and np.allclose(matrix,matrix.T,atol=1e-8)
    assert np.allclose(np.diag(distance),0)
    assert np.allclose(np.diag(duration),0)
    assert (np.diag(cost)>0).all()


def test_original_workflow_mathematics_and_network_replay(data,od):
    _,p,_=data
    population,service,diag,_=equilibrium(od[2],p.BEMP_Unif)
    report=validate_original(p,od[1],population,service,ROOT)
    assert report['cached_baseline_population_max_error']<1e-10
    assert report['rebuilt_network_duration_max_error_min']<1e-5
    assert report['rebuilt_population_vs_original_max_error']<1e-6
    assert diag['residual_inf']<1e-10


def test_network_scenario_is_recalculated_and_no_cost_increases(data,od):
    _,p,r=data
    d,t,c,_,_=calculate_od(r,p,'speed1')
    np.testing.assert_allclose(d,od[0],atol=1e-6)
    assert (t<=od[1]+1e-9).all() and (t<od[1]-1e-4).any()
    assert c.mean()<od[2].mean()


def test_deterministic_baseline(data,od):
    a=equilibrium(od[2],data[1].BEMP_Unif)
    b=equilibrium(od[2],data[1].BEMP_Unif)
    np.testing.assert_array_equal(a[0],b[0]);assert a[3]==b[3]


def test_export_schema_conservation_and_complete_gis_joins():
    summary=pd.read_csv(ROOT/'outputs/tables/scenario_comparison.csv')
    assert len(summary)==7
    for name in summary.scenario:
        frame=pd.read_csv(ROOT/'outputs/tables'/f'{name}.csv')
        params=json.loads((ROOT/'data/scenarios'/name/'parameters.json').read_text())
        validate_result(frame,Parameters(**params['parameters']))
        geometry=gpd.read_file(ROOT/'outputs/maps'/f'{name}.gpkg')
        assert len(geometry)==136 and geometry.zone_id.is_unique
        assert geometry.population.notna().all()


def test_original_inputs_unchanged():
    workspace=ROOT.parent
    original=next((ROOT/'original').glob('Case10*.knwf'))
    manifest=json.loads((ROOT/'docs/original_inputs_sha256.json').read_text())
    for relative,expected in manifest.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected
    # Compare the separately supplied originals too when running in the initial workspace.
    if (workspace/original.name).is_file():
        assert original.read_bytes()==(workspace/original.name).read_bytes()
    for name in ['tract','trtpt','road']:
        supplied=workspace/'Data/Lousiana'/f'{name}.zip'
        if supplied.is_file():
            assert (ROOT/'original/inputs'/f'{name}.zip').read_bytes()==supplied.read_bytes()


def test_archive_traversal_is_rejected(tmp_path):
    malicious=tmp_path/'bad.zip'
    with zipfile.ZipFile(malicious,'w') as z:z.writestr('../escape.txt','not extracted')
    with pytest.raises(ValueError):safe_extract(malicious,tmp_path/'inside')
    assert not (tmp_path/'escape.txt').exists()
