# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| KBF saja (α = 1,0) | 37,6% | 58,8% | 68,6% | 0,515 |
| CBF saja (α = 0,0) | 82,6% | 95,4% | 98,1% | 0,892 |
| Hibrida (α = 0,6) | 84,6% | 96,6% | 98,2% | 0,905 |

### A.2 Kepekaan terhadap α

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| α = 0,0 | 82,6% | 95,4% | 98,1% | 0,892 |
| α = 0,1 | 83,9% | 96,1% | 98,4% | 0,901 |
| α = 0,2 | 85,8% | 96,6% | 98,6% | 0,913 |
| α = 0,3 | 87,6% | 97,4% | 99,0% | 0,925 |
| α = 0,4 | 87,6% | 97,7% | 99,1% | 0,926 |
| α = 0,5 | 87,0% | 97,3% | 98,9% | 0,921 |
| α = 0,6 | 84,6% | 96,6% | 98,2% | 0,905 |
| α = 0,7 | 81,1% | 93,1% | 96,3% | 0,875 |
| α = 0,8 | 75,6% | 84,4% | 88,1% | 0,816 |
| α = 0,9 | 68,1% | 77,1% | 80,0% | 0,746 |
| α = 1,0 | 37,6% | 58,8% | 68,6% | 0,515 |

### A.3 Ukuran kongruensi RIASEC

| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Hibrida, iachan | 84,6% | 96,6% | 98,2% | 0,905 |
| Hibrida, korelasi | 90,6% | 98,7% | 99,6% | 0,946 |
| KBF saja, iachan | 37,6% | 58,8% | 68,6% | 0,515 |
| KBF saja, korelasi | 56,1% | 81,6% | 90,4% | 0,700 |

## B. Data responden

Belum ada responden di basis data. Bagian ini terisi setelah pengujian dengan mahasiswa dan profesional TI dijalankan lewat aplikasinya.

