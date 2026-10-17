import { ArrowRight, PencilLine } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ambilHasil, NAMA_RIASEC, persen, rupiah } from '../api'
import { AppBottomNav, AppTopNav, KepalaLayar } from '../komponen/AppNav'
import { Avatar, Batang, Galat, Memuat, Radar } from '../komponen/umum'
import { useData } from '../komponen/useData'

export default function Profil() {
  const { id = '' } = useParams()
  const { data, galat, muat } = useData(() => ambilHasil(id), id)
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      <KepalaLayar ke={`/explore/${id}`} judul="Profil" />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-2xl flex-1 p-6"><Galat pesan={galat ?? 'Profil tidak ditemukan.'} /></div>
      ) : (
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-12 pt-6 sm:px-6">
          <div className="flex flex-col items-center text-center">
            <Avatar nama={data.nama} className="size-24 text-[30px]" />
            <h1 className="mt-3 text-[19px] font-bold tracking-tight text-slate-900">{data.nama}</h1>
            <p className="text-[13px] text-slate-500">{data.jenis === 'profesional' ? 'Profesional TI' : 'Mahasiswa / pencari kerja'}</p>
          </div>

          <Kartu judul="Latar Belakang">
            <dl>
              {([
                ['Pendidikan', data.data_diri.jenjang],
                ['Program studi', data.data_diri.prodi ?? '—'],
                ['Domisili', data.data_diri.domisili],
                ['Bersedia relokasi', data.data_diri.bersedia_relokasi ? 'Ya' : 'Tidak'],
                ['Pengalaman di TI', data.data_diri.pengalaman_tahun === null ? 'Tidak diisi' : data.data_diri.pengalaman_tahun === 0 ? 'Belum ada' : `± ${data.data_diri.pengalaman_tahun.toLocaleString('id-ID')} tahun`],
                ['Ekspektasi gaji', data.data_diri.ekspektasi_gaji ? `${rupiah(data.data_diri.ekspektasi_gaji)}/bulan` : 'Tidak diisi'],
                ['Menanggung keluarga', data.data_diri.punya_tanggungan ? 'Ya' : 'Tidak'],
              ] as const).map(([k, v]) => (
                <div key={k} className="flex items-start justify-between gap-4 border-b border-slate-200 py-3 last:border-b-0">
                  <dt className="text-[13px] text-slate-500">{k}</dt>
                  <dd className="text-right text-[13.5px] font-semibold text-slate-900">{v}</dd>
                </div>
              ))}
            </dl>
          </Kartu>

          <Kartu judul="Minat (RIASEC)" kanan={<span className="rounded-md bg-violet-600 px-2 py-1 text-[11px] font-bold tracking-widest text-white">{data.hasil.kode_holland}</span>}>
            <Radar sumbu={[...'RIASEC'].map((t) => ({ kode: t, nama: NAMA_RIASEC[t] }))} kamu={data.hasil.profil.riasec} />
            <div className="mt-4"><Skor nama={NAMA_RIASEC} nilai={data.hasil.profil.riasec} urut="RIASEC" /></div>
          </Kartu>
          {data.data_diri.bidang && (
            <Kartu judul="Minat bidang TI">
              <div className="flex flex-col gap-3">
                {Object.entries(data.data_diri.bidang).sort((a, b) => b[1] - a[1]).map(([nama, v]) => (
                  <div key={nama}>
                    <div className="mb-1.5 flex justify-between text-[13px]">
                      <span className="text-slate-700">{nama}</span>
                      <span className="font-semibold tabular-nums text-slate-900">{persen(v)}</span>
                    </div>
                    <Batang nilai={v} />
                  </div>
                ))}
              </div>
            </Kartu>
          )}
          <Kartu judul="Keahlian" kanan={<span className="text-[12.5px] text-slate-400">{data.data_diri.skill.length} skill</span>}>
            {data.data_diri.skill.length === 0 ? (
              <p className="text-[13px] text-slate-400">Belum ada skill yang dipilih.</p>
            ) : (
              <ul className="flex flex-wrap gap-2">
                {data.data_diri.skill.map((s) => (
                  <li key={s.nama} className="rounded-full bg-[#F1EBFF] px-3 py-1.5 text-[12.5px] font-medium text-[#7033FF] ring-1 ring-[#DDD0FF]">
                    {s.nama} <span className="opacity-70">· {s.tingkat}</span>
                  </li>
                ))}
              </ul>
            )}
            {data.data_diri.skill_lain.length > 0 && (
              <>
                <p className="mt-4 text-[12px] leading-relaxed text-slate-500">Skill lain yang kamu tambahkan (dicatat, belum ikut dihitung dalam skor):</p>
                <ul className="mt-2 flex flex-wrap gap-2">
                  {data.data_diri.skill_lain.map((s) => (
                    <li key={s} className="rounded-full bg-slate-100 px-3 py-1.5 text-[12.5px] font-medium text-slate-700">{s}</li>
                  ))}
                </ul>
              </>
            )}
          </Kartu>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link to={`/mulai?dari=${id}`} className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-slate-100 px-5 py-3 text-[13.5px] font-semibold text-slate-700 transition-colors hover:bg-slate-200">
              <PencilLine className="size-4" aria-hidden /> Ubah jawaban
            </Link>
            <Link to={`/explore/${id}`} className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-violet-600 px-5 py-3 text-[13.5px] font-semibold text-white transition-colors hover:bg-violet-700">
              Lihat rekomendasi <ArrowRight className="size-4" aria-hidden />
            </Link>
          </div>
        </main>
      )}
      <AppBottomNav id={id} />
    </div>
  )
}

function Kartu({ judul, kanan, children }: { judul: string; kanan?: ReactNode; children: ReactNode }) {
  return (
    <section className="mt-5 rounded-2xl border border-slate-200 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-[15px] font-semibold text-slate-900">{judul}</h2>
        {kanan}
      </div>
      {children}
    </section>
  )
}

function Skor({ nama, nilai, urut }: { nama: Record<string, string>; nilai: Record<string, number>; urut: string }) {
  return (
    <div className="flex flex-col gap-3">
      {[...urut].map((k) => (
        <div key={k}>
          <div className="mb-1.5 flex justify-between text-[13px]">
            <span className="text-slate-700">{nama[k]}</span>
            <span className="font-semibold tabular-nums text-slate-900">{persen(nilai[k])}</span>
          </div>
          <Batang nilai={nilai[k]} />
        </div>
      ))}
    </div>
  )
}
