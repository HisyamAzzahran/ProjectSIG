# Laporan Word, hasil observasi, dan studi mandiri

Pembaruan 10 November 2026 menambahkan satu studi kasus di luar tujuh kasus sebelumnya: **kota dengan tiga pusat pekerjaan dasar**. Seluruh data geografis asli dan arsip tujuh skenario dipertahankan.

## Dokumen untuk dibaca

Semua dokumen berada di `outputs/reports/`, dalam format **DOCX yang dapat disunting dan PDF**:

1. `Laporan_Garin_Lowry_KNIME_dan_Studi_Mandiri`: laporan utama, mengikuti contoh layout yang disuplai—pendahuluan, metodologi, hasil dan pembahasan, kesimpulan dan rekomendasi, daftar pustaka, serta lampiran. Ada 18 gambar, termasuk screenshot workflow dan output KNIME.
2. `Studi_Kasus_Mandiri_Kota_Tiga_Pusat`: laporan tersendiri tentang eksperimen CBD 40% dan dua satelit 30%–30%.
3. `Penjelasan_Mudah_Project_Garin_Lowry`: panduan memahami pekerjaan–penduduk–jasa, kegunaan KNIME, cara membaca hasil, dan demonstrasi.

Teks dokumen memakai Times New Roman hitam, ukuran isi 12 pt, judul dan subjudul tebal, tabel/caption yang disesuaikan, halaman A4, daftar isi otomatis pada dua laporan, serta nomor halaman. Screenshot tetap mempertahankan tampilan aplikasi aslinya; gambar hasil analisis memakai data asli dan tabel perhitungan.

Dokumen contoh berjudul `Implementasi Model Garin-Lowry pada Kota Hipotetis Menggunakan KNIME Analytics P.docx` hanya dipakai untuk referensi struktur. Dokumen tersebut tidak ditimpa dan placeholder di dalamnya tidak disalin ke laporan baru.

## Studi mandiri dan hasil aktual

- CBD: zona 71, menerima 40% pekerjaan dasar.
- Satelit Barat: zona 63, menerima 30%.
- Satelit Timur: zona 79, menerima 30%.
- Lokasi dipilih dari centroid asli yang paling dekat dengan target offset −3.800 dan +3.800 meter proyeksi pada arah timur–barat dari CBD.
- Total pekerjaan dasar tetap 99,999984; jaringan tetap 30 mph; h=2, e=0,3 dan kedua friction=1.

Terhadap skenario CBD tunggal, penduduk CBD berubah dari 9,150670 menjadi 6,671878, turun sekitar **27,09%**. Radius rata-rata berbobot bertambah **168,64 meter proyeksi** dan HHI penduduk turun sekitar **7,33%**. CBD tetap merupakan zona dengan penduduk dan pekerjaan jasa tertinggi. Kesimpulannya adalah penyebaran relatif terhadap CBD tunggal, bukan terbentuknya tiga puncak permukiman yang sama kuat.

## Membuka versi KNIME terbaru

Jalankan dari direktori proyek:

```powershell
& '.\.venv\Scripts\python.exe' knime/setup/launch_knime.py --workspace knime/report_workspace
```

Pada KNIME Explorer/Local space, buka **Case10_Extended_8_Scenarios**. Copy hasil impor ulang yang juga diuji bernama **Case10_Extended_Reimport_Checked**. Arsip hasil ekspor GUI berada di:

`knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf`

Setelah impor atau pemindahan folder, lakukan Reset all dan Execute all. Output penting:

| Node | Hasil |
|---|---|
| #24 Column Appender | 136 baris baseline; `0`=jasa, `0 (#1)`=penduduk |
| #29 Validate and Run Scenarios | 1.088 baris, delapan skenario |
| #30 Join Scenarios to Geometry | 1.088 baris dengan geometri |
| #33 Custom Case - Three Centers | 136 zona studi mandiri |
| #34 Custom Population Map | Peta penduduk studi mandiri |

Untuk melihat tabel pada UI klasik, pilih node lalu **Shift+F6**. Untuk membuka view, pilih node view lalu **F10**. Screenshot pada laporan berasal dari tindakan ini dalam aplikasi KNIME.

## Berkas angka dan gambar

- `outputs/tables/scenario_comparison_extended.csv`: ringkasan delapan skenario.
- `outputs/tables/all_scenarios_extended.csv`: seluruh 1.088 pasangan skenario–zona.
- `outputs/tables/polycentric_centers.csv`: hasil 136 zona studi mandiri.
- `outputs/tables/custom_change_vs_cbd.csv`: perubahan terhadap CBD tunggal.
- `outputs/maps/polycentric_centers.gpkg`: data GIS studi mandiri.
- `outputs/reports/figures/`: gambar analisis yang dipakai laporan.
- `outputs/reports/screenshots/`: tangkapan layar KNIME asli.
- `outputs/logs/extended_validation.json`: bukti 34 node, ekspor/impor ulang, dan pengujian tambahan.
- `outputs/reports/REPORT_QA.json`: pemeriksaan font hitam Times New Roman, caption, dan batas halaman PDF.

## Reproduksi hasil dan laporan

```powershell
& '.\.venv\Scripts\python.exe' -m src.main all
& '.\.venv\Scripts\python.exe' -m src.custom_case
& '.\.venv\Scripts\python.exe' -m src.report_figures
& '.\.venv\Scripts\python.exe' -m pytest tests -q
```

Screenshot merupakan bukti GUI dan tidak dibuat ulang sebagai gambar tiruan. Setelah bukti KNIME serta XML hasil pytest tersedia, gunakan `knime/setup/validate_extended_delivery.py`, lalu `python -m src.build_reports`. Untuk memperbarui daftar isi dan membuat PDF dengan Microsoft Word terpasang, gunakan `knime/setup/render_word_reports.py`. Pemeriksaan terakhir dijalankan dengan `python -m src.validate_reports`.

Dokumen dapat disunting di Microsoft Word. Jika struktur atau halaman berubah setelah penyuntingan, perbarui daftar isi melalui klik kanan → Update Field → Update entire table. Identitas mahasiswa dapat ditambahkan pada sampul sesuai kebutuhan; laporan tidak mengarang nama, NIM, atau institusi yang belum diberikan.
