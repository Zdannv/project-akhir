/**
 * Explore: blok sapaan dan pencarian di kiri, deretan kartu rekomendasi di
 * kanan. Baris pertama adalah lima teratas hasil hybrid filtering; baris kedua
 * sisanya, supaya pengguna bisa membandingkan.
 */
import { ArrowRight, Info, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ambilHasil, NAMA_RIASEC, type Hasil } from '../api'
import { AppBottomNav, AppTopNav } from '../komponen/AppNav'
import { BarisKartu, KartuProfesi } from '../komponen/profesi'
import { Galat, Memuat } from '../komponen/umum'
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

          <section className="rounded-2xl bg-white p-4">
            <p className="text-[12px] font-bold text-violet-600">Career DNA-mu</p>
            <p className="mt-1 text-[22px] font-bold tracking-[0.12em] text-slate-900">{h.kode_holland}</p>
            <p className="text-[12.5px] leading-relaxed text-slate-500">{[...h.kode_holland].map((c) => NAMA_RIASEC[c]).join(' · ')}</p>
            <Link to={`/explore/${id}/profil`} className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-violet-700 hover:text-violet-800">
              Lihat profil lengkap <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          </section>

          <Link to={`/explore/${id}/penilaian`} style={{ backgroundColor: '#EFEBFB' }} className="group relative block min-h-[180px] overflow-hidden rounded-2xl transition-opacity hover:opacity-95">
            <div className="absolute inset-0 bg-cover bg-right-bottom bg-no-repeat sm:hidden lg:block" style={{ backgroundImage: "url('/explore/dna-art.webp')" }} aria-hidden />
            <div className="absolute inset-0 hidden bg-cover bg-right-bottom bg-no-repeat sm:block lg:hidden" style={{ backgroundImage: "url('/explore/dna-art-wide.webp')" }} aria-hidden />
            <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #EFEBFB, #EFEBFBd9 55%, transparent)' }} aria-hidden />
            <div className="relative flex max-w-[76%] flex-col gap-1.5 p-5 sm:max-w-[58%]">
              <p className="text-[12px] font-bold text-violet-600">Penilaian Sistem</p>
              <h3 className="text-[18px] font-bold leading-tight tracking-tight text-slate-900">
                {d.skor_sus === null ? 'Bantu penelitian ini' : 'Terima kasih!'}
              </h3>
              <p className="text-[12.5px] leading-relaxed text-slate-600">
                {d.skor_sus === null ? 'Nilai kemudahan penggunaan sistem lewat 10 pertanyaan singkat.' : 'Penilaianmu sudah tersimpan. Kamu masih bisa mengubahnya.'}
              </p>
              <span className="mt-3 inline-flex w-fit items-center gap-2 whitespace-nowrap rounded-full bg-violet-600 px-4 py-2 text-[12px] font-semibold text-white transition-colors group-hover:bg-violet-700">
                {d.skor_sus === null ? 'Isi Penilaian' : 'Ubah Penilaian'} <ArrowRight className="size-3.5" aria-hidden />
              </span>
            </div>
          </Link>
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
          <img src="/avatar-default.webp" alt="" width={40} height={40} className="size-10 rounded-full object-cover" />
        </Link>
      </div>
      <div className="relative">
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
    </div>
  )
}
