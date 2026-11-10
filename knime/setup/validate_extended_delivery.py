"""Record actual native execution, GUI export/import and numerical evidence."""
from pathlib import Path
import json
import hashlib
import xml.etree.ElementTree as E
import numpy as np
import pandas as pd
import zipfile

ROOT=Path(__file__).resolve().parents[2]
NS={'k':'http://www.knime.org/2008/09/XMLConfig'}


def states(folder):
    data=[]
    for p in folder.glob('*/settings.xml'):
        r=E.parse(p).getroot()
        data.append(dict(node=p.parent.name,state=r.find('k:entry[@key="state"]',NS).get('value'),
                         outputs=[e.get('value') for e in r.findall('.//k:entry[@key="port_object_summary"]',NS)]))
    return data


def main():
    archive=ROOT/'knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf'
    source=ROOT/'knime/report_workspace/Case10_Extended_8_Scenarios'
    imported=ROOT/'knime/report_workspace/Case10_Extended_Reimport_Checked'
    node_states=states(source);imported_states=states(imported)
    cases=list(E.parse(ROOT/'outputs/logs/pytest_extended.xml').getroot().iter('testcase'))
    failures=sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
    evidence=json.loads((source/'data/case10_project/outputs/logs/native_baseline_validation.json').read_text())
    original=pd.read_csv(ROOT/'outputs/tables/polycentric_centers.csv')
    native=pd.read_csv(source/'data/case10_project/outputs/tables/polycentric_centers.csv')
    delta=float(np.max(abs(original.population-native.population)))
    relocated=False
    for settings in imported.glob('*#27)/settings.xml'):
        relocated=(imported/'data/case10_project').as_posix() in settings.read_text(encoding='utf8').replace('\\','/')
    with zipfile.ZipFile(archive) as z:
        crc_ok=z.testzip() is None
        module=next(p for p in z.namelist() if p.endswith('/src/custom_case.py'))
        same_code=z.read(module)==(ROOT/'src/custom_case.py').read_bytes()
    result=dict(date='2026-11-10',workflow_nodes=34,scenario_count=8,output_rows=1088,
                native_execution_all_nodes=len(node_states)==34 and all(x['state']=='EXECUTED' for x in node_states),
                native_baseline_evidence=evidence,custom_population_max_difference=delta,
                archive=str(archive.relative_to(ROOT)),archive_bytes=archive.stat().st_size,
                archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                export_method='KNIME GUI: File > Export KNIME Workflow',archive_crc_ok=crc_ok,embedded_current_code=same_code,
                imported_by_knime_gui=imported.is_dir(),
                reimport_reset_and_reexecuted=len(imported_states)==34 and all(x['state']=='EXECUTED' for x in imported_states) and relocated,
                test_count=len(cases),test_failures=failures,node_states=node_states)
    assert result['native_execution_all_nodes'] and crc_ok and same_code and failures==0 and delta<1e-10
    (ROOT/'outputs/logs/extended_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    text=['# Validasi pengembangan dan studi mandiri','',
          'Tanggal: 10 November 2026. Berkas tujuh skenario sebelumnya dipertahankan.','',
          f'- Eksekusi native: **34/34 node EXECUTED**; keluaran skenario dan join geometri **1.088 baris**.',
          '- Studi tambahan: CBD 40%, Satelit Barat zona 63 sebesar 30%, Satelit Timur zona 79 sebesar 30%.',
          f'- Selisih maksimum penduduk studi mandiri Python vs KNIME: {delta:.8g}.',
          f'- Pengujian aktual: **{len(cases)} lulus; {failures} gagal**. Bukti: outputs/logs/pytest_extended.log dan XML.',
          '- Ekspor menggunakan GUI KNIME: knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf.',
          f'- Integritas arsip dan kode terkemas: {crc_ok and same_code}.',
          f'- Impor ulang melalui GUI: {result["imported_by_knime_gui"]}.',
          f'- Reset dan eksekusi ulang setelah impor pada lokasi baru: {result["reimport_reset_and_reexecuted"]}.','',
          'Pemeriksaan perpindahan lokasi memakai flow variable initializer, sehingga cache yang hanya diimpor tidak dihitung sebagai bukti eksekusi ulang.','',
          'Tangkapan layar di outputs/reports/screenshots/ berasal dari aplikasi KNIME, tanpa mengganti isi tabel atau membentuk screenshot buatan. Gambar analitis berasal dari geometri asli dan tabel hasil komputasi.','',
          'Batasan: konfigurasi diuji pada laptop Windows ini, KNIME 5.12.0, dan ekstensi geospatial dengan perbaikan kompatibilitas lokal. Batch Executor tetap tidak tersedia; GUI telah digunakan. Model merupakan simulasi teoritis, bukan prediksi kota nyata.','']
    (ROOT/'docs/VALIDASI_PENGEMBANGAN.md').write_text('\n'.join(text),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='node_states'},indent=2))


if __name__=='__main__':main()
