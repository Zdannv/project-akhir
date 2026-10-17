# Hasil Evaluasi

Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.

## A. Simulasi persona sintetis

1400 persona (40 per profesi × 35 profesi), derau σ = 0.12, seed 42. Tiap persona dibangkitkan dari satu profesi; mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.

> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini
> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.

### A.1 Ablasi: sumbangan tiap komponen

Selang kepercayaan 95%: Wilson untuk Hit@K, bootstrap 2000 sampel ulang untuk MRR. p-value dari uji
berpasangan terhadap hibrida bawaan pada persona yang sama.

| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@1 | p Wilcoxon RR |
|---|---:|---:|---:|---:|---:|---:|
| KBF saja (korelasi, α = 1,0) | 75,7% (73,4%–77,9%) | 96,8% | 99,7% | 0,852 (0,838–0,866) | < 0,001 | < 0,001 |
| CBF saja (α = 0,0) | 91,0% (89,4%–92,4%) | 99,1% | 99,9% | 0,949 (0,941–0,958) | < 0,001 | < 0,001 |
| Hibrida bawaan (korelasi, α = 0,5) | 95,6% (94,4%–96,5%) | 100,0% | 100,0% | 0,975 (0,969–0,981) | acuan | acuan |
| Hibrida tanpa minat bidang dan kesiapan (α = 0,5) | 96,4% (95,3%–97,3%) | 99,9% | 100,0% | 0,981 (0,975–0,986) | 0,134 | 0,033 |
| Hibrida dengan cosine murni (α = 0,5) | 95,7% (94,5%–96,7%) | 100,0% | 100,0% | 0,976 (0,970–0,982) | 0,851 | 0,922 |
| Hibrida proposal (Iachan, α = 0,6) | 88,9% (87,2%–90,5%) | 97,9% | 99,4% | 0,934 (0,925–0,944) | < 0,001 | < 0,001 |
| Hibrida tanpa RIASEC (α = 0,5) | 93,9% (92,5%–95,0%) | 100,0% | 100,0% | 0,966 (0,959–0,973) | < 0,001 | < 0,001 |
| Baseline: RIASEC saja (indeks Iachan) | 18,1% (16,1%–20,2%) | 35,2% | 44,2% | 0,324 (0,306–0,343) | < 0,001 | < 0,001 |
| Baseline: RIASEC saja (korelasi) | 34,5% (32,1%–37,0%) | 66,4% | 77,6% | 0,534 (0,515–0,553) | < 0,001 | < 0,001 |
| Baseline: kecocokan keahlian Jaccard | 98,6% (97,9%–99,1%) | 100,0% | 100,0% | 0,993 (0,990–0,996) | < 0,001 | < 0,001 |
| Baseline: acak (nilai harapan) | 2,9% | 8,6% | 14,3% | 0,118 | – | – |

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

### A.5 Kurva ketahanan terhadap derau

Derau minat dan kepribadian (σ) dibesarkan; keahlian tetap seperti persona bawaan:

| σ | Hibrida bawaan (korelasi, α = 0,5) Hit@1 | KBF saja Hit@1 | CBF saja Hit@1 | Baseline: kecocokan keahlian Jaccard Hit@1 |
|---:|---:|---:|---:|---:|
| 0,06 | 95,9% | 79,4% | 93,0% | 98,6% |
| 0,12 | 95,3% | 75,7% | 93,0% | 98,6% |
| 0,20 | 94,0% | 58,4% | 93,0% | 98,6% |
| 0,30 | 92,1% | 40,3% | 93,0% | 98,6% |
| 0,40 | 90,6% | 30,4% | 93,0% | 98,6% |

Keahlian makin sedikit (peluang memiliki keahlian profesi dikalikan faktor), σ = 0,20:

| faktor keahlian | Hibrida bawaan (korelasi, α = 0,5) Hit@1 | KBF saja Hit@1 | CBF saja Hit@1 | Baseline: kecocokan keahlian Jaccard Hit@1 |
|---:|---:|---:|---:|---:|
| 1,00 | 94,0% | 58,4% | 93,0% | 98,6% |
| 0,60 | 87,4% | 54,7% | 77,6% | 94,1% |
| 0,35 | 81,9% | 60,0% | 56,1% | 74,9% |
| 0,15 | 67,3% | 57,7% | 24,6% | 33,9% |

### A.6 H1: minat bidang pada pengguna berkeahlian sedikit

1400 persona dengan 2–4 keahlian profesi; pengalaman memenuhi syarat. Uji McNemar pada Hit@3.

| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@3 | p Wilcoxon RR |
|---|---:|---:|---:|---:|---:|---:|
| Hibrida bawaan (korelasi, α = 0,5) | 82,5% (80,4%–84,4%) | 98,5% | 100,0% | 0,898 (0,886–0,910) | acuan | acuan |
| Hibrida tanpa minat bidang | 76,4% (74,1%–78,5%) | 95,6% | 99,1% | 0,859 (0,845–0,872) | < 0,001 | < 0,001 |
| KBF saja | 74,7% (72,4%–76,9%) | 95,9% | 99,6% | 0,845 (0,830–0,859) | < 0,001 | < 0,001 |
| CBF saja | 52,4% (49,7%–55,0%) | 76,6% | 85,0% | 0,668 (0,649–0,686) | < 0,001 | < 0,001 |
| Baseline: kecocokan keahlian Jaccard | 52,2% (49,6%–54,8%) | 79,9% | 89,8% | 0,678 (0,660–0,697) | < 0,001 | < 0,001 |

### A.7 H2: kesiapan pengalaman bagi mahasiswa

520 persona mahasiswa (pengalaman 0 tahun, 3–6 keahlian) dari 13 profesi tingkat awal. Profesi senior = 12 profesi bersyarat pengalaman ≥ 2 tahun.

| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@3 | p Wilcoxon RR |
|---|---:|---:|---:|---:|---:|---:|
| Hibrida bawaan (korelasi, α = 0,5) | 96,9% (95,1%–98,1%) | 99,8% | 100,0% | 0,982 (0,973–0,990) | acuan | acuan |
| Hibrida tanpa kesiapan pengalaman | 93,8% (91,4%–95,6%) | 99,6% | 100,0% | 0,966 (0,953–0,977) | 1,000 | < 0,001 |

| Konfigurasi | Porsi profesi senior di 5 teratas |
|---|---:|
| Hibrida bawaan (korelasi, α = 0,5) | 4,5% |
| Hibrida tanpa kesiapan pengalaman | 19,2% |

Wilcoxon porsi senior per persona: p = < 0,001.

### A.8 Pengaruh indeks stabilitas (proksi) bagi pengguna bertanggungan

1400 persona bertanggungan.

| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@1 | p Wilcoxon RR |
|---|---:|---:|---:|---:|---:|---:|
| Hibrida bawaan (korelasi, α = 0,5) | 94,4% (93,0%–95,4%) | 99,9% | 100,0% | 0,969 (0,962–0,975) | acuan | acuan |
| Hibrida tanpa stabilitas kerja | 94,9% (93,7%–96,0%) | 99,9% | 100,0% | 0,972 (0,966–0,978) | 0,077 | 0,038 |

Daftar lima teratas berubah pada 32,6% persona bila komponen stabilitas dibuang.

## C. Uji pada lowongan nyata

863 lowongan LinkedIn unik (April–Juli 2026) yang judulnya terpetakan ke profesi data/AI dan menyebut ≥ 3 keahlian (median 7). Keahlian yang disebut lowongan menjadi profil, judul lowongan menjadi jawaban benar, dan peringkat dihitung di antara 35 profesi. Uji McNemar pada Hit@3.

> Sebagian relasi keahlian profesi data di basis pengetahuan diringkas dari lowongan yang sama, sehingga uji ini
> belum sepenuhnya lepas; tetapi kasusnya teks lowongan apa adanya, bukan persona yang dibangkitkan mesin.

| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@3 | p Wilcoxon RR |
|---|---:|---:|---:|---:|---:|---:|
| CBF gabungan (bawaan) | 34,1% (31,0%–37,3%) | 75,3% | 84,1% | 0,562 (0,540–0,585) | acuan | acuan |
| CBF cosine murni | 41,7% (38,5%–45,0%) | 73,6% | 85,1% | 0,604 (0,580–0,628) | 0,011 | < 0,001 |
| Baseline: kecocokan keahlian Jaccard | 35,0% (31,9%–38,2%) | 63,2% | 78,3% | 0,528 (0,503–0,552) | < 0,001 | < 0,001 |
| CBF gabungan, tanpa relasi kurasi | 33,6% (30,5%–36,8%) | 66,7% | 80,5% | 0,538 (0,515–0,562) | < 0,001 | < 0,001 |
| Baseline: profesi terpopuler | 35,7% (32,6%–38,9%) | 70,1% | 93,5% | 0,570 (0,547–0,592) | 0,017 | 0,786 |
| Baseline: acak (nilai harapan) | 2,9% | 8,6% | 14,3% | 0,118 | – | – |

| Profesi | n | Hit@1 | Hit@3 (95% CI) | MRR |
|---|---:|---:|---:|---:|
| Data Analyst | 308 | 31,2% | 80,5% (75,7%–84,6%) | 0,566 |
| Business Intelligence Developer | 90 | 32,2% | 83,3% (74,3%–89,6%) | 0,568 |
| Data Engineer | 179 | 38,5% | 78,2% (71,6%–83,6%) | 0,596 |
| Data Scientist | 112 | 19,6% | 70,5% (61,5%–78,2%) | 0,461 |
| Machine Learning Engineer | 44 | 36,4% | 65,9% (51,1%–78,1%) | 0,550 |
| AI Engineer | 118 | 44,1% | 57,6% (48,6%–66,2%) | 0,563 |
| Computer Vision Engineer | 10 | 80,0% | 90,0% (59,6%–98,2%) | 0,875 |
| NLP Engineer | 2 | 100,0% | 100,0% (34,2%–100,0%) | 1,000 |

Pasangan yang paling sering tertukar di peringkat pertama (jawaban benar → tebakan):

- Data Analyst → Business Intelligence Developer: 112 lowongan
- Data Engineer → Business Intelligence Developer: 44 lowongan
- Business Intelligence Developer → Data Analyst: 37 lowongan
- Data Engineer → Database Administrator: 31 lowongan
- Data Scientist → Data Analyst: 30 lowongan
- Data Analyst → Technical Writer: 30 lowongan

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

### B.4 Reliabilitas kuesioner

| Skala | Koefisien |
|---|---:|
| RIASEC R (α) | – |
| RIASEC I (α) | – |
| RIASEC A (α) | – |
| RIASEC S (α) | – |
| RIASEC E (α) | – |
| RIASEC C (α) | – |
| Big Five O (Spearman-Brown) | – |
| Big Five C (Spearman-Brown) | – |
| Big Five E (Spearman-Brown) | – |
| Big Five A (Spearman-Brown) | – |
| Big Five N (Spearman-Brown) | – |

RIASEC memakai Cronbach's α (tiga butir per tipe). Big Five memakai koefisien Spearman-Brown karena BFI-10 hanya dua butir per dimensi. Koefisien baru dihitung setelah ada minimal 10 responden.

### B.4b Relevansi menurut label skor

Porsi rekomendasi yang dinilai relevan oleh responden pada tiap label. Label yang baik menunjukkan porsi relevan yang menurun dari Sangat Cocok ke Kurang Cocok.

| Label | Porsi relevan | n penilaian |
|---|---:|---:|
| Sangat Cocok | – | 0 |
| Cocok | – | 0 |
| Cukup Cocok | 100,0% | 1 |
| Kurang Cocok | – | 0 |

### B.5 Skill di luar pilihan

Rata-rata 71.5 skill dipilih per responden. Skill yang diketik sendiri karena tidak ada di pilihan (bahan perluasan basis pengetahuan):

Belum ada.

