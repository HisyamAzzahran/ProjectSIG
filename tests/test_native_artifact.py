"""Checks against the real KNIME GUI export and recorded native evidence."""
import json
import zipfile
import xml.etree.ElementTree as ET
from src.data_loader import ROOT

NS={'k':'http://www.knime.org/2008/09/XMLConfig'}


def test_gui_export_contains_executed_native_workflow_and_inputs():
    archive=ROOT/'knime/Case10_Garin_Lowry_Final.knwf'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        name=next(n for n in z.namelist() if n.endswith('/workflow.knime'))
        prefix=name.rsplit('/',1)[0]
        workflow=ET.fromstring(z.read(name))
        assert workflow.find('k:entry[@key="created_by"]',NS).get('value').startswith('5.12')
        nodes=workflow.find('k:config[@key="nodes"]',NS)
        assert len(nodes)==32
        for node in nodes:
            relative=node.find('k:entry[@key="node_settings_file"]',NS).get('value')
            settings=ET.fromstring(z.read(prefix+'/'+relative))
            assert settings.find('k:entry[@key="state"]',NS).get('value')=='EXECUTED'
        for filename in ['tract.zip','trtpt.zip','road.zip']:
            assert z.read(prefix+'/data/case10_project/original/inputs/'+filename)==(ROOT/'original/inputs'/filename).read_bytes()
        assert z.read(prefix+'/data/case10_project/src/data_loader.py')==(ROOT/'src/data_loader.py').read_bytes()


def test_native_baseline_and_full_city_output_evidence():
    native=ROOT/'knime/validation_workspace/Case10_Garin_Lowry/data/case10_project/outputs/logs/native_baseline_validation.json'
    if native.is_file():
        evidence=json.loads(native.read_text())
    else:
        # A clean clone carries the genuine native export, without duplicate KNIME caches.
        with zipfile.ZipFile(ROOT/'knime/Case10_Garin_Lowry_Final.knwf') as archive:
            member=next(n for n in archive.namelist() if n.endswith('/outputs/logs/native_baseline_validation.json'))
            evidence=json.loads(archive.read(member))
    assert evidence['native_baseline_verified'] and evidence['rows']==136 and evidence['od_pairs']==18496
    assert evidence['population_max_error']<1e-10 and evidence['service_max_error']<1e-10
    states=json.loads((ROOT/'outputs/logs/native_node_states.json').read_text())
    assert len(states)==32 and all(r['state']=='EXECUTED' for r in states)
