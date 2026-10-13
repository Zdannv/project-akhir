/**
 * Bahan belajar: sumber per skill, peta belajar dan proyek per profesi, serta
 * tautan lowongan.
 *
 * Dua jenis tautan dibedakan dengan sengaja:
 *   - sumber kurasi  : dokumentasi resmi dan kursus gratis, disimpan di basis
 *                      pengetahuan dan sudah diperiksa bisa dibuka;
 *   - tautan cari    : pencarian YouTube dan Coursera yang dirakit dari nama
 *                      skill. Isinya berubah-ubah, jadi tidak pernah "mati",
 *                      dan selalu tersedia walau skill-nya belum punya kurasi.
 */
import { BookOpen, Briefcase, ChevronDown, ExternalLink, GraduationCap, Hammer, Map, MonitorPlay, Search } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import type { Proyek, Sumber } from '../api'

const IKON = { dokumentasi: BookOpen, kursus: GraduationCap, latihan: Hammer, panduan: BookOpen } as const
const LABEL = { dokumentasi: 'Dokumentasi', kursus: 'Kursus', latihan: 'Latihan', panduan: 'Panduan' } as const

/** "CI/CD (Jenkins, GitHub Actions)" -> "CI/CD": kata kunci cari yang ringkas. */
const kunci = (nama: string) => nama.replace(/\s*\(.*\)\s*/g, ' ').trim()

const tautanYoutube = (nama: string) =>
  `https://www.youtube.com/results?search_query=${encodeURIComponent(`tutorial ${kunci(nama)} bahasa indonesia`)}`
const tautanKursus = (nama: string) =>
  `https://www.coursera.org/search?query=${encodeURIComponent(kunci(nama))}`

function Tautan({ href, ikon, judul, ket }: { href: string; ikon: ReactNode; judul: string; ket: string }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer"
      className="group flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 transition-colors hover:border-violet-300 hover:bg-violet-50/40">
      <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-violet-50 text-violet-600">{ikon}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[13px] font-semibold text-slate-900">{judul}</span>
        <span className="block truncate text-[11.5px] text-slate-500">{ket}</span>
      </span>
      <ExternalLink className="size-3.5 shrink-0 text-slate-400 group-hover:text-violet-600" aria-hidden />
    </a>
  )
}

/** Daftar sumber belajar satu skill. */
export function SumberBelajar({ nama, belajar }: { nama: string; belajar: Sumber[] }) {
  return (
    <div className="flex flex-col gap-2">
      {belajar.map((b) => {
        const Ikon = IKON[b.jenis] ?? BookOpen
        return <Tautan key={b.url} href={b.url} ikon={<Ikon className="size-4" aria-hidden />} judul={b.judul} ket={`${LABEL[b.jenis] ?? 'Sumber'} gratis · ${b.penyedia}`} />
      })}
      <Tautan href={tautanYoutube(nama)} ikon={<MonitorPlay className="size-4" aria-hidden />} judul="Cari video tutorial" ket="YouTube · berbahasa Indonesia" />
      <Tautan href={tautanKursus(nama)} ikon={<Search className="size-4" aria-hidden />} judul="Cari kursus" ket="Coursera · sebagian bisa diaudit gratis" />
    </div>
  )
}

/** Hook: tombol "Belajar" dan panel sumber belajar untuk satu baris skill. */
export function useBelajar({ nama, belajar }: { nama: string; belajar: Sumber[] }) {
  const [buka, setBuka] = useState(false)
  return {
    tombol: (
      <button type="button" aria-expanded={buka} onClick={() => setBuka((v) => !v)}
        className="inline-flex shrink-0 items-center gap-1 rounded-full bg-violet-50 px-2.5 py-1.5 text-[12px] font-semibold text-violet-700 transition-colors hover:bg-violet-100">
        <BookOpen className="size-3.5" aria-hidden /> Belajar
        <ChevronDown className={`size-3.5 transition-transform ${buka ? 'rotate-180' : ''}`} aria-hidden />
      </button>
    ),
    isi: buka ? <div className="mt-2.5"><SumberBelajar nama={nama} belajar={belajar} /></div> : null,
  }
}

/** Peta belajar profesi (roadmap.sh), kalau ada. */
export function PetaBelajar({ peta }: { peta: { judul: string; url: string } | null }) {
  if (!peta) return null
  return <Tautan href={peta.url} ikon={<Map className="size-4" aria-hidden />} judul={peta.judul} ket="Peta belajar langkah demi langkah · roadmap.sh" />
}

/** Ide proyek portofolio. */
export function DaftarProyek({ proyek }: { proyek: Proyek[] }) {
  if (proyek.length === 0) return null
  return (
    <ul className="flex flex-col gap-2.5">
      {proyek.map((p) => (
        <li key={p.judul} className="rounded-2xl border border-slate-200 px-4 py-3.5">
          <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${p.tingkat === 'Pemula' ? 'bg-emerald-50 text-emerald-700' : 'bg-sky-50 text-sky-700'}`}>{p.tingkat}</span>
          <p className="mt-1.5 text-[13.5px] font-semibold leading-snug text-slate-900">{p.judul}</p>
          <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">{p.deskripsi}</p>
        </li>
      ))}
    </ul>
  )
}

/** Tautan pencarian lowongan untuk sebuah profesi. */
export function CariLowongan({ nama }: { nama: string }) {
  const q = kunci(nama).split('/')[0].trim()
  const slug = q.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  const situs = [
    ['LinkedIn', `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(q)}&location=Indonesia`],
    ['Jobstreet', `https://id.jobstreet.com/id/${slug}-jobs`],
    ['Glints', `https://glints.com/id/opportunities/jobs/explore?keyword=${encodeURIComponent(q)}&country=ID`],
  ]
  return (
    <ul className="flex flex-wrap gap-2">
      {situs.map(([s, url]) => (
        <li key={s}>
          <a href={url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-2 text-[13px] font-semibold text-slate-700 transition-colors hover:border-violet-300 hover:text-violet-700">
            <Briefcase className="size-3.5" aria-hidden /> {s} <ExternalLink className="size-3 text-slate-400" aria-hidden />
          </a>
        </li>
      ))}
    </ul>
  )
}
