/**
 * Explore: blok sapaan dan pencarian di kiri, deretan kartu rekomendasi di
 * kanan. Baris pertama adalah lima teratas hasil hybrid filtering; baris kedua
 * sisanya, supaya pengguna bisa membandingkan.
 */
import { ArrowRight, Info, Search, SlidersHorizontal, Target } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ambilHasil, NAMA_RIASEC, persen, type Hasil, type RingkasTarget } from '../api'
import { AppBottomNav, AppTopNav } from '../komponen/AppNav'
import { BarisKartu, KartuProfesi } from '../komponen/profesi'
import { Avatar, Batang, Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

export default function Explore() {
  const { id = '' } = useParams()
  const { data, galat, muat } = useData(() => ambilHasil(id), id)
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-md flex-1 p-6">
          <Galat pesan={galat ?? 'Hasil tidak ditemukan.'} />
          <Link to="/mulai" className="mt-4 inline-flex items-center gap-2 rounded-full bg-violet-600 px-5 py-3 text-[13.5px] font-semibold text-white">Isi kuesioner <ArrowRight className="size-4" aria-hidden /></Link>
        </div>
      ) : <Isi id={id} d={data} />}
      <AppBottomNav id={id} />
    </div>
  )
}

function Isi({ id, d }: { id: string; d: Hasil }) {
  const h = d.hasil
  const n = h.rekomendasi.length
  const alasan = new Map(h.rekomendasi.map((r) => [r.profesi_id, r.alasan.find((a) => a.nada === 'cocok')?.teks ?? r.alasan[0]?.teks]))
  const alpha = h.konfigurasi.alpha.toLocaleString('id-ID')
  const beta = (1 - h.konfigurasi.alpha).toLocaleString('id-ID', { maximumFractionDigits: 1 })

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-1 flex-col lg:flex-row lg:items-start lg:gap-8 lg:px-8 lg:py-8">
      <div className="bg-[#E7EAF2] px-4 py-5 sm:px-6 lg:sticky lg:top-24 lg:w-[380px] lg:shrink-0 lg:rounded-2xl lg:px-5">
        <div className="flex flex-col gap-4">
          <Sapaan id={id} d={d} />
          {d.target ? <KartuTarget id={id} t={d.target} /> : n > 0 && (
            <Banner
              ke={`/explore/${id}/roadmap`} gambar="/ilustrasi/banner-tujuan.webp" gambarLebar="/ilustrasi/banner-tujuan-lebar.webp"
              eyebrow="Profesi Tujuan" judul="Sudah ada yang menarik?"
              isi="Pilih satu profesi sebagai tujuan, lalu lihat skill apa yang perlu dikejar." tombol="Susun Roadmap"
            />
          )}

          <section className="rounded-2xl bg-white p-4">
            <p className="text-[12px] font-bold text-violet-600">Profil Kariermu</p>
            <p className="mt-1 text-[22px] font-bold tracking-[0.12em] text-slate-900">{h.kode_holland}</p>
            <p className="text-[12.5px] leading-relaxed text-slate-500">{[...h.kode_holland].map((c) => NAMA_RIASEC[c]).join(' · ')}</p>
            <Link to={`/explore/${id}/profil`} className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-violet-700 hover:text-violet-800">
              Lihat profil lengkap <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          </section>

          <Banner
            ke={`/explore/${id}/penilaian`} gambar="/ilustrasi/banner.webp" gambarLebar="/ilustrasi/banner-lebar.webp"
            eyebrow="Penilaian Sistem" judul={d.skor_sus === null ? 'Bantu penelitian ini' : 'Terima kasih!'}
            isi={d.skor_sus === null ? 'Nilai kemudahan penggunaan sistem lewat 10 pertanyaan singkat.' : 'Penilaianmu sudah tersimpan. Kamu masih bisa mengubahnya.'}
            tombol={d.skor_sus === null ? 'Isi Penilaian' : 'Ubah Penilaian'}
          />
        </div>
      </div>

      <main className="min-w-0 flex-1">
        {n === 0 ? (
          <div className="p-4 sm:p-6"><Galat pesan="Tidak ada profesi yang lolos penyaringan dengan syarat yang kamu isi. Coba ubah pendidikan atau kesediaan relokasi." /></div>
        ) : (
          <BarisKartu judul="Persentase Match Profesi" keterangan={`${n} profesi teratas untukmu. Skor akhir = ${alpha} × kecocokan profil (KBF) + ${beta} × kemiripan skill (CBF).`}>
            {h.peringkat_lengkap.slice(0, n).map((p) => <KartuProfesi key={p.profesi_id} id={id} p={p} alasan={alasan.get(p.profesi_id)} />)}
          </BarisKartu>
        )}

        {h.peringkat_lengkap.length > n && (
          <BarisKartu judul="Profesi TI Lainnya" keterangan={`Peringkat ${n + 1} sampai ${h.peringkat_lengkap.length}, diurutkan dari skor tertinggi.`}>
            {h.peringkat_lengkap.slice(n).map((p) => <KartuProfesi key={p.profesi_id} id={id} p={p} tampilDeskripsi />)}
          </BarisKartu>
        )}

        {h.tersaring.length > 0 && (
          <section className="px-4 py-5 sm:px-6">
            <h2 className="text-[17px] font-bold tracking-tight text-slate-900">Tidak Diikutkan</h2>
            <p className="mt-0.5 text-[13px] leading-relaxed text-slate-500">{h.tersaring.length} profesi disaring karena syarat mutlaknya tidak terpenuhi.</p>
            <ul className="mt-4 flex flex-col gap-2.5">
              {h.tersaring.map((t) => (
                <li key={t.profesi_id}>
                  <Link to={`/explore/${id}/profesi/${t.profesi_id}`} className="flex items-start gap-2.5 rounded-xl border border-slate-200 px-4 py-3 transition-colors hover:border-slate-300">
                    <span className="mt-0.5 grid size-[18px] shrink-0 place-items-center rounded-full border border-amber-500 text-amber-600" aria-hidden><Info className="size-3" /></span>
                    <span className="min-w-0">
                      <span className="block text-[13.5px] font-semibold text-slate-900">{t.nama}</span>
                      <span className="block text-[12.5px] leading-relaxed text-slate-500">{t.alasan.map((a) => a.pesan).join(' ')}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  )
}

function Sapaan({ id, d }: { id: string; d: Hasil }) {
  const [q, setQ] = useState('')
  const semua = useMemo(
    () => [
      ...d.hasil.peringkat_lengkap.map((p) => ({ id: p.profesi_id, nama: p.nama, ket: p.sektor })),
      ...d.hasil.tersaring.map((t) => ({ id: t.profesi_id, nama: t.nama, ket: 'Tidak diikutkan' })),
    ],
    [d],
  )
  const kata = q.trim().toLowerCase()
  const temuan = kata.length < 2 ? [] : semua.filter((p) => p.nama.toLowerCase().includes(kata) || p.ket.toLowerCase().includes(kata)).slice(0, 8)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[17px] font-bold tracking-tight text-slate-900">Halo, {d.nama.split(' ')[0]}</p>
          <p className="mt-0.5 text-[12.5px] text-slate-500">Ini profesi TI yang paling cocok dengan profilmu.</p>
        </div>
        <Link to={`/explore/${id}/profil`} aria-label="Buka profil" className="shrink-0 rounded-full transition-transform hover:scale-105">
          <Avatar nama={d.nama} />
        </Link>
      </div>
      <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <label htmlFor="cari-profesi" className="sr-only">Cari profesi TI</label>
        <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
        <input id="cari-profesi" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari profesi TI.."
          className="w-full rounded-full border border-slate-200 bg-white py-3 pl-11 pr-4 text-[13.5px] text-slate-900 outline-none placeholder:text-slate-400 focus:border-violet-400" />
        {kata.length >= 2 && (
          <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-20 max-h-80 overflow-y-auto rounded-2xl border border-slate-200 bg-white py-1 shadow-lg">
            {temuan.length === 0 ? (
              <p className="px-4 py-3 text-[13px] text-slate-400">Tidak ada profesi yang cocok dengan “{q.trim()}”.</p>
            ) : temuan.map((p) => (
              <Link key={p.id} to={`/explore/${id}/profesi/${p.id}`} className="block px-4 py-2.5 transition-colors hover:bg-slate-50">
                <span className="block text-[13.5px] font-medium text-slate-900">{p.nama}</span>
                <span className="block text-[12px] text-slate-500">{p.ket}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
      <Link to={`/explore/${id}/cari`} aria-label="Cari dengan filter" className="grid size-11 shrink-0 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50">
        <SlidersHorizontal className="size-4" aria-hidden />
      </Link>
      </div>
    </div>
  )
}

/** Kartu profesi tujuan: kemajuan roadmap dan cakupan skill saat ini. */
function KartuTarget({ id, t }: { id: string; t: RingkasTarget }) {
  const { selesai, total } = t.progres
  const bagian = total === 0 ? 1 : selesai / total
  return (
    <Link to={`/explore/${id}/roadmap`} className="block rounded-2xl bg-violet-600 p-4 text-white transition-colors hover:bg-violet-700">
      <p className="flex items-center gap-1.5 text-[12px] font-bold text-violet-200"><Target className="size-3.5" aria-hidden /> Profesi Tujuanmu</p>
      <p className="mt-1 text-[17px] font-bold leading-snug tracking-tight">{t.nama}</p>
      <div className="mt-3 flex items-baseline justify-between text-[12.5px] text-violet-100">
        <span>{total === 0 ? 'Semua skill sudah dikuasai' : `${selesai} dari ${total} skill dipelajari`}</span>
        {t.proyeksi && <span className="font-semibold text-white">Cakupan {persen(t.proyeksi.cakupan)}</span>}
      </div>
      <div className="mt-1.5"><Batang nilai={bagian} warna="bg-white" alas="bg-violet-400/60" /></div>
      <span className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] font-semibold">Lanjutkan roadmap <ArrowRight className="size-3.5" aria-hidden /></span>
    </Link>
  )
}

function Banner({ ke, gambar, gambarLebar, eyebrow, judul, isi, tombol }: {
  ke: string; gambar: string; gambarLebar: string; eyebrow: string; judul: string; isi: string; tombol: string
}) {
  return (
    <Link to={ke} style={{ backgroundColor: '#EFEBFB' }} className="group relative block min-h-[180px] overflow-hidden rounded-2xl transition-opacity hover:opacity-95">
      <div className="absolute inset-0 bg-cover bg-right-bottom bg-no-repeat sm:hidden lg:block" style={{ backgroundImage: `url('${gambar}')` }} aria-hidden />
      <div className="absolute inset-0 hidden bg-cover bg-right-bottom bg-no-repeat sm:block lg:hidden" style={{ backgroundImage: `url('${gambarLebar}')` }} aria-hidden />
      <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #EFEBFB, #EFEBFBd9 55%, transparent)' }} aria-hidden />
      <div className="relative flex max-w-[76%] flex-col gap-1.5 p-5 sm:max-w-[58%]">
        <p className="text-[12px] font-bold text-violet-600">{eyebrow}</p>
        <h3 className="text-[18px] font-bold leading-tight tracking-tight text-slate-900">{judul}</h3>
        <p className="text-[12.5px] leading-relaxed text-slate-600">{isi}</p>
        <span className="mt-3 inline-flex w-fit items-center gap-2 whitespace-nowrap rounded-full bg-violet-600 px-4 py-2 text-[12px] font-semibold text-white transition-colors group-hover:bg-violet-700">
          {tombol} <ArrowRight className="size-3.5" aria-hidden />
        </span>
      </div>
    </Link>
  )
}
