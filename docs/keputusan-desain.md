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
| Hard filter pendidikan dan relokasi | `kbf.alasan_tersaring` | pendidikan tetap penyaring; relokasi kini hanya catatan (§2) |
| Kongruensi Iachan | `kbf.kongruensi_iachan` | indeks M, maksimum 28; kini pembanding, bawaannya korelasi (§2) |
| Bobot KBF 50/20/15/15 dan 60/25/15/0 | `kbf.SKEMA_BOBOT["proposal"]` | kini pembanding; bawaannya skema enam komponen (§2) |
| CBF cosine similarity skill | `cbf.skor_cbf` | bawaannya kini gabungan cosine × cakupan (§2); cosine murni jadi pembanding |
| `α·KBF + (1−α)·CBF`, α = 0,6 | `hibrida.py` | bawaan kini α = 0,5 (§2); konfigurasi proposal tersedia sebagai `KONFIG_PROPOSAL` |
| Dasbor Top-N + detail 3 tab | layar Explore dan Detail Profesi | Analisa · Skill & Kompetensi · Insight |
| Analisis kesenjangan skill | `cbf.kesenjangan_skill`, `roadmap.py` | ditambah roadmap bertahap dan simulasi skor |
| Precision@K, Recall@K, Hit Rate@5, SUS | `scripts/evaluasi.py` | lihat §5 |

## 2. Yang sengaja berbeda dari proposal

**GMM tidak dimasukkan ke mesin.** Di proposal, keluaran klaster tidak dipakai
oleh rumus matching mana pun; ia hanya label. Melatihnya juga butuh data
pengguna yang belum ada, dan judul yang sudah direvisi tidak lagi menyebutnya.
Kalau penguji memintanya, tempat yang wajar adalah sebagai label profil di
layar Profil, dilatih dari `profil.riasec + profil.big5` responden yang
terkumpul — tanpa mengubah `hibrida.py`.

**Kongruensi minat: korelasi, bukan Iachan; dan α = 0,5, bukan 0,6.** Ini
penyimpangan terbesar dari proposal, diputuskan pada 13 Oktober 2026 setelah
uji coba dan simulasi.

- *Masalah Iachan.* Indeks Iachan hanya membandingkan tiga huruf teratas dan
  urutannya. Pengguna dengan minat merata (misalnya S 100%, E 100%, C 92%,
  I 83%) mendapat kode SEC, dan kongruensinya dengan profesi berkode ICR jatuh
  ke 7%, padahal minat Investigative-nya 83%. Selisih tipis di kuesioner
  menentukan segalanya. Selain itu 11 profesi berkode sama (ICR), sehingga
  Iachan tidak bisa membedakannya.
- *Penggantinya.* Korelasi Pearson antara keenam skor minat pengguna dan
  profil O*NET profesi, dipetakan ke 0–1. Memakai seluruh bentuk profil.
- *Bukti simulasi.* Hit@1 hibrida naik dari 89,6% (Iachan, α = 0,6) ke 95,9%
  (korelasi, α = 0,5). Dengan Iachan, hibrida α = 0,6 kalah dari CBF saja
  (91,4%); dengan korelasi, hibrida unggul di seluruh rentang α 0,1–0,9.
- *Kenapa α = 0,5.* Dengan korelasi, α 0,5–0,8 memberi hasil hampir sama di
  simulasi. Simulasi menguntungkan KBF (minat persona dibangkitkan dari profil
  profesi itu sendiri), sedangkan minat manusia lebih berderau; pada simulasi
  dengan derau minat dua kali lipat, puncaknya bergeser ke α = 0,5. Maka
  dipilih ujung bawah rentang itu: bobot seimbang antara profil dan skill.

Konfigurasi proposal tidak dibuang. `KONFIG_PROPOSAL` (Iachan, α = 0,6) selalu
dihitung berdampingan di laporan evaluasi dan dasbor peneliti, sehingga Bab 4
bisa menyajikan keduanya. **Keputusan ini perlu disetujui pembimbing**, karena
mengubah rumus yang tertulis di buku proposal.

**Dua komponen KBF baru: minat bidang TI dan kesiapan pengalaman.** Ditambahkan
pada 13 Oktober 2026 karena dua kelemahan yang terlihat saat uji coba.

- *Minat bidang TI.* RIASEC dirancang untuk membedakan bidang pekerjaan besar.
  Di dalam TI hampir semua profesi berkode mirip, sehingga RIASEC nyaris tidak
  membedakan Backend Developer dari Data Engineer dari UI/UX Designer. Yang
  membedakan mereka adalah bidang kerja yang disukai, jadi itu ditanyakan
  langsung: 16 bidang (web, mobile, data, AI, infrastruktur, keamanan, desain,
  manajemen, ...) dinilai 1–5. Tiap profesi punya bobot bidang
  (`bidang_profesi.csv`): bidang utama mengikuti kolom sektor di data lowongan,
  bidang sekunder ditambahkan penulis untuk profesi lintas bidang. Nilainya
  rata-rata berbobot minat pengguna pada bidang profesi itu.
- *Kesiapan pengalaman.* Tanpa ini, profesi senior (IT Project Manager, minimal
  3 tahun) bisa menjadi peringkat satu bagi mahasiswa. Nilainya 1 kalau
  pengalaman memenuhi syarat minimum profesi (kolom `min_experience_year` di
  data lowongan), turun linear sampai 0 saat kurang tiga tahun. Sengaja bukan
  penyaring mutlak: profesi itu tetap tampil, dengan catatan "tujuan jangka
  menengah".

Bobot KBF menjadi (punya tanggungan / tanpa): RIASEC 0,25 / 0,30 · minat
bidang 0,25 / 0,30 · Big Five 0,10 / 0,15 · kesiapan 0,15 / 0,15 · finansial
0,10 / 0,10 · stabilitas 0,15 / 0. Bobot Big Five diturunkan karena dasarnya
paling lemah (BFI-10 dua butir per dimensi, profil ideal hasil turunan).
**Bobot-bobot ini pilihan penulis, bukan hasil dari data.** `scripts/kalibrasi.py`
mencari bobot dan α dari data responden profesional dengan validasi
leave-one-out; jalankan setelah data terkumpul dan ganti bobot hanya kalau
hasil leave-one-out mengungguli bobot bawaan.

**Simulasi tidak mendukung dua komponen ini, dan itu harus dicatat.** KBF saja
memang naik dari 55,9% ke 75,7% (Hit@1), tetapi hibrida justru sedikit turun:
95,6% dengan dua komponen itu, 96,4% tanpanya. Pada persona sintetis, sisi
skill sudah hampir sempurna, sehingga komponen tambahan lebih banyak menambah
derau daripada informasi. Dua komponen ini dipertahankan karena alasan yang
tidak bisa diuji simulasi: pengguna sungguhan sering punya skill sedikit atau
terlalu banyak, dan rekomendasi profesi senior untuk mahasiswa tidak berguna
walaupun "cocok". Kalau data responden profesional juga tidak mendukungnya
(`scripts/kalibrasi.py` akan memberi bobot mendekati nol), keduanya sebaiknya
dibuang.

**Skor skill: gabungan cosine dan cakupan, bukan cosine saja.** Cosine mengukur
arah, bukan kelengkapan. Akibatnya orang dengan tiga skill yang semuanya
penting bagi sebuah profesi mendapat cosine 61% padahal baru menguasai 16%
kebutuhan profesi itu; dua angka itu tampil berdampingan dan saling
bertentangan. Skor CBF bawaan sekarang akar(cosine × cakupan): tinggi hanya
kalau skill-nya searah dan cukup lengkap. Pada simulasi dengan empat jenis
persona (pemula 3 skill, spesialis, generalis, sangat luas), akurasi peringkat
ukuran gabungan setara dengan cosine murni: selisih Hit@1 paling besar 1,1
poin, dan untuk pemula justru 3,5 poin lebih baik. Jadi yang berubah terutama
makna angkanya, bukan urutannya. Roadmap ikut diuntungkan: mempelajari skill
menaikkan cakupan, sehingga skor proyeksi naik.

**Relokasi bukan lagi penyaring mutlak.** Kolom lokasi di data sumber mencatat
kota dengan lowongan terbanyak, bukan kota tempat profesi itu mustahil ada.
Menyaring Mobile Developer bagi orang di luar lima kota besar menyatakan
sesuatu yang tidak didukung datanya, dan bisa menutup pilihan yang sebenarnya
terbuka. Sekarang profesinya tetap dinilai dan pengguna diberi catatan
("lowongannya paling banyak di ...; di kotamu peluangnya mungkin lebih
sedikit"). Catatan itu tidak mengubah skor. Penyaring pendidikan tetap mutlak.

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

**Skill hasil kurasi.** Workbook sumber punya dua lubang, dan keduanya ditambal
lewat `data/sumber/pelengkap_*.csv`:

- sembilan profesi (C023, C028–C035) tidak punya relasi skill sama sekali;
- banyak skill umum tidak ada di daftarnya (machine learning, statistika,
  pengujian, jaringan, riset pengguna, dan lain-lain), sehingga responden tidak
  menemukan skill mereka, dan technical skill tiap profesi terlalu sedikit
  (IT Project Manager 4, Scrum Master 2). Ditambahkan 171 skill beserta
  relasinya ke profesi yang sudah ada, dengan bobot sengaja kecil (3–16)
  supaya tidak mengalahkan data lowongan.

Hasilnya 305 skill dan 898 relasi, **591 relasi di antaranya kurasi (66%)**.
Di dalamnya termasuk platform dan perkakas modern (Supabase, Vercel,
Cloudflare, asisten koding AI, dan sejenisnya) yang tidak muncul di data lowongan.
Technical skill per profesi sekarang 12–47. Karena lebih dari separuh relasi
kini berasal dari kurasi, validasi ini bukan lagi pelengkap: basis pengetahuan
skill harus diperiksa pakar atau dicocokkan dengan data lowongan sebelum
hasilnya dilaporkan sebagai temuan. Setiap
relasi membawa penanda `sumber` (`lowongan` atau `kurasi`), dan layar detail
memberi tahu pengguna kalau daftar skill sebuah profesi memuat kurasi. **Ini
perlu divalidasi** dengan data lowongan atau pakar sebelum naskah final.

**Skill di luar daftar.** Responden bisa mengetik skill yang tidak ada di
pilihan. Skill itu disimpan dan dilaporkan (dasbor peneliti dan bagian B.5
laporan evaluasi) tetapi tidak ikut dihitung, karena belum ada profesi yang bisa
dicocokkan dengannya. Daftar itu adalah bahan perluasan basis pengetahuan dan
bisa dilaporkan sebagai ukuran cakupan kosakata.

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

**Pita kecocokan** (≥ 75% sangat cocok, ≥ 60% cocok, ≥ 45% cukup cocok, di
bawahnya kurang cocok) hanya cara menyajikan skor di antarmuka. Ambangnya
ditetapkan penulis, bukan hasil kalibrasi, dan mesin maupun evaluasi tidak
memakainya. Labelnya sengaja menggambarkan kecocokan, bukan anjuran: profesi
peringkat satu tetap rekomendasi terbaik walau skornya rendah.

**Skor absolut cenderung rendah.** Skor akhir jarang melewati 60–70% karena
tiga hal yang bekerja bersamaan: (a) Iachan memberi nilai sangat rendah kalau
huruf pertama kode minat tidak sama, dan pengguna yang menjawab "suka" di
hampir semua butir mendapat kode tiga huruf yang ditentukan selisih tipis;
(b) cosine pada seluruh kosakata skill menurunkan nilai orang yang memilih
banyak skill; (c) skill bertingkat Dasar dan Menengah dihitung 1/3 dan 2/3.
Yang bermakna adalah URUTAN profesi, bukan angka persennya. Layar detail
merinci berapa poin yang hilang di tiap komponen supaya pengguna bisa melihat
sebabnya.

## 4. Temuan dari simulasi

Angka lengkap ada di `docs/hasil-evaluasi.md`. Tiga hal yang layak dibahas
dengan pembimbing:

1. **Dengan konfigurasi bawaan, hibrida mengungguli KBF saja dan CBF saja**
   (Hit@1 95,6% vs 75,7% dan 91,0%).
2. **Dengan konfigurasi proposal, hibrida kalah dari CBF saja** (88,9% vs
   91,1%). Iachan baru unggul tipis pada α 0,1–0,5 (puncak 93,9% di α = 0,3):
   banyak profesi TI berkode Holland sama, jadi Iachan kurang membedakan dan
   bobot 0,6 padanya terlalu besar. Inilah alasan konfigurasi bawaan diganti (§2).
3. **Korelasi tahan terhadap pilihan α**: Hit@1 di atas 94% untuk α 0,4–0,9.
4. **Cosine global mengungguli cosine pada ruang skill profesi** (Hit@1 92,9%
   vs 65,9%), juga untuk persona yang skill-nya banyak. Varian ruang profesi
   sempat dicoba karena cosine global "mengencerkan" skor orang yang memilih
   banyak skill, tetapi daya bedanya ternyata jauh lebih buruk, jadi cosine
   global — sesuai proposal — dipertahankan.

**Keterbatasan cosine yang perlu disebut di naskah.** Cosine mengukur kemiripan
arah, bukan banyaknya skill. Akibatnya (a) orang yang memilih sangat banyak
skill mendapat skor CBF lebih rendah di semua profesi, dan (b) menambah skill
berbobot kecil bisa sedikit menurunkan skor. Karena itu kemajuan belajar di
roadmap diukur dengan *cakupan* (porsi bobot skill profesi yang dikuasai), yang
selalu naik, sedangkan skor dan peringkat proyeksi ditampilkan apa adanya.

Simulasi memakai persona yang dibangkitkan dari basis pengetahuan itu sendiri,
jadi angkanya batas atas dan **bukan** bukti akurasi pada manusia. Persona
juga dibangkitkan dari vektor minat profesi, sehingga simulasi cenderung
menguntungkan ukuran korelasi. Konfigurasi bawaan dan konfigurasi proposal
harus dibandingkan lagi pada data responden sungguhan.

## 5. Bahan belajar

Roadmap dan layar detail menampilkan bahan belajar. Tidak satu pun ikut dalam
perhitungan skor; semuanya membantu pengguna menindaklanjuti rekomendasi.

| Bahan | Sumber | Catatan |
|---|---|---|
| Sumber belajar per skill | `sumber_belajar.csv`, 216 tautan untuk 182 skill | dokumentasi resmi dan kursus gratis; tiap tautan diperiksa bisa dibuka pada 13 Oktober 2026 |
| Video tutorial per skill | `video_tutorial.csv`, 515 video untuk 271 dari 287 technical skill | dibuat `scripts/ambil_video.py` dari hasil pencarian YouTube, lihat di bawah |
| Tautan cari video dan kursus | dirakit dari nama skill | pencarian YouTube dan Coursera; tersedia untuk semua skill, isinya tidak dikurasi |
| Peta belajar per profesi | `panduan_karier.csv`, 28 profesi | roadmap.sh |
| Ide proyek portofolio | `proyek_portofolio.csv`, 2 per profesi | disusun penulis |
| Tautan lowongan | dirakit dari nama profesi | LinkedIn, Jobstreet, Glints |

**Cara video dipilih.** Tautan video tidak ditulis tangan. Untuk tiap skill,
`ambil_video.py` membuka pencarian YouTube ("tutorial <skill> bahasa
indonesia"), mengambil dua hasil teratas yang durasinya minimal 8 menit dan
judulnya memuat nama skill, lalu memastikan videonya masih ada lewat oEmbed.
Seluruh 563 judul hasilnya dibaca satu per satu; 48 yang meleset dibuang dan
dicatat beserta alasannya di `video_ditolak.csv` (misalnya "dbt" yang ternyata
terapi psikologi, "Helm" yang ternyata helm motor, "risk management" yang
ternyata trading). Video di daftar itu tidak akan terpilih lagi.

Yang dijamin: videonya ada, publik, cukup panjang, dan judulnya relevan. Yang
TIDAK dijamin: mutu isinya, karena tidak ada yang menontonnya. Kanal dan durasi
ditampilkan supaya pengguna bisa menilai sendiri. Sebagian besar berbahasa
Indonesia; untuk skill yang tidak punya tutorial Indonesia, dipakai video
berbahasa Inggris.

Tautan luar bisa berubah. Sebelum demo atau pengujian, jalankan
`scripts/cek_tautan.py` (video diperiksa lewat oEmbed, karena halaman video
yang sudah dihapus tetap menjawab 200) dan perbaiki yang mati.

## 6. Rencana pengujian

| Pengujian | Cara | Target proposal |
|---|---|---|
| Fungsional | `pytest` (33 uji) | semua lulus |
| Kalibrasi bobot | `scripts/kalibrasi.py` pada data profesional, leave-one-out | — |
| Akurasi, uji pakar | 15–20 profesional TI mengisi sebagai "Profesional TI" beserta profesinya; Hit Rate@5 dan MRR dihitung terhadap profesi itu | Hit Rate@5 ≥ 60% |
| Relevansi | responden menilai tiap rekomendasi relevan/tidak di layar detail; Precision@K | — |
| Usability | 10 butir SUS di menu Penilaian | skor ≥ 68 |
| Reliabilitas instrumen | Cronbach's α per skala | — |

Isian yang diperbarui lewat "Ubah jawaban" disimpan sebagai isian baru yang
menunjuk isian lamanya; evaluasi hanya menghitung isian terakhir tiap orang.
Centang di roadmap disimpan terpisah dan tidak pernah mengubah rekomendasi yang
tersimpan, supaya data pengujian tetap mencerminkan jawaban asli.

Recall@K dengan satu jawaban benar per orang sama dengan Hit Rate@K, jadi
tidak dilaporkan terpisah. Jawaban mentah kuesioner disimpan, sehingga
perbandingan konfigurasi (α, Iachan vs korelasi) bisa diulang pada data
responden yang sama tanpa meminta mereka mengisi ulang.
