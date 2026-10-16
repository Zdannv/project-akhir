# Relevansi RIASEC dan Data O*NET untuk Kondisi Indonesia

Pertanyaan dari sidang proposal: profil minat profesi diambil dari O*NET yang
datanya berasal dari Amerika Serikat. Apakah masih relevan untuk Indonesia?

Jawaban singkatnya: **sebagian relevan, sebagian belum terbukti, dan sistem
ini dirancang supaya tidak bergantung padanya serta bisa dikalibrasi dengan
data lokal.** Rinciannya di bawah.

## 1. Ada dua hal berbeda yang sering tercampur

| | Apa | Dipakai sistem untuk |
|---|---|---|
| **RIASEC sisi orang** | Teori bahwa minat seseorang dapat digambarkan dengan enam tipe Holland | Kuesioner minat 18 butir yang diisi pengguna |
| **RIASEC sisi profesi** (*occupational interest profile*) | Skor enam tipe untuk tiap profesi, ditetapkan O*NET dari deskripsi pekerjaan di AS | Profil minat 35 profesi pada basis pengetahuan |

Bukti untuk keduanya berbeda.

## 2. Sisi orang: didukung lintas budaya, dan lazim dipakai di Indonesia

- Struktur RIASEC diuji pada 20.108 klien layanan karier nasional Finlandia.
  Urutan melingkarnya sesuai model Holland dan tingkat kecocokannya setara
  dengan sampel di AS, walaupun bentuk lingkarannya tidak sempurna [1].
- Tinjauan cakupan atas alat ukur minat vokasional di Indonesia (17 artikel,
  2014–2024) menemukan bahwa sebagian besar alat ukur di Indonesia memang
  disusun dari struktur minat Holland. Tinjauan yang sama mencatat bahwa bukti
  validitasnya masih banyak celah [2].
- Tes Minat Vokasional Indonesia pada 474 siswa SMK menunjukkan kecocokan
  model yang baik, tetapi sebagian butir lemah karena kosakatanya tidak sesuai
  usia responden, sehingga kalimat butir perlu disesuaikan [3].
- Adaptasi Indonesia dari CABIN-NET (instrumen minat berbasis O*NET) pada 375
  responden: reliabilitas semua dimensi RIASEC tinggi (α dan ω > 0,70) dan
  skornya berkorelasi positif dengan O*NET Interest Profiler, tetapi struktur
  faktor Holland belum memenuhi kriteria kecocokan model [4].

**Kesimpulan sisi orang:** memakai RIASEC untuk mengukur minat orang Indonesia
punya dasar, tetapi kualitas butirnya harus dibuktikan. Karena itu butir
kuesioner sistem ini diuji validitas isinya (Aiken's V oleh ahli) dan
reliabilitasnya (Cronbach's α dari data responden). Lihat
`backend/scripts/validitas_isi.py`.

## 3. Sisi profesi: titik yang lemah

- Ekspor data okupasi O*NET ke luar AS jarang diuji validitasnya. Studi yang
  membandingkan 296 pasang okupasi AS–Korea Selatan menemukan bahwa profil
  minat okupasi Korea kurang cocok dengan model RIASEC dibandingkan profil
  AS, dan perbedaannya bersumber dari cara tugas pekerjaan dituliskan di tiap
  negara [5].

Belum ditemukan penelitian yang membandingkan profil minat okupasi O*NET
dengan profesi di Indonesia. Jadi **tidak ada dasar untuk mengklaim** profil
O*NET pasti berlaku di Indonesia, dan juga tidak ada dasar untuk mengklaim
sebaliknya. Itu yang dijawab dengan desain dan pengujian di bawah.

## 4. Bagaimana sistem ini menanganinya

1. **RIASEC bukan penentu utama.** Bobot RIASEC 0,30 di dalam KBF, dan KBF
   0,5 dari skor akhir, jadi profil minat O*NET menyumbang sekitar 15% skor
   akhir (12,5% bagi yang punya tanggungan). Sisanya dari data lokal: skill
   dan syarat pendidikan, pengalaman, serta gaji dari lowongan kerja Indonesia,
   dan minat bidang kerja TI yang ditanyakan langsung.
2. **Diuji seberapa bergantung hasilnya pada RIASEC.** Konfigurasi
   "Hibrida tanpa RIASEC" selalu dihitung berdampingan. Pada simulasi, Hit@1
   hanya turun dari 95,6% menjadi 93,9% tanpa RIASEC, sementara rekomendasi
   yang hanya memakai RIASEC (pendekatan penelitian terdahulu) hanya 18,1%
   (indeks Iachan) dan 34,5% (korelasi). Lihat `docs/hasil-evaluasi.md` A.1.
   Angka simulasi berasal dari persona sintetis dan harus dikonfirmasi dengan
   data responden.
3. **Dapat dikalibrasi dengan data lokal.** Jawaban minat responden
   profesional TI Indonesia dipakai untuk menyusutkan profil O*NET tiap
   profesi ke rata-rata profesional lokal di profesi itu
   (bobot lokal = n / (n + k)). Dampaknya diuji dengan *leave-one-out* dan uji
   McNemar/Wilcoxon terhadap profil O*NET murni:
   - otomatis dilaporkan di `docs/hasil-evaluasi.md` B.1
     (baris "profil RIASEC dikalibrasi responden lokal"),
   - rinci per profesi, termasuk korelasi profil O*NET vs lokal, lewat
     `backend/scripts/kalibrasi_riasec.py`,
   - dan hanya diterapkan (`--tulis`) kalau terbukti tidak lebih buruk.
4. **Kalimat butir diuji ahli** sebelum pengambilan data, sesuai temuan [3]
   bahwa kosakata butir memengaruhi kualitas pengukuran.

## 5. Kalimat yang bisa dipakai saat sidang

> Profil minat profesi memang berasal dari O*NET. Literatur menunjukkan
> struktur minat RIASEC cukup stabil lintas negara dan sudah menjadi dasar
> sebagian besar alat ukur minat di Indonesia, tetapi profil minat per profesi
> belum pernah diuji untuk Indonesia dan di negara lain terbukti bisa berbeda.
> Karena itu RIASEC hanya menyumbang sekitar 15% skor akhir; sebagian besar
> skor berasal dari data lowongan kerja Indonesia. Kami juga menguji seberapa
> besar hasilnya berubah tanpa RIASEC, dan menyediakan kalibrasi profil minat
> dari responden profesional TI Indonesia yang hanya dipakai kalau terbukti
> lebih akurat pada uji *leave-one-out*.

## Referensi

[1] V. Puonti, A. J. Tolvanen, J. Rantanen, dan N. H. Kiuru, "The Structure of
Vocational Interests in Finland: A Study of the Fit of Holland's RIASEC Model
Based on a Representative Nationwide Sample of Career Counselling Clients,"
*Journal of Career Assessment*, vol. 34, no. 4, hal. 958–984, 2026,
doi: 10.1177/10690727251414369.

[2] R. S. Bagaskara, H. F. G. I. Nurochim, H. P. D. Susilowati, dan N. N.
Agustin, "Exploring Vocational Interest Measurement Instruments in Indonesia:
Insights from a Scoping Review," *Jurnal Psikologi*, vol. 51, no. 3, 2024,
doi: 10.22146/jpsi.101309.

[3] R. P. Ayuni dan M. A. Hakim, "Construct Validity of Indonesian Vocational
Interest Test (Tes Minat Vokasional Indonesia) to Measure Interest of
Vocational School Student," *Psympathic: Jurnal Ilmiah Psikologi*, vol. 12,
no. 2, hal. 125–136, 2025, doi: 10.15575/psy.v12i2.44353.

[4] I. Putri, "Adaptasi Comprehensive Assessment of Basic Interest–O*NET
(CABIN-NET) Versi Bahasa Indonesia," skripsi, Universitas Muhammadiyah
Malang, 2026. *(Identitas institusi dari metadata repositori; periksa ulang
sebelum dikutip.)*

[5] J. Youn, "How do occupations differ across South Korea and the US: Studies
of RIASEC occupational interest profiles (OIPs)," disertasi, University of
Illinois at Urbana-Champaign, 2024.
