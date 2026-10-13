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
| CBF saja (α = 0,0) | 91,1% | 99,1% | 99,9% | 0,949 |
| Hibrida bawaan (korelasi, α = 0,5) | 95,7% | 100,0% | 100,0% | 0,976 |
| Hibrida tanpa minat bidang dan kesiapan (α = 0,5) | 95,6% | 99,8% | 99,9% | 0,975 |
| Hibrida proposal (Iachan, α = 0,6) | 88,9% | 97,9% | 99,4% | 0,934 |

### A.2 Kepekaan terhadap α

Kongruensi minat berbasis korelasi (bawaan):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,1% | 99,1% | 99,9% | 0,949 |
| α = 0,1 | 92,6% | 99,3% | 99,9% | 0,958 |
| α = 0,2 | 93,4% | 99,6% | 99,9% | 0,963 |
| α = 0,3 | 94,2% | 99,9% | 99,9% | 0,968 |
| α = 0,4 | 94,7% | 99,9% | 100,0% | 0,971 |
| α = 0,5 | 95,7% | 100,0% | 100,0% | 0,976 |
| α = 0,6 | 95,9% | 100,0% | 100,0% | 0,977 |
| α = 0,7 | 94,8% | 100,0% | 100,0% | 0,971 |
| α = 0,8 | 91,7% | 99,9% | 100,0% | 0,952 |
| α = 0,9 | 87,1% | 99,3% | 99,9% | 0,919 |
| α = 1,0 | 75,7% | 96,8% | 99,7% | 0,852 |

Kongruensi minat dengan indeks Iachan (proposal):

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,1% | 99,1% | 99,9% | 0,949 |
| α = 0,1 | 92,7% | 99,3% | 99,9% | 0,959 |
| α = 0,2 | 93,7% | 99,6% | 99,9% | 0,965 |
| α = 0,3 | 94,8% | 99,8% | 100,0% | 0,971 |
| α = 0,4 | 95,4% | 99,9% | 100,0% | 0,975 |
| α = 0,5 | 95,7% | 99,9% | 100,0% | 0,976 |
| α = 0,6 | 95,1% | 99,9% | 100,0% | 0,973 |
| α = 0,7 | 94,1% | 99,9% | 100,0% | 0,967 |
| α = 0,8 | 89,2% | 99,6% | 100,0% | 0,938 |
| α = 0,9 | 81,9% | 98,1% | 99,8% | 0,888 |
| α = 1,0 | 68,4% | 94,0% | 98,4% | 0,806 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 95,7% | 99,9% | 100,0% | 0,976 |
| Hibrida, korelasi | 95,7% | 100,0% | 100,0% | 0,976 |
| KBF saja, iachan | 68,4% | 94,0% | 98,4% | 0,806 |
| KBF saja, korelasi | 75,7% | 96,8% | 99,7% | 0,852 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 63,1% | 92,6% | 97,6% | 0,781 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 85,6% | 99,4% | 99,9% | 0,920 |
| CBF saja, ruang global — spesialis (2 skill lain) | 91,1% | 99,1% | 99,9% | 0,949 |
| Hibrida, ruang global — spesialis (2 skill lain) | 95,7% | 100,0% | 100,0% | 0,976 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 60,4% | 88,8% | 95,4% | 0,754 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 86,1% | 99,2% | 100,0% | 0,923 |
| CBF saja, ruang global — generalis (15 skill lain) | 89,1% | 98,1% | 99,4% | 0,936 |
| Hibrida, ruang global — generalis (15 skill lain) | 94,9% | 100,0% | 100,0% | 0,973 |

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

