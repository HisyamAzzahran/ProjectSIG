"""Launch a project-scoped KNIME session with the native network compatibility fix.

Does not edit knime.ini, installed extensions, or the user's existing workspace.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--knime-home',type=Path,default=Path(os.environ.get('LOCALAPPDATA',''))/'Programs/KNIME')
    parser.add_argument('--workspace',type=Path,default=ROOT/'knime/validation_workspace')
    args=parser.parse_args();knime=args.knime_home.resolve();workspace=args.workspace.resolve()
    if not (knime/'knime.ini').is_file():raise SystemExit('KNIME installation not found; pass --knime-home')
    environment=ROOT/'.venv/Scripts/python.exe'
    if not environment.is_file():raise SystemExit('Create the project .venv and install requirements.txt first')
    # Use the installed Geospatial extension's complete runtime; only the source
    # comes from the project-local compatibility copy.
    native_python=knime/'bundling/sdl_harvard_geospatial/.pixi/envs/default/python.exe'
    if not native_python.is_file():raise SystemExit('Install Geospatial Analytics and let KNIME initialize its environment first')
    compatibility=ROOT/'knime/setup/geospatial_compat'
    if not (compatibility/'knime.yml').is_file():raise SystemExit('Project-local geospatial compatibility source is missing')
    yaml=ROOT/'knime/setup/geospatial_compat.yml'
    yaml.write_text('sdl.harvard.geospatial:\n  src: '+json.dumps(compatibility.as_posix())+
                    '\n  python_executable: '+json.dumps(native_python.as_posix())+'\n  debug_mode: true\n',encoding='utf8')
    workspace.mkdir(parents=True,exist_ok=True)
    lines=(knime/'knime.ini').read_text().splitlines();vmargs=lines[lines.index('-vmargs')+1:]
    java=next(knime.glob('plugins/org.knime.binary.jre*/jre/bin/java.exe'))
    launcher=next(knime.glob('plugins/org.eclipse.equinox.launcher_*.jar'))
    command=[str(java),*vmargs,'-Dknime.python.extension.config='+yaml.as_posix(),'-jar',str(launcher),
             '-nosplash','-consoleLog','-application','org.knime.product.KNIME_APPLICATION','-data',str(workspace)]
    logs=ROOT/'outputs/logs';logs.mkdir(parents=True,exist_ok=True)
    with (logs/'knime_session_stdout.log').open('w',encoding='utf8') as out,(logs/'knime_session_stderr.log').open('w',encoding='utf8') as err:
        print(f'Opening KNIME in {workspace}; original installation is unchanged.',flush=True)
        process=subprocess.Popen(command,cwd=knime,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        return process.wait()


if __name__=='__main__':raise SystemExit(main())
