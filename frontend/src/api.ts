// Bentuk data dan pemanggil API. Nama kolom mengikuti keluaran backend apa adanya.

export type Butir = { kode: string; teks: string }
export type Skill = { id: string; nama: string; kategori: string; tipe: string; alias: string[] }

export type Kuesioner = {
  riasec: { skala: string[]; butir: Butir[] }
  big5: { skala: string[]; awalan: string; butir: Butir[] }
  sus: string[]
  jenjang: { kode: string; nama: string; rank: number }[]
  kota: string[]
  prodi: { id: string; nama: string }[]
  skill: Skill[]
  tingkat_skill: Record<string, string>
  profesi: { id: string; nama: string }[]
}

export type Masukan = {
  nama: string
  jenis_responden: 'mahasiswa' | 'profesional'
  profesi_aktual: string | null
  jenjang: string
  prodi_id: string | null
  domisili: string
  bersedia_relokasi: boolean
  ekspektasi_gaji: number
  punya_tanggungan: boolean
  riasec: Record<string, number>
  big5: Record<string, number>
  skill: Record<string, number>
  skill_lain: string[]
  induk?: string | null
}

export type Sumber = {
  judul: string; penyedia: string; url: string; durasi?: string
  jenis: 'dokumentasi' | 'kursus' | 'latihan' | 'panduan' | 'video'
}
export type Proyek = { tingkat: string; judul: string; deskripsi: string }

export type SkillProfesi = {
  skill_id: string
  nama: string
  wajib: boolean
  bobot: number
  catatan: string | null
  tingkat?: number
  label_tingkat?: string
  belajar?: Sumber[]
}

export type Kesenjangan = {
  dimiliki: SkillProfesi[]
  belum: SkillProfesi[]
  wajib_terpenuhi: number
  wajib_total: number
}

export type Alasan = { nada: 'cocok' | 'perhatian'; teks: string }

export type Komponen = { riasec: number; big5: number; finansial: number; stabilitas: number }

export type Rekomendasi = {
  peringkat: number
  profesi_id: string
  nama: string
  sektor: string
  skor: number
  kbf: { skor: number; komponen: Komponen; bobot: Komponen }
  cbf: { skor: number; cakupan: number }
  kode_holland: string
  gaji_min: number
  gaji_maks: number
  pola_kerja: string[]
  kesenjangan: Kesenjangan
  alasan: Alasan[]
}

export type Ringkas = {
  peringkat: number
  profesi_id: string
  nama: string
  sektor: string
  skor: number
  skor_kbf: number
  skor_cbf: number
  gaji_min: number
  gaji_maks: number
  pola_kerja: string[]
  kode_holland: string
  deskripsi: string
  senioritas: string
}

export type DataDiri = {
  jenjang: string
  prodi: string | null
  domisili: string
  bersedia_relokasi: boolean
  ekspektasi_gaji: number
  punya_tanggungan: boolean
  skill: { nama: string; tingkat: string }[]
  skill_lain: string[]
}

export type Posisi = { skor: number; skor_cbf: number; cakupan: number; peringkat: number }

export type RingkasTarget = {
  profesi_id: string
  nama: string
  progres: { selesai: number; total: number }
  awal: Posisi | null
  proyeksi: Posisi | null
}

export type SkillRoadmap = { skill_id: string; nama: string; wajib: boolean; bobot: number; dicentang: boolean; belajar: Sumber[] }

export type Roadmap =
  | { target: null }
  | {
      target: {
        profesi_id: string; nama: string; sektor: string; skill_sumber: string
        peta_belajar: { judul: string; url: string } | null; proyek: Proyek[]
      }
      tahap: { kode: string; nama: string; keterangan: string; skill: SkillRoadmap[] }[]
      dikuasai: { skill_id: string; nama: string; wajib: boolean }[]
      progres: { selesai: number; total: number }
      awal: Posisi | null
      proyeksi: Posisi | null
    }

export type Peneliti = {
  n: number
  n_pakar?: number
  pakar?: Record<string, { 'hit@1': number; 'hit@3': number; 'hit@5': number; mrr: number }>
  presisi?: Record<string, [number, number] | null>
  sus?: [number, number] | null
  reliabilitas?: Record<string, number | null>
  skill_lain?: [string, number][]
  n_skill?: number
  responden?: {
    id: string; dibuat: string; nama: string; jenis: string; profesi_aktual: string | null
    kode_holland: string; teratas: string | null; posisi_aktual: number | null
    n_dinilai: number; skor_sus: number | null
  }[]
}

export type Tersaring = { profesi_id: string; nama: string; alasan: { kode: string; pesan: string }[] }

export type Hasil = {
  id: string
  nama: string
  jenis: string
  hasil: {
    konfigurasi: { alpha: number; metode_riasec: string; top_n: number }
    kode_holland: string
    n_lolos: number
    n_tersaring: number
    profil: { riasec: Record<string, number>; big5: Record<string, number> }
    rekomendasi: Rekomendasi[]
    peringkat_lengkap: Ringkas[]
    tersaring: Tersaring[]
  }
  umpan_balik: Record<string, boolean>
  skor_sus: number | null
  data_diri: DataDiri
  target: RingkasTarget | null
}

export type Profesi = {
  id: string
  nama: string
  nama_en: string
  sektor: string
  senioritas: string
  pendidikan_min_label: string
  pengalaman_min_tahun: number
  gaji_min: number
  gaji_maks: number
  gaji_median: number
  pola_kerja: string[]
  lokasi: string[]
  semua_kota: boolean
  deskripsi: string
  tanggung_jawab: string[]
  jenjang_karier: string
  soc_code: string
  soc_judul: string
  soc_keyakinan: string
  soc_catatan: string
  riasec: Record<string, number>
  kode_holland: string
  big5_ideal: Record<string, number>
  stabilitas: number
  skill_sumber: string
  peta_belajar: { judul: string; url: string } | null
  proyek: Proyek[]
}

export type Detail = {
  profesi: Profesi
  profil: { riasec: Record<string, number>; big5: Record<string, number> }
  kode_holland_pengguna: string
  penilaian: Rekomendasi | null
  ringkas: Ringkas | null
  tersaring: Tersaring | null
  relevan: boolean | null
  jadi_target: boolean
  kesenjangan: Kesenjangan
  prodi_terkait: string[]
}

async function minta<T>(jalur: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${jalur}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!r.ok) {
    const badan = await r.json().catch(() => null)
    const detail = badan?.detail
    throw new Error(typeof detail === 'string' ? detail : 'Permintaan gagal. Coba lagi.')
  }
  return r.status === 204 ? (undefined as T) : r.json()
}

export const ambilKuesioner = () => minta<Kuesioner>('/kuesioner')
export const kirimMasukan = (m: Masukan) =>
  minta<{ id: string }>('/rekomendasi', { method: 'POST', body: JSON.stringify(m) })
export const ambilHasil = (id: string) => minta<Hasil>(`/rekomendasi/${id}`)
export const ambilDetail = (id: string, pid: string) => minta<Detail>(`/rekomendasi/${id}/profesi/${pid}`)
export const kirimUmpanBalik = (id: string, penilaian: Record<string, boolean>) =>
  minta<void>(`/rekomendasi/${id}/umpan-balik`, { method: 'POST', body: JSON.stringify({ penilaian }) })
export const ambilMasukan = (id: string) => minta<Masukan>(`/rekomendasi/${id}/masukan`)
export const pilihTarget = (id: string, profesi_id: string | null) =>
  minta<void>(`/rekomendasi/${id}/target`, { method: 'PUT', body: JSON.stringify({ profesi_id }) })
export const ambilRoadmap = (id: string) => minta<Roadmap>(`/rekomendasi/${id}/roadmap`)
export const centangRoadmap = (id: string, skill_id: string, selesai: boolean) =>
  minta<void>(`/rekomendasi/${id}/roadmap/centang`, { method: 'POST', body: JSON.stringify({ skill_id, selesai }) })
export const ambilPeneliti = (kunci: string) =>
  minta<Peneliti>('/peneliti/ringkasan', { headers: kunci ? { 'X-Kunci': kunci } : {} })
export async function unduhEkspor(kunci: string): Promise<Blob> {
  const r = await fetch('/api/peneliti/ekspor.csv', { headers: kunci ? { 'X-Kunci': kunci } : {} })
  if (!r.ok) throw new Error('Gagal mengunduh data.')
  return r.blob()
}
export const kirimSus = (id: string, jawaban: number[]) =>
  minta<{ skor: number }>(`/rekomendasi/${id}/sus`, { method: 'POST', body: JSON.stringify({ jawaban }) })

/** Pita rekomendasi. Hanya cara menyajikan skor; tidak dipakai mesin maupun evaluasi. */
export function pita(skor: number): { label: string; nada: 'hijau' | 'biru' | 'kuning' } {
  if (skor >= 0.75) return { label: 'Sangat Direkomendasikan', nada: 'hijau' }
  if (skor >= 0.6) return { label: 'Direkomendasikan', nada: 'biru' }
  return { label: 'Kurang Direkomendasikan', nada: 'kuning' }
}

export const gaji = (min: number, maks: number) =>
  `Rp ${(min / 1e6).toLocaleString('id-ID')} - ${(maks / 1e6).toLocaleString('id-ID')} juta/bulan`

export const rupiah = (n: number) => `Rp${(n / 1_000_000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} jt`
export const persen = (x: number) => `${Math.round(x * 100)}%`

export const NAMA_RIASEC: Record<string, string> = {
  R: 'Realistic', I: 'Investigative', A: 'Artistic', S: 'Social', E: 'Enterprising', C: 'Conventional',
}
export const NAMA_BIG5: Record<string, string> = {
  O: 'Openness', C: 'Conscientiousness', E: 'Extraversion', A: 'Agreeableness', N: 'Neuroticism',
}
