"""Rebind scripting environments in a CLOSED imported workflow after relocation."""
from pathlib import Path
import argparse
import shutil
import xml.etree.ElementTree as ET

NS='http://www.knime.org/2008/09/XMLConfig'
ET.register_namespace('',NS)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workflow',type=Path);p.add_argument('--python',type=Path,required=True);a=p.parse_args()
    folder=a.workflow.resolve();executable=a.python.resolve()
    if not (folder/'workflow.knime').is_file() or not executable.is_file():p.error('Workflow directory or Python executable does not exist')
    count=0
    for settings in folder.glob('*/settings.xml'):
        tree=ET.parse(settings);r=tree.getroot();factory=r.find(f'{{{NS}}}entry[@key="factory"]')
        if factory is None or 'PythonScriptNodeFactory' not in factory.get('value',''):continue
        model=r.find(f'{{{NS}}}config[@key="model"]');field=model.find(f'{{{NS}}}entry[@key="python3_command"]')
        if field is None:field=ET.SubElement(model,f'{{{NS}}}entry',key='python3_command',type='xstring')
        backup=settings.with_name('settings.before_python_rebind.xml')
        if not backup.exists():shutil.copy2(settings,backup)
        field.set('value',str(executable));field.attrib.pop('isnull',None)
        tree.write(settings,encoding='UTF-8',xml_declaration=True);count+=1
    print(f'Configured {count} Python Script nodes. Open the workflow and execute Initialize Project first.')


if __name__=='__main__':main()
