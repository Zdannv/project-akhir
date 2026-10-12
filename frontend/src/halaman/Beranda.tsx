import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Kerangka, kartu, tombolUtama } from '../komponen/umum'

const LANGKAH = [
  ['Profiling', 'Kamu mengisi data diri, kuesioner minat (RIASEC), kepribadian (Big Five), dan skill yang dikuasai.'],
  ['Matching', 'Profilmu dicocokkan dengan 35 profesi TI: aturan dan kecocokan psikologis (KBF) digabung dengan kemiripan skill (CBF).'],
  ['Rekomendasi', 'Kamu mendapat lima profesi teratas, alasan di balik tiap skor, dan skill yang masih perlu dikejar.'],
]

export default function Beranda() {
  return (
    <Kerangka>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">
        Profesi TI mana yang paling cocok untukmu?
      </h1>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-slate-600">
        Sistem ini merekomendasikan profesi bidang teknologi informasi dengan pendekatan hybrid filtering:
        minat, kepribadian, dan kondisi pribadimu dipertimbangkan bersama skill yang sudah kamu miliki.
        Pengisian butuh sekitar 7 menit.
      </p>
      <Link to="/kuesioner" className={`${tombolUtama} mt-6`}>
        Mulai <ArrowRight className="size-4" aria-hidden />
      </Link>

      <ol className="mt-10 grid gap-4 sm:grid-cols-3">
        {LANGKAH.map(([judul, isi], i) => (
          <li key={judul} className={kartu}>
            <p className="text-xs font-semibold text-teal-700">TAHAP {i + 1}</p>
            <h2 className="mt-1 font-semibold text-slate-900">{judul}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{isi}</p>
          </li>
        ))}
      </ol>
    </Kerangka>
  )
}
