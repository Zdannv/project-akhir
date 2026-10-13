# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (α = 1,0) | 38,0% | 58,5% | 68,3% | 0,515 |
| CBF saja (α = 0,0) | 92,9% | 99,1% | 99,9% | 0,959 |
| Hibrida (α = 0,6) | 89,7% | 97,5% | 98,9% | 0,937 |

### A.2 Kepekaan terhadap α

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 92,9% | 99,1% | 99,9% | 0,959 |
| α = 0,1 | 93,4% | 99,3% | 99,9% | 0,963 |
| α = 0,2 | 94,5% | 99,4% | 99,9% | 0,969 |
| α = 0,3 | 94,4% | 99,4% | 99,9% | 0,968 |
| α = 0,4 | 93,9% | 99,6% | 99,8% | 0,966 |
| α = 0,5 | 92,5% | 99,0% | 99,6% | 0,957 |
| α = 0,6 | 89,7% | 97,5% | 98,9% | 0,937 |
| α = 0,7 | 84,4% | 94,1% | 96,5% | 0,896 |
| α = 0,8 | 75,4% | 83,6% | 87,0% | 0,811 |
| α = 0,9 | 68,4% | 76,1% | 78,1% | 0,743 |
| α = 1,0 | 38,0% | 58,5% | 68,3% | 0,515 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 89,7% | 97,5% | 98,9% | 0,937 |
| Hibrida, korelasi | 96,6% | 100,0% | 100,0% | 0,982 |
| KBF saja, iachan | 38,0% | 58,5% | 68,3% | 0,515 |
| KBF saja, korelasi | 55,2% | 81,1% | 90,6% | 0,694 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 65,9% | 92,7% | 98,1% | 0,796 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 74,4% | 92,6% | 96,6% | 0,840 |
| CBF saja, ruang global — spesialis (2 skill lain) | 92,9% | 99,1% | 99,9% | 0,959 |
| Hibrida, ruang global — spesialis (2 skill lain) | 89,7% | 97,5% | 98,9% | 0,937 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 56,6% | 88,0% | 94,8% | 0,730 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 72,4% | 90,6% | 95,4% | 0,821 |
| CBF saja, ruang global — generalis (15 skill lain) | 88,4% | 97,9% | 99,1% | 0,931 |
| Hibrida, ruang global — generalis (15 skill lain) | 84,1% | 95,2% | 97,1% | 0,898 |

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

