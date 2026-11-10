"""Derive an unpacked KNIME workflow from the original, never an arbitrary ZIP.

The output directory must be loaded, executed and saved in KNIME before export.
Original node IDs, connections and mathematical settings are preserved.
"""
from pathlib import Path
import copy
import json
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
NS='http://www.knime.org/2008/09/XMLConfig'
ET.register_namespace('',NS)
def tag(n):return '{'+NS+'}'+n
def config(parent,key):
    found=parent.find(f'{tag("config")}[@key="{key}"]')
    return found if found is not None else ET.SubElement(parent,tag('config'),key=key)
def entry(parent,key,value,kind='xstring'):
    found=parent.find(f'{tag("entry")}[@key="{key}"]')
    if found is None:found=ET.SubElement(parent,tag('entry'),key=key)
    found.attrib.update(type=kind,value=str(value));found.attrib.pop('isnull',None)
    return found
def strings(parent,key,values):
    c=config(parent,key);c.clear();c.set('key',key);entry(c,'array-size',len(values),'xint')
    for i,value in enumerate(values):entry(c,str(i),value)
def reset(node):
    entry(node,'state','IDLE');entry(node,'hasContent','false','xboolean')
    for key in ['ports','filestores']:
        old=node.find(f'{tag("config")}[@key="{key}"]')
        if old is not None:node.remove(old)
    config(node,'ports');config(node,'filestores')
def script_node(template,script,inputs):
    node=copy.deepcopy(template);reset(node)
    entry(config(node,'model'),'script',script.replace('\n','%%00010'))
    # This explicit command is an environment dependency, never an input path.
    entry(config(node,'model'),'python3_command',str(ROOT/'.venv/Scripts/python.exe'))
    creation=config(node,'node_creation_config')
    for child in list(creation):creation.remove(child)
    for label in ['Input object (pickled)','Input table','Output table','Output image','Output object (pickled)']:
        group=config(creation,label)
        count=inputs if label=='Input table' else 1 if label=='Output table' else 0
        for i in range(count):entry(config(group,f'port_{i}'),'object_class','org.knime.core.node.BufferedDataTable')
    return node
def bind(node,key,variable):
    variables=config(node,'variables');entry(variables,'version','V_2019_09_13')
    mapping=config(config(variables,'tree'),key);entry(mapping,'used_variable',variable)
    e=entry(mapping,'exposed_variable','');e.set('isnull','true')
def write(path,tree):
    path.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(tree,space='    ');ET.ElementTree(tree).write(path,encoding='UTF-8',xml_declaration=True)


def main():
    destination=(ROOT/'knime/workflow').resolve()
    assert destination.is_relative_to(ROOT.resolve()) and destination.name=='workflow'
    if destination.exists():shutil.rmtree(destination)
    destination.mkdir(parents=True)
    archive=next((ROOT/'original').glob('Case10*.knwf'))
    with zipfile.ZipFile(archive) as z:
        prefix=next(n for n in z.namelist() if n.endswith('/workflow.knime')).rsplit('/',1)[0]
        workflow=ET.fromstring(z.read(prefix+'/workflow.knime'))
        node_files={}
        for n in z.namelist():
            if n.endswith('/settings.xml'):
                node=ET.fromstring(z.read(n));reset(node)
                relative=n[len(prefix)+1:];ident=int(relative.split('#')[-1].split(')')[0])
                node_files[ident]=(relative,node)
        for name in ['workflow-metadata.xml','workflowset.meta']:
            member=prefix+'/'+name
            if member in z.namelist():(destination/name).write_bytes(z.read(member))
    entry(workflow,'state','IDLE')
    changes=[]
    for ident,(relative,node) in node_files.items():
        if ident in [18,20,21,22]:
            entry(config(node,'model'),'python3_command',str(ROOT/'.venv/Scripts/python.exe'))
        if ident in [1,2]:
            variable='case10_points_path' if ident==1 else 'case10_roads_path'
            bind(node,'data_url',variable)
            entry(config(node,'model'),'data_url','Configured by Initialize Project (#27)')
        if ident==3:
            entry(config(config(node,'model'),'basemap_setting'),'base_map',"Don't show base map")
        write(destination/relative,node)
    nodes=config(workflow,'nodes');connections=config(workflow,'connections')
    def add_node(ident,label,node,x,y):
        relative=f'{label} (#{ident})/settings.xml';write(destination/relative,node)
        item=config(nodes,f'node_{ident}');entry(item,'id',ident,'xint');entry(item,'node_settings_file',relative)
        entry(item,'node_is_meta','false','xboolean');entry(item,'node_type','NativeNode')
        entry(item,'ui_classname','org.knime.core.node.workflow.NodeUIInformation')
        bounds=config(config(item,'ui_settings'),'extrainfo.node.bounds');entry(bounds,'array-size',4,'xint')
        for k,v in enumerate([x,y,110,80]):entry(bounds,str(k),v,'xint')
    def connect(source,dest,source_port=1,dest_port=1):
        c=config(connections,f'connection_{len(connections)}')
        for k,v in [('sourceID',source),('destID',dest),('sourcePort',source_port),('destPort',dest_port)]:entry(c,k,v,'xint')
        entry(c,'ui_classname','org.knime.core.node.workflow.ConnectionUIInformation')
        entry(config(c,'ui_settings'),'extrainfo.conn.bendpoints_size',0,'xint')
    template=node_files[18][1]
    add_node(27,'Initialize Project',script_node(template,(ROOT/'knime/scripts/initialize.py').read_text(),0),40,260)
    connect(27,1,0,0);connect(27,2,0,0)
    polygon=copy.deepcopy(node_files[1][1]);bind(polygon,'data_url','case10_polygons_path')
    add_node(28,'Read Zone Polygons',polygon,50,975);connect(27,28,0,0)
    add_node(29,'Validate and Run Scenarios',script_node(template,(ROOT/'knime/scripts/scenarios.py').read_text(),2),1100,740)
    connect(24,29,1,1);connect(7,29,1,2)
    joiner=copy.deepcopy(node_files[5][1]);model=config(joiner,'model')
    strings(model,'leftTableJoinPredicate',['zone_id']);strings(model,'rightTableJoinPredicate',['zone_id'])
    # Correct legacy spelling is lower-case leftTable... (copied from original).
    left_columns=['zone_id','geometry'];right_columns=['scenario','basic_employment','population','service_employment','total_employment','population_change','service_change','population_change_pct','ring','radius_m']
    for key,columns in [('leftColumnSelectionConfig',left_columns),('rightColumnSelectionConfig',right_columns)]:
        f=config(model,key);entry(f,'filter-type','STANDARD');strings(f,'included_names',columns);strings(f,'excluded_names',[]);entry(f,'enforce_option','EnforceInclusion')
    add_node(30,'Join Scenarios to Geometry',joiner,1310,975)
    connect(28,30,1,1);connect(29,30,1,2)
    filtered=copy.deepcopy(node_files[25][1]);m=config(filtered,'model');old=m.find(f'{tag("config")}[@key="rowFilter"]');m.remove(old)
    filt=config(m,'rowFilter');entry(filt,'RowFilter_TypeID','StringComp_RowFilter');entry(filt,'ColumnName','scenario');entry(filt,'include','true','xboolean');entry(filt,'deepFiltering','false','xboolean')
    entry(filt,'Pattern','baseline_uniform');entry(filt,'CaseSensitive','true','xboolean');entry(filt,'hasWildCards','false','xboolean');entry(filt,'isRegExpr','false','xboolean')
    add_node(31,'Select Baseline Map',filtered,1480,975);connect(30,31)
    view=copy.deepcopy(node_files[3][1]);entry(config(config(view,'model'),'color_settings'),'color_col','population')
    entry(config(config(view,'model'),'basemap_setting'),'base_map',"Don't show base map")
    add_node(32,'Population Geospatial View',view,1640,975);connect(31,32)
    annotation=copy.deepcopy(list(config(workflow,'annotations'))[0]);annotation.set('key','annotation_2')
    for key,value,kind in [('text','Extended project: preserve native baseline -> validate -> seven scenarios -> geometry join -> exports','xstring'),('x-coordinate',1020,'xint'),('y-coordinate',680,'xint'),('width',760,'xint'),('height',430,'xint')]:entry(annotation,key,value,kind)
    config(workflow,'annotations').append(annotation)
    write(destination/'workflow.knime',workflow)
    project=destination/'data/case10_project';project.mkdir(parents=True)
    shutil.copytree(ROOT/'original',project/'original')
    shutil.copytree(ROOT/'src',project/'src',ignore=shutil.ignore_patterns('__pycache__'))
    for d in ['docs','data/processed','data/matrices','data/scenarios','outputs/maps','outputs/charts','outputs/tables','outputs/logs']:(project/d).mkdir(parents=True,exist_ok=True)
    print(f'Prepared {len(nodes)} nodes and {len(connections)} connections at {destination}')
    print('Status: UNVERIFIED until loaded, executed and saved by KNIME. No final archive created.')

if __name__=='__main__':main()
