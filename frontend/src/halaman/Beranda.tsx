import { ArrowRight, ListChecks, ScanSearch, Sparkles, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Lambang } from '../komponen/umum'
import { hasilTerakhir } from '../sesi'

const TAHAP = [
  { ikon: ListChecks, nama: 'Profiling', isi: 'Isi latar belakang, minat (RIASEC), kepribadian (Big Five), dan skill yang sudah kamu kuasai.' },
  { ikon: ScanSearch, nama: 'Matching', isi: 'Profilmu dicocokkan dengan 35 profesi TI: aturan dan kecocokan psikologis (KBF) digabung dengan kemiripan skill (CBF).' },
  { ikon: Target, nama: 'Rekomendasi', isi: 'Dapatkan lima profesi teratas, alasan di balik skornya, dan skill yang masih perlu dikejar.' },
]

export default function Beranda() {
  const terakhir = hasilTerakhir()
  return (
    <div className="min-h-screen w-full bg-white text-slate-900">
      <header className="border-b border-slate-200 bg-white/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
          <Lambang className="h-7 w-[21px] shrink-0 text-violet-600" />
          <span className="h-6 w-px bg-slate-200" aria-hidden />
          <span className="leading-tight">
            <span className="block text-[13px] font-semibold text-slate-900">Rekomendasi Profesi TI</span>
            <span className="block text-[11px] text-slate-400">Hybrid Filtering</span>
          </span>
          {terakhir && (
            <Link to={`/explore/${terakhir}`} className="ml-auto rounded-full border border-violet-300 px-4 py-2 text-[13px] font-semibold text-violet-700 hover:bg-violet-50">
              Buka hasil terakhir
            </Link>
          )}
        </div>
      </header>

      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50 via-purple-50/60 to-white">
        <div className="pointer-events-none absolute right-0 top-0 h-[36rem] w-[36rem] -translate-y-1/4 translate-x-1/4 rounded-full bg-gradient-to-br from-purple-300/50 via-indigo-300/40 to-transparent blur-3xl" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 sm:py-20 lg:grid-cols-2 lg:px-8">
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-1.5 rounded-full border border-indigo-100 bg-white px-3 py-1 text-xs font-bold text-indigo-600 shadow-sm">
              <Sparkles className="size-3.5" aria-hidden />
              Sistem Rekomendasi Profesi Bidang TI
            </div>
            <h1 className="mt-5 text-3xl font-bold leading-tight tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
              Temukan profesi TI yang paling <span className="text-violet-600">cocok</span> untukmu
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-slate-600 lg:mx-0">
              Minat, kepribadian, dan kondisi pribadimu dipertimbangkan bersama skill yang sudah kamu miliki,
              dengan pendekatan hybrid knowledge-based dan content-based filtering.
            </p>
            <div className="mt-7 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start">
              <Link to="/mulai" className="inline-flex items-center justify-center gap-2 rounded-full bg-violet-600 px-6 py-3.5 text-[14px] font-semibold text-white transition-colors hover:bg-violet-700">
                Mulai Sekarang <ArrowRight className="size-4" aria-hidden />
              </Link>
              <span className="text-[13px] text-slate-500">±7 menit · tanpa perlu akun</span>
            </div>
          </div>
          <img src="/landing/hero-roadmap.webp" alt="" width={997} height={1240} className="mx-auto h-auto w-full max-w-[420px]" aria-hidden />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-20 pt-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-slate-900">Cara kerjanya</h2>
        <ol className="mt-8 grid gap-4 md:grid-cols-3">
          {TAHAP.map(({ ikon: Ikon, nama, isi }, i) => (
            <li key={nama} className="rounded-2xl border border-slate-200 bg-white p-6">
              <span className="grid size-11 place-items-center rounded-xl bg-violet-50 text-violet-600">
                <Ikon className="size-5" aria-hidden />
              </span>
              <p className="mt-4 text-[12px] font-bold text-violet-600">TAHAP {i + 1}</p>
              <h3 className="mt-0.5 text-[17px] font-bold text-slate-900">{nama}</h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-slate-600">{isi}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
