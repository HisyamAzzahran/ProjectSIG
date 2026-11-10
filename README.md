# Implementing the Garin–Lowry Model in a Hypothetical City

**Pembaruan laporan dan studi mandiri:** tersedia versi **8 skenario / 34 node**, laporan Word dan PDF bergambar, serta panduan penjelasan mudah. Mulai dari [petunjuk laporan dan studi mandiri](docs/PETUNJUK_LAPORAN_DAN_STUDI_MANDIRI.md). Versi extended diekspor melalui KNIME, diimpor ulang, di-reset dan dieksekusi kembali. Bukti tambahan: [validasi pengembangan](docs/VALIDASI_PENGEMBANGAN.md). Uraian tujuh skenario di bawah tetap mendokumentasikan versi awal yang dipertahankan.

Proyek SIG berbasis **workflow KNIME Case 10 asli**, didukung model Python yang diuji, analisis jaringan jalan, tujuh simulasi, peta GIS dan panduan presentasi. File asli, dataset asli, kasus lain serta folder SHP File dan SHP2 dipertahankan.

Mulai dari [status validasi](docs/VALIDATION_REPORT.md) dan [petunjuk KNIME](docs/KNIME_SETUP.md). Status pemuatan, eksekusi dan ekspor KNIME dilaporkan terpisah dari tes Python.

## Hasil utama

- Data nyata yang disuplai: 136 poligon, 136 centroid dan 330 fitur jalan, EPSG:3857.
- Matriks OD jaringan: 136 × 136, termasuk 18.496 pasangan OD; tidak diganti dengan jarak lurus.
- Baseline arsip asli: pekerjaan dasar merata, 99,999984 model jobs; menghasilkan 499,999920 model persons dan 149,999976 service jobs.
- Solver independen menyelesaikan `(I − GT)P = GB`, kemudian `S = TP`, dan dibandingkan dengan iterasi serta hasil asli tersimpan.
- Tujuh skenario mempertahankan total pekerjaan dasar: baseline uniform, pekerjaan CBD, friction 0,5 dan 2, beltway, CBD + friction 2, CBD + beltway.
- Seluruh 26 node dan 34 koneksi asli dipertahankan; enam node tambahan menangani audit/path portabel, skenario, geometri dan peta.

Ini adalah simulasi teoritis kota hipotetis, bukan prediksi penduduk kota nyata. Peta menunjukkan jumlah per zona, bukan kepadatan per km².

## Jalankan di KNIME

Lingkungan Python lokal sudah disiapkan pada laptop ini. Untuk Geospatial Analytics 2.1.0, buka KNIME melalui launcher proyek yang mengaktifkan perbaikan kompatibilitas pada salinan lokal ekstensi:

```powershell
Set-Location 'D:\Project Kuliah\ProjectSIG\SIG\Studi Kasus KNIME\Case10_Garin_Lowry_Project'
& '.\.venv\Scripts\python.exe' knime/setup/launch_knime.py
```

Pilih **Home → Local space → Case10_Garin_Lowry**, kemudian **Execute all**. Setelah mengimpor arsip atau memindahkan workflow, gunakan **Reset all → Execute all** agar initializer menghitung ulang lokasi data. Direktori workflow yang diuji berada di `knime/validation_workspace/Case10_Garin_Lowry/`. Artefak final adalah **`knime/Case10_Garin_Lowry_Final.knwf`**, diekspor oleh KNIME, diimpor ulang, di-reset dan berhasil dieksekusi kembali pada seluruh **32 node**. Bukti dan **25 tes yang lulus** tercatat dalam [VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md). Panduan [KNIME_SETUP.md](docs/KNIME_SETUP.md) menjelaskan konfigurasi dan pemeriksaan setiap tahap serta cara mengimpor pada komputer lain.

Output yang dibuat oleh workflow disimpan dalam **`data/case10_project/outputs/` di direktori workflow tersebut**. Output yang telah dihitung dari VS Code tersedia langsung dalam **`outputs/` pada proyek ini**.

## Reproduksi Python

Diuji menggunakan Python 3.11.9 pada Windows. Dependencies dipin dalam `requirements.txt`; gunakan lingkungan terisolasi:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' -m src.main audit
& '.\.venv\Scripts\python.exe' -m src.main baseline
& '.\.venv\Scripts\python.exe' -m src.main all
& '.\.venv\Scripts\python.exe' -m pytest tests -q
```

`python -m src.main scenarios` juga menjalankan seluruh eksperimen; `--no-plots` melewati regenerasi gambar. `python -m src.main validate` menjalankan tes. Jangan menjalankan skrip adapter KNIME sebagai Python biasa; `knime.scripting.io` disediakan di dalam node KNIME.

## Struktur dan keluaran

| Lokasi | Isi |
|---|---|
| `original/` | Backup workflow dan input asli yang diinspeksi |
| `src/` | Loader, jaringan, matriks OD, model, skenario, visualisasi dan validasi |
| `data/processed/` | Poligon ber-ID unik, centroid dan jalan dengan kecepatan yang dipulihkan |
| `data/matrices/` | Matriks jarak, durasi, model cost dan tabel OD panjang |
| `data/scenarios/` | Parameter, pekerjaan dasar, diagnostik solver dan jaringan beltway |
| `knime/workflow/` | Sumber workflow repair yang diturunkan dari arsip asli |
| `knime/validation_workspace/` | Workspace pengujian KNIME yang terpisah dari workspace pengguna |
| `knime/scripts/` | Adapter inisialisasi dan simulasi KNIME |
| `knime/setup/` | Launcher, helper konfigurasi dan salinan ekstensi kompatibilitas |
| `outputs/maps/` | Tujuh peta PNG, tujuh GeoPackage hasil, peta HTML interaktif |
| `outputs/charts/` | Heatmap OD/model cost, grafik perbandingan, profil dan konvergensi |
| `outputs/tables/` | Hasil 136 zona per skenario, seluruh hasil dan tabel perbandingan |
| `outputs/logs/` | Log Python/KNIME, bukti GUI, hasil pytest dan diagnostik jaringan |
| `tests/` | Tes solusi yang diketahui, data asli, jaringan, skenario dan pelestarian workflow |
| `docs/` | Audit, persamaan, panduan node, analisis, validasi dan presentasi |

Peta interaktif: buka `outputs/maps/interactive_scenarios.html` di browser; tidak memerlukan server atau basemap. Gunakan dropdown untuk memilih skenario dan arahkan pointer pada zona untuk membaca hasilnya. Gambar perbandingan utama adalah `outputs/maps/05_scenario_population.png`; tabel utama adalah `outputs/tables/scenario_comparison.csv`.

## Asal data dan batasan

Sumber geografi ditemukan pada `../Data/Lousiana/`, sedangkan skrip matriks berada pada `../Data/SimuCity/`. Tidak ada data pengganti yang diunduh. Kecepatan yang hilang pada SHP dipulihkan dari tabel reader dalam workflow asli setelah ID dan geometri dibandingkan. Kolom `TRACT0_ID` bukan ID unik; join spasial menggunakan `zone_id`, diturunkan dari `ORIG_FID` centroid.

Workflow asli menggunakan baseline uniform, sedangkan pengantar lab manual menggunakan CBD; dokumentasi membedakan keduanya. Nilai perimeter lama dan geometri memiliki perbedaan skala kecil; formula asli dipertahankan untuk reproduksi. Model tidak memasukkan kapasitas perumahan atau kemacetan endogen. Pemindahan proyek membutuhkan pengaturan ulang interpreter Python dan reset Initialize Project; lihat KNIME_SETUP.

Referensi utama: Liu dan Wang, *Computational Methods and GIS Applications in Social Science — Lab Manual*, Case 10, printed pp. 196–203, [DOI bab](https://doi.org/10.1201/9781003304357-10). PDF disuplai dalam workspace pengguna. Lihat [METHODOLOGY.md](docs/METHODOLOGY.md) untuk persamaan dan asumsi, serta [PRESENTATION_GUIDE.md](docs/PRESENTATION_GUIDE.md) untuk alur penjelasan dalam bahasa Indonesia.


## Repository GitHub

Repository ini memuat proyek Case 10 beserta delapan skenario, kode sumber, data input, dua arsip workflow KNIME hasil ekspor asli, serta laporan Word/PDF dan tangkapan layar KNIME. Mulai dari [workflow extended](knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf) dan [laporan lengkap](outputs/reports/Laporan_Garin_Lowry_KNIME_dan_Studi_Mandiri.pdf).

Folder `.venv`, workspace/cache KNIME, gambar pratinjau pemeriksaan PDF, ZIP laporan duplikat, serta buku dan contoh laporan yang diberikan sebagai referensi tidak disertakan. Buat environment sesuai petunjuk reproduksi, lalu impor `.knwf` melalui KNIME dan sesuaikan interpreter Python sebagaimana panduan. Lokasi workspace dalam dokumentasi menunjukkan lokasi pengujian lokal; workspace tersebut dibuat sendiri setelah impor.

Integritas input asli diperiksa melalui `docs/original_inputs_sha256.json`. Tes bukti baseline dapat membaca langsung arsip KNIME asli sehingga tidak memerlukan salinan workspace pengujian.
