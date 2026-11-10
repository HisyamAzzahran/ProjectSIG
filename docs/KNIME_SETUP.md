# Menjalankan proyek di KNIME pada Windows

Status pemuatan, eksekusi dan ekspor aktual dicatat dalam `VALIDATION_REPORT.md`. Jangan menyamakan keberhasilan tes Python dengan keberhasilan seluruh workflow.

## Persiapan lingkungan

Versi yang ditemukan: KNIME Analytics Platform 5.12.0 dan Geospatial Analytics 2.1.0. Ekstensi lain yang diperlukan: KNIME Python Integration, KNIME Base Nodes, Math Expression/JEP dan JavaScript Views/Plotly. Ekstensi tersebut sudah ditemukan pada laptop ini. Jika dipasang di komputer lain, buka **Menu → Install extensions** atau menu klasik **File → Install KNIME Extensions**, pasang ekstensi yang diperlukan lalu restart.

Di PowerShell, masuk ke direktori proyek:

```powershell
Set-Location 'D:\Project Kuliah\ProjectSIG\SIG\Studi Kasus KNIME\Case10_Garin_Lowry_Project'
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
```

Pada laptop ini `.venv` sudah disiapkan. Gunakan **Pandas 2.3.3** yang dipin pada requirements. Pandas 3.1.1 telah dicoba dan menghasilkan Arrow `large_string` yang ditolak KNIME 5.12. Lingkungan ini berisi NumPy, SciPy, Pandas, GeoPandas, Shapely, NetworkX, Matplotlib, Plotly, PyArrow dan Py4J. Jangan memasang paket pip bernama `knime`; API scripting disediakan oleh aplikasi KNIME.

## Mempertahankan node Road Network asli

Ekstensi Geospatial Analytics 2.1.0 yang terpasang memiliki masalah kompatibilitas Pandas pada `POI.groupby(["kne_idx"])`. Eksekusi GUI benar-benar menghasilkan `KeyError: key of type tuple not found and not a MultiIndex`. Salinan sumber ekstensi berada di `knime/setup/geospatial_compat/`, dengan satu perubahan lokal menjadi `POI.groupby("kne_idx")`. Perubahan mempertahankan pengelompokan yang sama dan mengembalikan key scalar yang diperlukan akses edge. Lisensi asli disertakan dalam direktori salinan. Instalasi KNIME utama dan data asli tidak diubah.

Mulai sesi proyek menggunakan:

```powershell
& '.\.venv\Scripts\python.exe' knime/setup/launch_knime.py
```

Alternatif: `./Launch_Case10.ps1`. Jika lokasi KNIME berbeda, gunakan:

```powershell
& '.\.venv\Scripts\python.exe' knime/setup/launch_knime.py --knime-home 'C:/path/to/KNIME'
```

Launcher meneruskan `-Dknime.python.extension.config=.../geospatial_compat.yml` hanya untuk proses ini. Penggunaan sumber ekstensi lokal dan custom Python executable mengikuti [panduan resmi Python node extensions](https://docs.knime.com/developers/latest/create_a_node_with_python/). Tidak ada penyuntingan permanen pada `knime.ini`. Workspace validasi terletak di `knime/validation_workspace/`; workspace asli pengguna tidak disentuh. Tutup sesi proyek sebelum membuka sesi lain pada workspace yang sama.

## Membuka workflow

1. Pada KNIME modern, pilih **Home → Local space**. Salinan yang digunakan untuk pengujian bernama **Case10_Garin_Lowry**. Klik dua kali untuk membukanya.
2. Untuk workflow hasil ekspor, pilih **Import workflow**, tentukan berkas `.knwf` final yang tercatat dalam `VALIDATION_REPORT.md`, beri nama baru dan konfirmasi impor.
3. Jika menggunakan direktori workflow yang belum dikemas, pada tampilan klasik gunakan **File → Import KNIME Workflow → Select root directory**, pilih direktori yang berisi `workflow.knime`, pilih workflow yang terdeteksi lalu **Finish**. Jangan mengimpor direktori proyek sebagai ZIP arbitrer.
4. Pastikan tersedia 32 node. Seluruh node asli 1–26 dan koneksinya harus terlihat. Enam node tambahan menangani inisialisasi, poligon, skenario, join, filter baseline dan peta.

## Eksekusi bertahap dan pemeriksaan GUI

Setelah impor baru atau pemindahan lokasi, pilih **Reset all** terlebih dahulu. Pada UI klasik: klik area kosong editor, **Ctrl+A → Node → Reset**, lalu konfirmasi. Hal ini membuat initializer mengisi ulang path pada lokasi workflow yang baru, alih-alih menggunakan flow variables yang tersimpan dalam cache ekspor.

1. Jalankan **Initialize Project (#27)** terlebih dahulu. Outputnya adalah tabel empat parameter, dan flow variables `case10_points_path`, `case10_roads_path`, `case10_polygons_path`, `case10_project_root`. Peringatan reader tentang variabel yang belum tersedia sebelum node ini dijalankan dapat hilang setelah inisialisasi.
2. Reader #1 harus mengeluarkan 136 centroid dan reader #2 mengeluarkan 330 jalan. Periksa kolom `speed`=30 dan `speed1`=75 hanya pada `TYPE=r7`.
3. Jalankan **Road Network Distance Matrix (#4)**. Origin dan destination ID harus `ORIG_FID`; ketiga geometry fields adalah `geometry`, road speed adalah `speed`, unit **Miles per hour**. Output harus 18.496 baris dengan `Duration` dalam menit dan `Distance` dalam projected metre.
4. Jalankan sampai **Column Appender (#24)**. Jangan berhenti pada Row Filter #25 yang sengaja menyisakan sepuluh zona transek. #24 harus berisi 136 baris; `0` adalah pekerjaan jasa, `0 (#1)` adalah penduduk.
5. Jalankan **Validate and Run Scenarios (#29)**. Node ini memeriksa hasil #24 dan matriks #7 terhadap solver independen sebelum membuat skenario. Output harus 952 baris (7 × 136). Buka log Python atau berkas `data/case10_project/outputs/logs/native_baseline_validation.json` untuk melihat bukti perbandingan.
6. **Join Scenarios to Geometry (#30)** harus menghasilkan 952 baris bergeometri, dengan join `zone_id` ke `zone_id`. **Select Baseline Map (#31)** harus menghasilkan 136 baris. Jangan melakukan join pada TRACT0_ID.
7. Buka view **Population Geospatial View (#32)**. Tidak ada basemap dunia nyata. Buka **Line Plot (Plotly) (#26)** untuk profil sepuluh zona asli.
8. Untuk menjalankan semuanya, klik **Execute all** pada toolbar modern atau tekan **Shift+F7**. Tunggu hingga seluruh node selesai, simpan dengan **Ctrl+S**.
9. Periksa keluaran di `data/case10_project/outputs/` dalam direktori workflow yang diimpor. Peta interaktif HTML, tujuh GeoPackage, PNG dan tabel perbandingan tersedia di sana. Keluaran yang telah dihitung dari VS Code berada di `outputs/` pada direktori proyek utama.

## Memindahkan ke komputer atau folder lain

Input dan core Python sudah berada dalam data area workflow. Yang perlu disesuaikan adalah lokasi interpreter Python eksternal. Tutup workflow, buat `.venv` di komputer tujuan, kemudian:

```powershell
& '.\.venv\Scripts\python.exe' knime/setup/configure_python.py 'C:/path/to/imported/workflow' --python 'C:/path/to/project/.venv/Scripts/python.exe'
```

Helper membuat backup settings sebelum mengubah `python3_command` pada enam Python Script nodes. Buka ulang workflow, reset dan jalankan #27. Alternatif GUI: buka konfigurasi setiap Python Script node (#18, #20, #21, #22, #27, #29), pilih interpreter `.venv` proyek pada pengaturan environment. Setelah pindah folder, reset #27 dan semua downstream nodes agar flow variables dihitung ulang.

## Ekspor dan validasi ulang

Gunakan **Home → Local space**, menu konteks workflow → **Export**, atau menu klasik **File → Export KNIME Workflow**. Pilih workflow yang telah dijalankan, sertakan data area dan tulis ke `knime/Case10_Garin_Lowry_Final.knwf`. Impor hasil ekspor dengan nama berbeda. Reset dan Execute all untuk membuktikan data tidak bergantung pada cache atau path workflow lama. Simpan bukti log dan status semua node. Ekspor atau pemuatan ulang yang belum dilakukan harus dinyatakan belum terverifikasi.

## Pemecahan masalah

| Gejala | Pemeriksaan / tindakan |
|---|---|
| Missing GeoFile Reader atau Python Script | Pastikan ekstensi terpasang, restart KNIME lalu impor ulang arsip asli; jangan memakai copy yang telah disimpan sebagai MISSING node |
| Error GeoPointCell/GeoLineCell lama | Gunakan workflow repair yang telah di-reset, sehingga data geometri dibaca ulang |
| KeyError tuple pada Road Network | Buka melalui launcher proyek agar sumber kompatibilitas lokal digunakan |
| Arrow large_string | Pastikan Python Script memakai Pandas 2.3.3, bukan Pandas 3 |
| Unknown case10_* path variable | Jalankan #27 terlebih dahulu dan periksa koneksi flow variable ke readers |
| Dua input Python hilang | Periksa konfigurasi port: #18/#20/#21/#22/#29 masing-masing dua input tabel, satu output tabel; pulihkan koneksi sesuai WORKFLOW_EXPLANATION |
| Appender atau solver tidak cocok | Periksa urutan zona numerik 1–136 dan kolom input tanpa ID/string tambahan |
| Batch executor not installed | Ini hambatan otomasi command line, bukan bukti workflow gagal; launcher GUI dan langkah di atas tidak memerlukan Batch Executor |

API adapter mengikuti [KNIME Python Scripting API](https://docs.knime.com/ap/latest/python-script-api/). Data area diakses melalui `knio.get_workflow_data_area_dir()`, yang juga tersedia pada instalasi lokal yang diperiksa.
