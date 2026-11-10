"""Structural checks do not claim native KNIME execution."""
import json
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from src.data_loader import ROOT

NS={'k':'http://www.knime.org/2008/09/XMLConfig'}

def native_xml(relative):
    with zipfile.ZipFile(ROOT/'knime/Case10_Garin_Lowry_Final.knwf') as archive:
        root=next(n.rsplit('/',1)[0] for n in archive.namelist() if n.endswith('/workflow.knime'))
        return ET.fromstring(archive.read(root+'/'+relative))
def value(element,key):return element.find(f'k:entry[@key="{key}"]',NS).get('value')


def test_original_nodes_and_connections_preserved():
    original=json.loads((ROOT/'docs/original_workflow_configuration.json').read_text())
    workflow=native_xml('workflow.knime')
    nodes=workflow.find('k:config[@key="nodes"]',NS)
    assert {str(i) for i in range(1,27)}.issubset({value(c,'id') for c in nodes})
    connections=workflow.find('k:config[@key="connections"]',NS)
    fields=['sourceID','sourcePort','destID','destPort']
    actual={tuple(value(c,k) for k in fields) for c in connections}
    expected={tuple(c[k] for k in fields) for c in original['connections'].values()}
    assert expected.issubset(actual)
    for node in nodes:
        native_xml(value(node,'node_settings_file'))


def test_original_equations_and_scripts_preserved():
    originals=json.loads((ROOT/'docs/original_node_configurations.json').read_text())
    for label,original in originals.items():
        xml=native_xml(label+'/settings.xml')
        model=xml.find('k:config[@key="model"]',NS)
        for key in ['expression','script']:
            if key in original['model']:assert value(model,key)==original['model'][key]
