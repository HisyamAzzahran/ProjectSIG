"""Extend the real, previously GUI-exported workflow while preserving the original."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as E
import copy
import shutil

ROOT=Path(__file__).resolve().parents[2]
NS='http://www.knime.org/2008/09/XMLConfig'
E.register_namespace('',NS)
def tag(s):return '{'+NS+'}'+s
def cfg(parent,key):
    c=parent.find(f'{tag("config")}[@key="{key}"]')
    return c if c is not None else E.SubElement(parent,tag('config'),key=key)
def set_entry(parent,key,value,kind='xstring'):
    e=parent.find(f'{tag("entry")}[@key="{key}"]')
    if e is None:e=E.SubElement(parent,tag('entry'),key=key)
    e.attrib.update(value=str(value),type=kind);e.attrib.pop('isnull',None)
def reset(settings):
    set_entry(settings,'state','IDLE');set_entry(settings,'hasContent','false','xboolean')
    for key in ['ports','filestores']:
        c=settings.find(f'{tag("config")}[@key="{key}"]')
        if c is not None:settings.remove(c)
        cfg(settings,key)
    for key in ['file_store_location','file_store_id']:
        set_entry(cfg(settings,'filestores'),key,'')
        cfg(settings,'filestores').find(f'{tag("entry")}[@key="{key}"]').set('isnull','true')
def write(path,root):
    path.parent.mkdir(parents=True,exist_ok=True);E.indent(root,space='    ')
    E.ElementTree(root).write(path,encoding='UTF-8',xml_declaration=True)


def main():
    destination=ROOT/'knime/report_workspace/Case10_Extended_8_Scenarios'
    if destination.exists():raise SystemExit('Prepared workflow already exists; do not overwrite a live workflow')
    archive=ROOT/'knime/Case10_Garin_Lowry_Final.knwf'
    with zipfile.ZipFile(archive) as z:
        prefix=next(n for n in z.namelist() if n.endswith('/workflow.knime')).rsplit('/',1)[0]
        for item in z.infolist():
            relative=Path(item.filename).relative_to(prefix)
            target=(destination/relative).resolve()
            if not target.is_relative_to(destination.resolve()):raise ValueError(item.filename)
            if item.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
    embedded=destination/'data/case10_project'
    shutil.copy2(ROOT/'src/custom_case.py',embedded/'src/custom_case.py')
    workflow=E.parse(destination/'workflow.knime').getroot();nodes=cfg(workflow,'nodes');connections=cfg(workflow,'connections')
    byid={int(c.find(f'{tag("entry")}[@key="id"]').get('value')):c for c in nodes}
    paths={i:destination/n.find(f'{tag("entry")}[@key="node_settings_file"]').get('value') for i,n in byid.items()}
    scenario=E.parse(paths[29]).getroot();model=cfg(scenario,'model')
    original_script=model.find(f'{tag("entry")}[@key="script"]').get('value').replace('%%00010','\n').replace('%%00013','\r')
    script=original_script.replace('from src.main import run','from src.main import run\nfrom src.custom_case import run_custom_case')
    script=script.replace('results, summary = run(project, plots=True)','results, summary = run(project, plots=True)\ncustom, summary, custom_effects = run_custom_case(project, plots=True)')
    script=script.replace('service_max_error=service_error)','service_max_error=service_error, scenario_count=8, output_rows=1088, custom_case="polycentric_centers")')
    script=script.replace('frame = pd.concat(results.values(),ignore_index=True)','frame = pd.concat([*results.values(),custom],ignore_index=True)')
    (ROOT/'knime/scripts/scenarios_extended.py').write_text(script,encoding='utf8')
    set_entry(model,'script',script.replace('\n','%%00010'))
    set_entry(cfg(scenario,'nodeAnnotation'),'text','Validate baseline + 8 scenarios')
    reset(scenario);write(paths[29],scenario)
    def add_node(ident,label,settings,x,y):
        node=copy.deepcopy(byid[31 if ident==33 else 32]);node.set('key',f'node_{ident}')
        set_entry(node,'id',ident,'xint');relative=f'{label} (#{ident})/settings.xml'
        set_entry(node,'node_settings_file',relative)
        b=cfg(cfg(node,'ui_settings'),'extrainfo.node.bounds')
        for k,v in enumerate([x,y,120,80]):set_entry(b,str(k),v,'xint')
        nodes.append(node);reset(settings);set_entry(cfg(settings,'nodeAnnotation'),'text',label)
        write(destination/relative,settings)
    filtered=E.parse(paths[31]).getroot()
    set_entry(cfg(cfg(filtered,'model'),'rowFilter'),'Pattern','polycentric_centers')
    add_node(33,'Custom Case - Three Centers',filtered,1380,1190)
    view=E.parse(paths[32]).getroot()
    add_node(34,'Custom Population Map',view,1640,1190)
    for source,dest in [(30,33),(33,34)]:
        c=copy.deepcopy(next(iter(connections)));c.set('key',f'connection_{len(connections)}')
        for key,v in [('sourceID',source),('destID',dest),('sourcePort',1),('destPort',1)]:set_entry(c,key,v,'xint')
        connections.append(c)
    annotations=cfg(workflow,'annotations');a=copy.deepcopy(list(annotations)[-1]);a.set('key',f'annotation_{len(annotations)}')
    for k,v,kind in [('text','Custom study: CBD 40% + West 30% + East 30%','xstring'),('x-coordinate',1250,'xint'),('y-coordinate',1120,'xint'),('width',570,'xint'),('height',230,'xint')]:set_entry(a,k,v,kind)
    annotations.append(a);write(destination/'workflow.knime',workflow)
    print(f'Prepared {len(nodes)} nodes and {len(connections)} connections at {destination}')
    print('Status: awaits real KNIME load, execution and native export')


if __name__=='__main__':main()
