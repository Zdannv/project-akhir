# Keputusan Desain

Catatan ini memetakan buku proposal ke implementasi, dan mencatat setiap hal
yang berbeda atau yang masih berupa asumsi. Tujuannya supaya tidak ada angka di
sistem yang tidak bisa dijelaskan asal-usulnya saat sidang.

## 1. Peta proposal → implementasi

| Di proposal | Di kode | Catatan |
|---|---|---|
| Profiling: RIASEC | `kuesioner.py`, 18 butir, 3 per tipe | butir susunan sendiri, lihat §3 |
| Profiling: Big Five | `kuesioner.py`, BFI-10 | terjemahan sendiri, lihat §3 |
| Profiling: skill, preferensi, kendala sosial-keluarga | langkah 1 dan 4 kuesioner | |
| Profiling: klaster GMM (K = 8) | **tidak dibuat** | lihat §2 |
| Hard filter pendidikan dan relokasi | `kbf.alasan_tersaring` | profesi tersaring tetap ditampilkan dengan alasannya |
| Kongruensi Iachan | `kbf.kongruensi_iachan` | indeks M, maksimum 28 |
| Bobot KBF 50/20/15/15 dan 60/25/15/0 | `kbf.BOBOT_TANGGUNGAN`, `BOBOT_TANPA` | sesuai proposal |
| CBF cosine similarity skill | `cbf.skor_cbf` | vektor profesi berbobot `skill_weight_pct` |
| `α·KBF + (1−α)·CBF`, α = 0,6 | `hibrida.py` | α bisa diubah untuk eksperimen |
| Dasbor Top-N + detail 3 tab | layar Explore dan Detail Profesi | Analisa · Skill & Kompetensi · Insight |
| Precision@K, Recall@K, Hit Rate@5, SUS | `scripts/evaluasi.py` | lihat §5 |

## 2. Yang sengaja berbeda dari proposal

**GMM tidak dimasukkan ke mesin.** Di proposal, keluaran klaster tidak dipakai
oleh rumus matching mana pun; ia hanya label. Melatihnya juga butuh data
pengguna yang belum ada, dan judul yang sudah direvisi tidak lagi menyebutnya.
Kalau penguji memintanya, tempat yang wajar adalah sebagai label profil di
layar Profil, dilatih dari `profil.riasec + profil.big5` responden yang
terkumpul — tanpa mengubah `hibrida.py`.

**Tumpukan teknologi.** FastAPI + Python untuk mesin dan evaluasi (satu bahasa
untuk rumus dan pengujiannya), React + Vite untuk antarmuka, SQLite untuk
penyimpanan. Tanpa Supabase dan tanpa login: responden cukup mengisi nama,
dan demo tetap jalan tanpa internet.

**Istilah "hybrid filtering".** Di literatur, istilah ini paling sering berarti
collaborative + content-based. Sistem ini tidak memakai collaborative
filtering (belum ada data interaksi pengguna), jadi di naskah sebaiknya ditulis
lengkap: *hybrid knowledge-based dan content-based filtering*, dengan teknik
penggabungan *weighted hybrid* (Burke, 2002).

## 3. Asumsi yang perlu dipertanggungjawabkan

**Sembilan profesi tanpa data skill dari lowongan.** Workbook sumber berhenti di
C027; C023 dan C028–C035 tidak punya relasi skill. Dilengkapi lewat
`data/sumber/pelengkap_*.csv` yang isinya kurasi, dan ditandai
`skill_sumber: "kurasi"` di basis pengetahuan serta di layar detail. **Ini
perlu divalidasi** dengan data lowongan atau pakar sebelum naskah final; kalau
tidak sempat, sembilan profesi itu lebih aman dikeluarkan dari cakupan.

**Profil ideal Big Five per profesi.** O*NET tidak mengukur Big Five. Profil
ideal diturunkan dari O*NET Work Styles dengan pemetaan yang ditulis di
`bangun_kb.py`. Extraversion paling lemah dasarnya karena data Work Styles
yang tersedia tidak memuat Leadership. Pemetaan ini butuh rujukan literatur
di naskah.

**Indeks stabilitas kerja.** Sumber data tidak punya kolom status kontrak.
Indeksnya proksi dari pola kerja (onsite 1,00 · hybrid 0,80 · remote 0,55)
dikurangi penalti sektor baru. Angka-angka itu penilaian, bukan pengukuran.

**Padanan profesi → kode SOC O*NET.** Tiap padanan punya tingkat keyakinan
(high/medium/low) dan ditampilkan di layar detail. Beberapa profesi berbagi
satu kode SOC sehingga profil RIASEC dan Big Five-nya identik — itulah
sebabnya KBF saja tidak bisa membedakan, misalnya, Backend dari Mobile
Developer, dan CBF diperlukan.

**Butir kuesioner.** 18 butir RIASEC disusun sendiri dan BFI-10 diterjemahkan
sendiri; keduanya belum divalidasi. `evaluasi.py` menghitung Cronbach's α dari
jawaban yang terkumpul sebagai bukti awal reliabilitas.

**Skill berbobot nol.** Di data sumber, sebagian soft skill ditandai wajib
tetapi bobotnya 0. Skill itu tampil di analisis kesenjangan, tetapi tidak
menyumbang ke skor CBF.

**Pita rekomendasi** (≥ 75% sangat direkomendasikan, ≥ 60% direkomendasikan)
hanya cara menyajikan skor di antarmuka. Mesin dan evaluasi tidak memakainya.

## 4. Temuan dari simulasi

Angka lengkap ada di `docs/hasil-evaluasi.md`. Tiga hal yang layak dibahas
dengan pembimbing:

1. **Hibrida mengungguli KBF saja maupun CBF saja** — dasar empiris untuk
   memilih pendekatan hybrid.
2. **α = 0,6 bukan yang terbaik di simulasi**; puncaknya di sekitar 0,3–0,4.
   Banyak profesi TI punya kode Holland yang mirip (ICR muncul 11 kali), jadi
   KBF kurang membedakan dan terlalu banyak bobot padanya merugikan.
3. **Korelasi profil RIASEC mengungguli Iachan**, karena Iachan hanya memakai
   tiga huruf teratas dan memberi skor identik untuk profesi berkode sama.

Simulasi memakai persona yang dibangkitkan dari basis pengetahuan itu sendiri,
jadi angkanya batas atas dan **bukan** bukti akurasi pada manusia. Nilai α dan
ukuran kongruensi sebaiknya baru diputuskan setelah ada data responden.

## 5. Rencana pengujian

| Pengujian | Cara | Target proposal |
|---|---|---|
| Fungsional | `pytest` (22 uji) | semua lulus |
| Akurasi, uji pakar | 15–20 profesional TI mengisi sebagai "Profesional TI" beserta profesinya; Hit Rate@5 dan MRR dihitung terhadap profesi itu | Hit Rate@5 ≥ 60% |
| Relevansi | responden menilai tiap rekomendasi relevan/tidak di layar detail; Precision@K | — |
| Usability | 10 butir SUS di menu Penilaian | skor ≥ 68 |
| Reliabilitas instrumen | Cronbach's α per skala | — |

Recall@K dengan satu jawaban benar per orang sama dengan Hit Rate@K, jadi
tidak dilaporkan terpisah. Jawaban mentah kuesioner disimpan, sehingga
perbandingan konfigurasi (α, Iachan vs korelasi) bisa diulang pada data
responden yang sama tanpa meminta mereka mengisi ulang.
