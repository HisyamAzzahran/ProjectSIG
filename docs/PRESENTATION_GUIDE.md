# Panduan presentasi: Model Garin–Lowry pada kota hipotetis

## Alur presentasi sekitar 8–10 menit

**1. Pertanyaan penelitian.** Bagaimana lokasi pekerjaan dasar dan kemudahan perjalanan memengaruhi persebaran penduduk serta pekerjaan jasa? Jelaskan bahwa kota ini dibuat untuk eksperimen teoritis. Angka yang dihasilkan bukan ramalan jumlah penduduk suatu kota nyata.

**2. Data dan struktur kota.** Tampilkan `01_city_structure.png`. Data berisi 136 poligon zona, 136 titik centroid dan 330 fitur jalan. Bentuk kota mengikuti satu CBD dan sembilan cincin luar yang dibagi menjadi 15 sektor. Titik pusat adalah zona 71. Koordinat berformat EPSG:3857, tetapi lokasi tersebut tetap merupakan penempatan kota hipotetis, sehingga peta tidak menggunakan basemap dunia nyata.

**3. Mengapa Garin–Lowry?** Pekerjaan dasar adalah kegiatan ekonomi yang dianggap datang dari luar sistem model. Pekerjaan ini mendukung penduduk. Penduduk membutuhkan layanan, sehingga muncul pekerjaan jasa. Pekerja jasa juga mendukung penduduk. Model menghitung keseimbangan dari hubungan yang berulang ini.

**4. Peran KNIME.** Tampilkan workflow. Bagian OD membaca data, menghitung rute terpendek dan menambahkan biaya perjalanan lokal. Bagian Garin–Lowry mengubah daftar OD menjadi matriks, melakukan normalisasi, lalu menyelesaikan persamaan dengan Python. Seluruh 26 node asli tetap dipertahankan. Node tambahan memeriksa data dan baseline, menjalankan skenario, menggabungkan hasil dengan geometri dan mengekspor peta serta tabel. Sebutkan status eksekusi yang tercatat dalam `VALIDATION_REPORT.md`, bukan hanya hasil pengujian Python.

**5. Persamaan yang perlu dipahami.** Gunakan tiga hubungan: `E = B + S`, `P = GE`, dan `S = TP`. B adalah pekerjaan dasar, S pekerjaan jasa, E seluruh pekerjaan, dan P penduduk. G menyebarkan penduduk dari pekerjaan; T menyebarkan pekerjaan jasa dari permintaan penduduk. Substitusi menghasilkan `(I − GT)P = GB`. Matriks kiri dan kanan dihitung, kemudian diselesaikan sebagai sistem persamaan linear. Tidak perlu menjelaskan detail faktorisasi LU kecuali ditanya.

**6. Contoh total.** Setiap satu pekerjaan mendukung dua penduduk; setiap satu penduduk menghasilkan 0,3 pekerjaan jasa. Jika B=100, maka `P=2(100+0,3P)`, sehingga `P=500` dan `S=150`. Dalam file asli, total pekerjaan dasar tersimpan sebagai 99,999984 akibat pembulatan, sehingga hasil aktual sedikit di bawah 500 dan 150. Nilai pecahan adalah satuan simulasi.

**7. Baseline dan pemeriksaan.** Baseline arsip workflow memakai pekerjaan dasar merata (`BEMP_Unif`), sedangkan pengantar buku memakai pekerjaan dasar di CBD (`BEMP_CBD`). Keduanya jangan tertukar. Perhitungan independen berhasil mereproduksi hasil tersimpan. ID unik zona adalah ORIG_FID, bukan TRACT0_ID; TRACT0_ID hanya menandai sepuluh zona pada satu transek.

**8. Hasil skenario.** Tampilkan `05_scenario_population.png` dan `scenario_comparison.png`. Memusatkan pekerjaan dasar di CBD menaikkan populasi CBD dari sekitar 5,43 menjadi 9,15. Friction yang lebih besar meningkatkan penalti perjalanan jauh, sehingga distribusi lebih terkonsentrasi. Peningkatan kecepatan ring 7 menjadi 75 mph membuat sebagian lokasi luar relatif lebih mudah diakses dan menggeser distribusi ke luar. Total populasi dan pekerjaan jasa tetap karena total pekerjaan dasar dan rasio demografis tidak diubah.

**9. Membaca perubahan spasial.** Pada `06_population_change.png`, warna menunjukkan penambahan atau pengurangan terhadap baseline uniform. Jumlah perubahan seluruh zona mendekati nol. Peta beltway terpisah memakai skala warna yang lebih kecil; sebutkan perbedaan legendanya. Klik zona pada peta interaktif untuk menampilkan nilai dan ID. Peta menampilkan jumlah per zona, bukan kepadatan per km².

**10. Kesimpulan yang didukung.** Pada asumsi model ini, distribusi pekerjaan dasar, friction perjalanan dan kecepatan jaringan mengubah lokasi penduduk serta pekerjaan jasa. Hasil tidak membuktikan bahwa kebijakan jalan tertentu akan memberikan dampak yang sama pada kota nyata. Model belum memasukkan kapasitas perumahan, harga lahan, kemacetan endogen atau perilaku migrasi.

## Jawaban singkat untuk pertanyaan dosen

| Pertanyaan | Jawaban |
|---|---|
| Mengapa tidak memakai jarak lurus? | Interaksi dipengaruhi jaringan transportasi, sehingga dihitung rute terpendek pada garis jalan asli. |
| Mengapa diagonal matriks biaya tidak nol? | Node #7 menambahkan komponen perjalanan lokal berbasis seperempat perimeter, sesuai contoh asli. |
| Dari mana kecepatan jalan diperoleh? | SHP yang disuplai tidak memiliki kolom speed. Nilainya dipulihkan dari tabel tersimpan dalam workflow asli setelah seluruh ID dan geometri jalan diperiksa cocok. |
| Mengapa total penduduk sama antar skenario? | Total pekerjaan dasar, rasio penduduk per pekerja dan rasio jasa per penduduk dipertahankan. Skenario mengubah alokasi spasial. |
| Apa bukti hasilnya benar? | Ada pemeriksaan konservasi total, residual persamaan, perbandingan solver linear dan iterasi, perbandingan dengan hasil asli, serta pengujian data GIS dan jaringan. |
| Apakah hasil sudah dijalankan di KNIME? | Jawab sesuai status final dalam VALIDATION_REPORT.md dan tunjukkan bukti log/screenshot asli. |

## Berkas yang dibuka saat demonstrasi

1. Workflow KNIME final atau folder workflow sesuai `KNIME_SETUP.md`.
2. `outputs/maps/01_city_structure.png`.
3. `outputs/maps/03_baseline_population.png` dan `04_baseline_services.png`.
4. `outputs/maps/05_scenario_population.png` dan `07_beltway_change.png`.
5. `outputs/maps/interactive_scenarios.html`.
6. `outputs/tables/scenario_comparison.csv` dan `docs/VALIDATION_REPORT.md`.
