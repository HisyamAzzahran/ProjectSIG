"""Package reports/results for reading and review; this ZIP is not a KNIME archive."""
from pathlib import Path
import json
import zipfile
import hashlib

ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'outputs/reports';archive=out/'Paket_Laporan_dan_Hasil_Garin_Lowry.zip';entries=[]
    for p in sorted(out.glob('*.docx')):entries.append((p,'Laporan/'+p.name))
    for p in sorted(out.glob('*.pdf')):entries.append((p,'Laporan/'+p.name))
    for p in sorted((ROOT/'outputs/tables').glob('*.csv')):entries.append((p,'Tabel_Hasil/'+p.name))
    for p in sorted((out/'figures').glob('*.png')):entries.append((p,'Gambar_Analisis/'+p.name))
    for p in sorted((out/'screenshots').glob('*.png')):entries.append((p,'Screenshot_KNIME/'+p.name))
    for p in [out/'screenshots/CAPTURE_PROVENANCE.json',out/'word_render_manifest.json']:
        entries.append((p,'Validasi_dan_Petunjuk/'+p.name))
    for p in sorted((ROOT/'outputs/maps').glob('*.gpkg')):entries.append((p,'Data_GIS/'+p.name))
    for p in [out/'REPORT_QA.json',ROOT/'outputs/logs/extended_validation.json',ROOT/'outputs/logs/pytest_extended.log',ROOT/'docs/VALIDASI_PENGEMBANGAN.md',ROOT/'docs/PETUNJUK_LAPORAN_DAN_STUDI_MANDIRI.md']:
        entries.append((p,'Validasi_dan_Petunjuk/'+p.name))
    readme=('PAKET LAPORAN DAN HASIL GARIN–LOWRY\n\n'
            'Mulai dari Laporan/Laporan_Garin_Lowry_KNIME_dan_Studi_Mandiri.pdf.\n'
            'Versi DOCX dapat disunting; PDF mempertahankan layout hasil render Microsoft Word.\n'
            'Tersedia laporan studi mandiri dan panduan penjelasan mudah.\n\n'
            'Hasil proyek: 8 skenario, 34 node KNIME, 1.088 pasangan skenario–zona; 29 tes lulus.\n'
            'Skenario baru: CBD 40%, satelit zona 63 dan 79 masing-masing 30%.\n'
            'Screenshot_KNIME berisi tangkapan layar aplikasi asli, tanpa mengganti isi output.\n\n'
            'ZIP ini adalah paket dokumen dan hasil untuk dibaca, bukan pengganti workflow KNIME.\n'
            'Workflow native yang diekspor dan diuji tersedia terpisah pada proyek: \n'
            'knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf\n'
            'Gunakan launcher dan pengaturan environment proyek untuk eksekusi.\n')
    manifest=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('BACA_DAHULU.txt',readme)
        for path,name in entries:
            z.write(path,name);manifest.append(dict(file=name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(f'Created {archive.name}: {len(entries)} artifacts, {archive.stat().st_size} bytes')


if __name__=='__main__':main()
