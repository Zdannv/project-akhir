/**
 * Navigasi aplikasi: bar atas di desktop, bar bawah di ponsel dan tablet.
 * Daftar tujuannya ditulis sekali supaya kedua bentuk tidak berbeda isi.
 */
import { ClipboardCheck, Compass, UserRound } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { Lambang } from './umum'

function tujuan(id: string) {
  return [
    { href: `/explore/${id}`, label: 'Explore', icon: Compass, persis: true },
    { href: `/explore/${id}/penilaian`, label: 'Penilaian', icon: ClipboardCheck, persis: false },
    { href: `/explore/${id}/profil`, label: 'Profil', icon: UserRound, persis: false },
  ]
}

function aktif(pathname: string, href: string, persis: boolean): boolean {
  // Detail profesi berada di bawah Explore.
  return persis ? pathname === href || pathname.startsWith(`${href}/profesi`) : pathname.startsWith(href)
}

export function AppTopNav({ id }: { id: string }) {
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-30 hidden border-b border-slate-200 bg-white/95 backdrop-blur lg:block">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-6 px-8">
        <Link to={`/explore/${id}`} className="flex items-center gap-3">
          <Lambang className="h-7 w-[21px] shrink-0 text-violet-600" />
          <span className="h-6 w-px bg-slate-200" aria-hidden />
          <span className="leading-tight">
            <span className="block text-[13px] font-semibold text-slate-900">Rekomendasi Profesi TI</span>
            <span className="block text-[11px] text-slate-400">Hybrid Filtering</span>
          </span>
        </Link>
        <nav aria-label="Navigasi utama" className="ml-auto flex items-center gap-1">
          {tujuan(id).map(({ href, label, persis }) => {
            const on = aktif(pathname, href, persis)
            return (
              <Link
                key={href} to={href} aria-current={on ? 'page' : undefined}
                className={`rounded-full px-4 py-2 text-[14px] transition-colors ${
                  on ? 'border border-violet-300 font-semibold text-violet-700' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {label}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}

export function AppBottomNav({ id }: { id: string }) {
  const { pathname } = useLocation()
  return (
    <nav
      aria-label="Navigasi utama"
      className="sticky bottom-0 z-30 border-t border-slate-200 bg-[#EDEBFA] lg:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <ul className="mx-auto flex max-w-2xl items-stretch">
        {tujuan(id).map(({ href, label, icon: Ikon, persis }) => {
          const on = aktif(pathname, href, persis)
          return (
            <li key={href} className="flex-1">
              <Link
                to={href} aria-current={on ? 'page' : undefined}
                className={`flex flex-col items-center gap-1 py-2.5 text-[11px] transition-colors ${
                  on ? 'font-semibold text-violet-700' : 'text-slate-500'
                }`}
              >
                <Ikon className="size-5" aria-hidden />
                {label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

/** Bar atas layar turunan: panah kembali dan dua baris judul. */
export function KepalaLayar({ ke, judul, subjudul }: { ke: string; judul: string; subjudul?: string }) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur lg:top-16">
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link to={ke} aria-label="Kembali" className="-ml-1 rounded-full p-1.5 text-slate-700 transition-colors hover:bg-slate-100">
          <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="m12 19-7-7 7-7" /><path d="M19 12H5" />
          </svg>
        </Link>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-[14px] font-semibold text-slate-900">{judul}</p>
          {subjudul && <p className="truncate text-[12px] text-slate-400">{subjudul}</p>}
        </div>
      </div>
    </header>
  )
}
