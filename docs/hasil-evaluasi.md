# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (korelasi, α = 1,0) | 75,7% | 96,8% | 99,7% | 0,852 |
| CBF saja (α = 0,0) | 91,0% | 99,1% | 99,9% | 0,949 |
| Hibrida bawaan (korelasi, α = 0,5) | 95,6% | 100,0% | 100,0% | 0,975 |
| Hibrida tanpa minat bidang dan kesiapan (α = 0,5) | 96,4% | 99,9% | 100,0% | 0,981 |
| Hibrida dengan cosine murni (α = 0,5) | 95,7% | 100,0% | 100,0% | 0,976 |
| Hibrida proposal (Iachan, α = 0,6) | 88,9% | 97,9% | 99,4% | 0,934 |
| Hibrida tanpa RIASEC (α = 0,5) | 93,9% | 100,0% | 100,0% | 0,966 |
| Baseline: RIASEC saja (indeks Iachan) | 18,1% | 35,2% | 44,2% | 0,324 |
| Baseline: RIASEC saja (korelasi) | 34,5% | 66,4% | 77,6% | 0,534 |
| Baseline: acak (nilai harapan) | 2,9% | 8,6% | 14,3% | 0,118 |

### A.2 Kepekaan terhadap α

Kongruensi minat berbasis korelasi (bawaan):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,0% | 99,1% | 99,9% | 0,949 |
| α = 0,1 | 92,7% | 99,5% | 99,9% | 0,960 |
| α = 0,2 | 93,7% | 99,9% | 100,0% | 0,965 |
| α = 0,3 | 94,7% | 100,0% | 100,0% | 0,971 |
| α = 0,4 | 95,4% | 100,0% | 100,0% | 0,975 |
| α = 0,5 | 95,6% | 100,0% | 100,0% | 0,975 |
| α = 0,6 | 94,4% | 100,0% | 100,0% | 0,969 |
| α = 0,7 | 92,7% | 99,9% | 100,0% | 0,958 |
| α = 0,8 | 90,6% | 99,7% | 100,0% | 0,944 |
| α = 0,9 | 85,5% | 98,9% | 99,9% | 0,909 |
| α = 1,0 | 75,7% | 96,8% | 99,7% | 0,852 |

Kongruensi minat dengan indeks Iachan (proposal):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 90,9% | 99,1% | 99,9% | 0,949 |
| α = 0,1 | 93,1% | 99,4% | 100,0% | 0,962 |
| α = 0,2 | 94,4% | 99,9% | 100,0% | 0,969 |
| α = 0,3 | 95,4% | 99,9% | 100,0% | 0,975 |
| α = 0,4 | 95,4% | 99,9% | 100,0% | 0,975 |
| α = 0,5 | 95,2% | 99,9% | 100,0% | 0,973 |
| α = 0,6 | 93,8% | 99,9% | 100,0% | 0,966 |
| α = 0,7 | 91,1% | 99,9% | 100,0% | 0,950 |
| α = 0,8 | 86,9% | 99,3% | 100,0% | 0,922 |
| α = 0,9 | 79,4% | 97,3% | 99,5% | 0,872 |
| α = 1,0 | 68,4% | 94,0% | 98,4% | 0,806 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 95,2% | 99,9% | 100,0% | 0,973 |
| Hibrida, korelasi | 95,6% | 100,0% | 100,0% | 0,975 |
| KBF saja, iachan | 68,4% | 94,0% | 98,4% | 0,806 |
| KBF saja, korelasi | 75,7% | 96,8% | 99,7% | 0,852 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 84,0% | 97,7% | 99,7% | 0,908 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 92,0% | 100,0% | 100,0% | 0,956 |
| CBF saja, ruang global — spesialis (2 skill lain) | 91,0% | 99,1% | 99,9% | 0,949 |
| Hibrida, ruang global — spesialis (2 skill lain) | 95,6% | 100,0% | 100,0% | 0,975 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 82,6% | 96,8% | 99,4% | 0,898 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 92,6% | 99,8% | 100,0% | 0,960 |
| CBF saja, ruang global — generalis (15 skill lain) | 90,4% | 98,7% | 99,9% | 0,945 |
| Hibrida, ruang global — generalis (15 skill lain) | 95,1% | 100,0% | 100,0% | 0,973 |

## B. Data responden

2 responden, 0 di antaranya profesional yang mengisi profesi aktual.

### B.1 Hit Rate terhadap profesi aktual (uji pakar)

Belum ada responden profesional.

### B.2 Precision@K dari penilaian relevansi

| K | Precision@K | n responden |
|---:|---:|---:|
| 1 | – | 0 |
| 3 | – | 0 |
| 5 | – | 0 |

### B.3 Usability (SUS)

Belum ada jawaban SUS.

### B.3b Evaluasi penjelasan rekomendasi

Belum ada jawaban.

### B.4 Reliabilitas kuesioner (Cronbach's α)

| Skala | α |
|---|---:|
| RIASEC R | 0,67 |
| RIASEC I | 0,94 |
| RIASEC A | -6,00 |
| RIASEC S | 0,75 |
| RIASEC E | – |
| RIASEC C | 0,00 |
| Big Five O | 0,00 |
| Big Five C | 0,00 |
| Big Five E | 1,00 |
| Big Five A | – |
| Big Five N | – |

Skala Big Five hanya dua butir per dimensi (BFI-10), sehingga α yang rendah di sana lazim dan bukan tanda instrumen rusak.

### B.5 Skill di luar pilihan

Rata-rata 71.5 skill dipilih per responden. Skill yang diketik sendiri karena tidak ada di pilihan (bahan perluasan basis pengetahuan):

Belum ada.

