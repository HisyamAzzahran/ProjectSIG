"""Policy controls and real native artifacts for the additional study."""
import json
import zipfile
import xml.etree.ElementTree as E
import numpy as np
import pandas as pd
from src.data_loader import ROOT,load_data
from src.custom_case import design_employment
from src.garin_lowry_model import equilibrium


def test_custom_policy_conserves_original_employment_and_uses_existing_zones():
    _,p,_=load_data();b,centers=design_employment(p)
    assert {c['zone_id'] for c in centers}=={71,63,79}
    assert np.count_nonzero(b)==3
    np.testing.assert_allclose(b.sum(),p.BEMP_Unif.sum(),rtol=1e-14)
    np.testing.assert_allclose([c['basic_employment']/b.sum() for c in centers],[.4,.3,.3])
    assert set(c['zone_id'] for c in centers).issubset(set(p.zone_id))


def test_custom_equilibrium_is_reproducible_and_uses_unchanged_network_cost():
    frame=pd.read_csv(ROOT/'outputs/tables/polycentric_centers.csv')
    cost=pd.read_csv(ROOT/'data/matrices/model_cost_matrix.csv',index_col=0).to_numpy()
    p,s,diag,_=equilibrium(cost,frame.basic_employment)
    np.testing.assert_allclose(p,frame.population,atol=1e-12)
    np.testing.assert_allclose(s,frame.service_employment,atol=1e-12)
    assert diag['balance_residual_inf']<1e-10 and diag['converged']
    assert np.isclose(p.sum(),499.99992)


def test_extended_table_has_unique_scenario_zone_pairs_and_conserved_totals():
    frame=pd.read_csv(ROOT/'outputs/tables/all_scenarios_extended.csv')
    assert len(frame)==1088 and frame.scenario.nunique()==8
    assert not frame.duplicated(['scenario','zone_id']).any()
    np.testing.assert_allclose(frame.groupby('scenario').population.sum(),499.99992,atol=1e-8)
    assert frame.groupby('scenario').size().eq(136).all()


def test_extended_native_archive_preserves_original_nodes_and_contains_new_study():
    ns={'k':'http://www.knime.org/2008/09/XMLConfig'}
    with zipfile.ZipFile(ROOT/'knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf') as z:
        assert z.testzip() is None
        path=next(n for n in z.namelist() if n.endswith('/workflow.knime'));prefix=path.rsplit('/',1)[0]
        workflow=E.fromstring(z.read(path));nodes=workflow.find('k:config[@key="nodes"]',ns)
        assert len(nodes)==34
        assert {str(i) for i in range(1,27)}.issubset({n.find('k:entry[@key="id"]',ns).get('value') for n in nodes})
        for node in nodes:
            p=node.find('k:entry[@key="node_settings_file"]',ns).get('value');r=E.fromstring(z.read(prefix+'/'+p))
            assert r.find('k:entry[@key="state"]',ns).get('value')=='EXECUTED'
        assert z.read(prefix+'/data/case10_project/src/custom_case.py')==(ROOT/'src/custom_case.py').read_bytes()
        evidence=json.loads(z.read(prefix+'/data/case10_project/outputs/logs/native_baseline_validation.json'))
        assert evidence['scenario_count']==8 and evidence['output_rows']==1088
