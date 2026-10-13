# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (korelasi, α = 1,0) | 55,9% | 82,2% | 90,4% | 0,700 |
| CBF saja (α = 0,0) | 91,4% | 99,4% | 99,9% | 0,952 |
| Hibrida bawaan (korelasi, α = 0,5) | 95,9% | 99,9% | 99,9% | 0,978 |
| Hibrida proposal (Iachan, α = 0,6) | 89,6% | 98,5% | 99,3% | 0,940 |

### A.2 Kepekaan terhadap α

Kongruensi minat berbasis korelasi (bawaan):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,4% | 99,4% | 99,9% | 0,952 |
| α = 0,1 | 91,6% | 99,6% | 99,9% | 0,955 |
| α = 0,2 | 92,9% | 99,6% | 99,9% | 0,962 |
| α = 0,3 | 93,6% | 99,6% | 99,9% | 0,966 |
| α = 0,4 | 94,6% | 99,7% | 99,9% | 0,971 |
| α = 0,5 | 95,9% | 99,9% | 99,9% | 0,978 |
| α = 0,6 | 96,3% | 99,9% | 99,9% | 0,980 |
| α = 0,7 | 96,5% | 99,8% | 99,9% | 0,982 |
| α = 0,8 | 96,6% | 99,8% | 99,8% | 0,982 |
| α = 0,9 | 94,0% | 99,4% | 99,6% | 0,967 |
| α = 1,0 | 55,9% | 82,2% | 90,4% | 0,700 |

Kongruensi minat dengan indeks Iachan (proposal):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,4% | 99,4% | 99,9% | 0,952 |
| α = 0,1 | 92,0% | 99,6% | 99,9% | 0,957 |
| α = 0,2 | 93,1% | 99,6% | 99,9% | 0,963 |
| α = 0,3 | 93,9% | 99,6% | 99,9% | 0,967 |
| α = 0,4 | 93,4% | 99,4% | 99,8% | 0,964 |
| α = 0,5 | 92,4% | 99,1% | 99,6% | 0,958 |
| α = 0,6 | 89,6% | 98,5% | 99,3% | 0,940 |
| α = 0,7 | 83,9% | 95,7% | 97,1% | 0,898 |
| α = 0,8 | 75,6% | 83,1% | 87,5% | 0,812 |
| α = 0,9 | 68,2% | 76,6% | 78,4% | 0,743 |
| α = 1,0 | 36,8% | 57,4% | 68,1% | 0,506 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 92,4% | 99,1% | 99,6% | 0,958 |
| Hibrida, korelasi | 95,9% | 99,9% | 99,9% | 0,978 |
| KBF saja, iachan | 36,8% | 57,4% | 68,1% | 0,506 |
| KBF saja, korelasi | 55,9% | 82,2% | 90,4% | 0,700 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 64,9% | 92,4% | 98,4% | 0,790 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 80,6% | 98,4% | 99,7% | 0,893 |
| CBF saja, ruang global — spesialis (2 skill lain) | 91,4% | 99,4% | 99,9% | 0,952 |
| Hibrida, ruang global — spesialis (2 skill lain) | 95,9% | 99,9% | 99,9% | 0,978 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 59,1% | 89,6% | 95,4% | 0,749 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 79,1% | 96,7% | 99,0% | 0,878 |
| CBF saja, ruang global — generalis (15 skill lain) | 89,0% | 98,1% | 99,4% | 0,935 |
| Hibrida, ruang global — generalis (15 skill lain) | 94,9% | 99,4% | 99,9% | 0,971 |

## B. Data responden

2 responden, 0 di antaranya profesional yang mengisi profesi aktual.

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

