# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (α = 1,0) | 37,9% | 58,2% | 68,7% | 0,515 |
| CBF saja (α = 0,0) | 91,0% | 98,8% | 99,9% | 0,949 |
| Hibrida (α = 0,6) | 88,9% | 98,1% | 99,2% | 0,934 |

### A.2 Kepekaan terhadap α

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 91,0% | 98,8% | 99,9% | 0,949 |
| α = 0,1 | 92,0% | 99,2% | 99,9% | 0,955 |
| α = 0,2 | 92,9% | 99,5% | 99,9% | 0,961 |
| α = 0,3 | 93,6% | 99,6% | 99,9% | 0,965 |
| α = 0,4 | 93,0% | 99,7% | 99,9% | 0,962 |
| α = 0,5 | 91,9% | 99,5% | 99,9% | 0,955 |
| α = 0,6 | 88,9% | 98,1% | 99,2% | 0,934 |
| α = 0,7 | 83,4% | 94,4% | 96,9% | 0,892 |
| α = 0,8 | 76,2% | 84,1% | 88,4% | 0,821 |
| α = 0,9 | 69,8% | 77,9% | 79,4% | 0,757 |
| α = 1,0 | 37,9% | 58,2% | 68,7% | 0,515 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 88,9% | 98,1% | 99,2% | 0,934 |
| Hibrida, korelasi | 96,0% | 100,0% | 100,0% | 0,978 |
| KBF saja, iachan | 37,9% | 58,2% | 68,7% | 0,515 |
| KBF saja, korelasi | 57,4% | 80,9% | 90,7% | 0,708 |

### A.4 Ruang vektor CBF

Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi
saja (`profesi`), untuk persona spesialis dan generalis.

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| CBF saja, ruang profesi — spesialis (2 skill lain) | 64,9% | 95,0% | 98,4% | 0,794 |
| Hibrida, ruang profesi — spesialis (2 skill lain) | 76,1% | 94,1% | 97,2% | 0,852 |
| CBF saja, ruang global — spesialis (2 skill lain) | 91,0% | 98,8% | 99,9% | 0,949 |
| Hibrida, ruang global — spesialis (2 skill lain) | 88,9% | 98,1% | 99,2% | 0,934 |
| CBF saja, ruang profesi — generalis (15 skill lain) | 58,3% | 89,4% | 95,3% | 0,741 |
| Hibrida, ruang profesi — generalis (15 skill lain) | 72,1% | 89,4% | 94,6% | 0,817 |
| CBF saja, ruang global — generalis (15 skill lain) | 87,7% | 97,7% | 99,4% | 0,927 |
| Hibrida, ruang global — generalis (15 skill lain) | 83,9% | 95,5% | 97,6% | 0,898 |

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

