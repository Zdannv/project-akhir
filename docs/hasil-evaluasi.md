# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (α = 1,0) | 36,8% | 58,7% | 69,2% | 0,510 |
| CBF saja (α = 0,0) | 85,3% | 96,2% | 98,4% | 0,910 |
| Hibrida (α = 0,6) | 85,5% | 97,3% | 98,7% | 0,913 |

### A.2 Kepekaan terhadap α

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 85,3% | 96,2% | 98,4% | 0,910 |
| α = 0,1 | 86,6% | 96,6% | 98,8% | 0,918 |
| α = 0,2 | 88,1% | 96,9% | 98,9% | 0,928 |
| α = 0,3 | 88,9% | 97,4% | 99,1% | 0,933 |
| α = 0,4 | 89,0% | 98,0% | 99,1% | 0,935 |
| α = 0,5 | 88,0% | 98,1% | 99,1% | 0,930 |
| α = 0,6 | 85,5% | 97,3% | 98,7% | 0,913 |
| α = 0,7 | 82,1% | 93,6% | 96,4% | 0,883 |
| α = 0,8 | 76,7% | 86,2% | 89,2% | 0,827 |
| α = 0,9 | 68,6% | 77,8% | 79,4% | 0,750 |
| α = 1,0 | 36,8% | 58,7% | 69,2% | 0,510 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 85,5% | 97,3% | 98,7% | 0,913 |
| Hibrida, korelasi | 92,4% | 99,1% | 99,6% | 0,957 |
| KBF saja, iachan | 36,8% | 58,7% | 69,2% | 0,510 |
| KBF saja, korelasi | 56,7% | 80,6% | 89,6% | 0,701 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 65,5% | 92,6% | 97,0% | 0,791 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 76,0% | 94,5% | 97,4% | 0,854 |
| CBF saja, ruang global — spesialis (2 skill lain) | 85,3% | 96,2% | 98,4% | 0,910 |
| Hibrida, ruang global — spesialis (2 skill lain) | 85,5% | 97,3% | 98,7% | 0,913 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 50,1% | 81,6% | 92,1% | 0,672 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 66,4% | 88,4% | 94,3% | 0,783 |
| CBF saja, ruang global — generalis (15 skill lain) | 77,1% | 92,9% | 96,1% | 0,855 |
| Hibrida, ruang global — generalis (15 skill lain) | 76,6% | 91,3% | 94,9% | 0,846 |

## B. Data responden

1 responden, 0 di antaranya profesional yang mengisi profesi aktual.

### B.1 Hit Rate terhadap profesi aktual (uji pakar)

Belum ada responden profesional.

### B.2 Precision@K dari penilaian relevansi

| K | Precision@K | n responden |
|---:|---:|---:|
| 1 | 100,0% | 1 |
| 3 | – | 0 |
| 5 | – | 0 |

### B.3 Usability (SUS)

Belum ada jawaban SUS.

### B.4 Reliabilitas kuesioner (Cronbach's α)

| Skala | α |
|---|---:|
| RIASEC R | – |
| RIASEC I | – |
| RIASEC A | – |
| RIASEC S | – |
| RIASEC E | – |
| RIASEC C | – |
| Big Five O | – |
| Big Five C | – |
| Big Five E | – |
| Big Five A | – |
| Big Five N | – |

Skala Big Five hanya dua butir per dimensi (BFI-10), sehingga α yang rendah di sana lazim dan bukan tanda instrumen rusak.

### B.5 Skill di luar pilihan

Rata-rata 46.0 skill dipilih per responden. Skill yang diketik sendiri karena tidak ada di pilihan (bahan perluasan basis pengetahuan):

Belum ada.

