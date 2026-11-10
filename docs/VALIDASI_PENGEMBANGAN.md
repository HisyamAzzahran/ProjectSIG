# Validasi pengembangan dan studi mandiri

Tanggal: 10 November 2026. Berkas tujuh skenario sebelumnya dipertahankan.

- Eksekusi native: **34/34 node EXECUTED**; keluaran skenario dan join geometri **1.088 baris**.
- Studi tambahan: CBD 40%, Satelit Barat zona 63 sebesar 30%, Satelit Timur zona 79 sebesar 30%.
- Selisih maksimum penduduk studi mandiri Python vs KNIME: 0.
- Pengujian aktual: **29 lulus; 0 gagal**. Bukti: outputs/logs/pytest_extended.log dan XML.
- Ekspor menggunakan GUI KNIME: knime/Case10_Garin_Lowry_Extended_8_Scenarios.knwf.
- Integritas arsip dan kode terkemas: True.
- Impor ulang melalui GUI: True.
- Reset dan eksekusi ulang setelah impor pada lokasi baru: True.

Pemeriksaan perpindahan lokasi memakai flow variable initializer, sehingga cache yang hanya diimpor tidak dihitung sebagai bukti eksekusi ulang.

Tangkapan layar di outputs/reports/screenshots/ berasal dari aplikasi KNIME, tanpa mengganti isi tabel atau membentuk screenshot buatan. Gambar analitis berasal dari geometri asli dan tabel hasil komputasi.

Batasan: konfigurasi diuji pada laptop Windows ini, KNIME 5.12.0, dan ekstensi geospatial dengan perbaikan kompatibilitas lokal. Batch Executor tetap tidak tersedia; GUI telah digunakan. Model merupakan simulasi teoritis, bukan prediksi kota nyata.
