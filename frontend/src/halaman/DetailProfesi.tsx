import { ArrowLeft, Check, X } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ambilDetail, NAMA_BIG5, NAMA_RIASEC, persen, rupiah, type Detail, type SkillProfesi } from '../api'
import { Batang, Galat, Kerangka, Memuat, kartu, useData } from '../komponen/umum'

const TAB = ['Kecocokan', 'Skill', 'Tentang profesi'] as const
type Tab = (typeof TAB)[number]

const NAMA_KOMPONEN = {
  riasec: 'Kongruensi minat (RIASEC)',
  big5: 'Kecocokan kepribadian (Big Five)',
  finansial: 'Kecocokan finansial',
  stabilitas: 'Stabilitas kerja',
} as const

export default function DetailProfesi() {
  const { id = '', pid = '' } = useParams()
  const { data, galat, muat } = useData(() => ambilDetail(id, pid), `${id}/${pid}`)
  const [tab, setTab] = useState<Tab>('Kecocokan')
  if (muat) return <Kerangka><Memuat /></Kerangka>
  if (galat || !data) return <Kerangka><Galat pesan={galat ?? 'Profesi tidak ditemukan.'} /></Kerangka>
  const p = data.profesi

  return (
    <Kerangka>
      <Link to={`/hasil/${id}`} className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden /> Kembali ke hasil
      </Link>
      <p className="mt-4 text-xs font-semibold text-teal-700">{p.sektor} · {p.senioritas}</p>
      <h1 className="mt-0.5 text-2xl font-bold text-slate-900">{p.nama}</h1>
      {data.ringkas && (
        <p className="mt-1 text-sm text-slate-600">
          Peringkat {data.ringkas.peringkat} untukmu · skor akhir <strong className="text-slate-900">{persen(data.ringkas.skor)}</strong>
        </p>
      )}
      {data.tersaring && (
        <div className="mt-3"><Galat pesan={`Tidak diikutkan dalam peringkat: ${data.tersaring.alasan.map((a) => a.pesan).join(' ')}`} /></div>
      )}

      <div role="tablist" className="mt-5 flex gap-1 border-b border-slate-200">
        {TAB.map((t) => (
          <button key={t} type="button" role="tab" aria-selected={t === tab} onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${t === tab ? 'border-teal-700 font-semibold text-teal-800' : 'border-transparent text-slate-600 hover:text-slate-900'}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="mt-5 space-y-4">
        {tab === 'Kecocokan' && <TabKecocokan d={data} />}
        {tab === 'Skill' && <TabSkill d={data} />}
        {tab === 'Tentang profesi' && <TabTentang d={data} />}
      </div>
    </Kerangka>
  )
}

function TabKecocokan({ d }: { d: Detail }) {
  const p = d.profesi
  const n = d.penilaian
  return (
    <>
      {n ? (
        <section className={kartu}>
          <h2 className="font-semibold text-slate-900">Rincian skor</h2>
          <p className="mt-1 text-sm text-slate-600">
            KBF {persen(n.kbf.skor)} dan CBF {persen(n.cbf.skor)} digabung menjadi skor akhir {persen(n.skor)}.
          </p>
          <dl className="mt-4 space-y-3">
            {(Object.keys(NAMA_KOMPONEN) as (keyof typeof NAMA_KOMPONEN)[]).map((k) => (
              <div key={k} className={n.kbf.bobot[k] === 0 ? 'opacity-50' : ''}>
                <div className="mb-1 flex justify-between text-sm">
                  <dt className="text-slate-700">{NAMA_KOMPONEN[k]} <span className="text-xs text-slate-500">· bobot {persen(n.kbf.bobot[k])}</span></dt>
                  <dd className="tabular-nums text-slate-900">{persen(n.kbf.komponen[k])}</dd>
                </div>
                <Batang nilai={n.kbf.komponen[k]} />
              </div>
            ))}
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <dt className="text-slate-700">Kemiripan skill (cosine)</dt>
                <dd className="tabular-nums text-slate-900">{persen(n.cbf.skor)}</dd>
              </div>
              <Batang nilai={n.cbf.skor} warna="bg-indigo-500" />
            </div>
          </dl>
        </section>
      ) : d.ringkas && (
        <section className={kartu}>
          <p className="text-sm text-slate-700">
            Profesi ini di luar lima teratasmu: KBF {persen(d.ringkas.skor_kbf)}, CBF {persen(d.ringkas.skor_cbf)}, skor akhir {persen(d.ringkas.skor)}.
          </p>
        </section>
      )}

      <section className={kartu}>
        <h2 className="font-semibold text-slate-900">Minat: kamu ({d.kode_holland_pengguna}) dan profesi ini ({p.kode_holland})</h2>
        <Banding
          baris={[...'RIASEC'].map((t) => ({ nama: NAMA_RIASEC[t], kamu: d.profil.riasec[t], profesi: (p.riasec[t] - 1) / 6 }))}
        />
        <p className="mt-3 text-xs text-slate-500">
          Profil profesi dari O*NET: {p.soc_judul} ({p.soc_code}), keyakinan padanan {p.soc_keyakinan}.
          {p.soc_catatan && ` Catatan: ${p.soc_catatan}.`}
        </p>
      </section>

      <section className={kartu}>
        <h2 className="font-semibold text-slate-900">Kepribadian: kamu dan profil ideal profesi</h2>
        <Banding baris={[...'OCEAN'].map((k) => ({ nama: NAMA_BIG5[k], kamu: d.profil.big5[k], profesi: p.big5_ideal[k] }))} />
      </section>
    </>
  )
}

function Banding({ baris }: { baris: { nama: string; kamu: number; profesi: number }[] }) {
  return (
    <div className="mt-3 space-y-3">
      <div className="flex gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-teal-600" /> Kamu</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-slate-400" /> Profesi</span>
      </div>
      {baris.map((b) => (
        <div key={b.nama}>
          <p className="mb-1 text-sm text-slate-700">{b.nama}</p>
          <div className="space-y-1">
            <Batang nilai={b.kamu} />
            <Batang nilai={b.profesi} warna="bg-slate-400" />
          </div>
        </div>
      ))}
    </div>
  )
}

function TabSkill({ d }: { d: Detail }) {
  const g = d.kesenjangan
  return (
    <>
      <section className={kartu}>
        <p className="text-sm text-slate-700">
          Kamu sudah memenuhi <strong className="text-slate-900">{g.wajib_terpenuhi} dari {g.wajib_total}</strong> skill wajib.
          Yang belum diurutkan dari yang paling penting untuk dikejar.
        </p>
        {d.profesi.skill_sumber === 'kurasi' && (
          <p className="mt-2 text-xs text-amber-700">
            Daftar skill profesi ini hasil kurasi, belum divalidasi dengan data lowongan.
          </p>
        )}
      </section>
      <DaftarSkill judul={`Perlu dikejar (${g.belum.length})`} daftar={g.belum} punya={false} />
      <DaftarSkill judul={`Sudah kamu miliki (${g.dimiliki.length})`} daftar={g.dimiliki} punya />
    </>
  )
}

function DaftarSkill({ judul, daftar, punya }: { judul: string; daftar: SkillProfesi[]; punya: boolean }) {
  return (
    <section className={kartu}>
      <h2 className="font-semibold text-slate-900">{judul}</h2>
      {daftar.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">{punya ? 'Belum ada.' : 'Semua skill profesi ini sudah kamu miliki.'}</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100">
          {daftar.map((s) => (
            <li key={s.skill_id} className="flex items-start gap-3 py-2.5">
              {punya ? <Check className="mt-0.5 size-4 shrink-0 text-teal-700" aria-hidden /> : <X className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />}
              <div className="min-w-0 flex-1">
                <p className="text-sm text-slate-800">
                  {s.nama}
                  {s.wajib && <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold text-amber-800">wajib</span>}
                  {s.label_tingkat && <span className="ml-2 text-xs text-slate-500">{s.label_tingkat}</span>}
                </p>
                {s.catatan && <p className="text-xs text-slate-500">{s.catatan}</p>}
              </div>
              {s.bobot > 0 && <span className="shrink-0 text-xs tabular-nums text-slate-500">bobot {s.bobot}</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function TabTentang({ d }: { d: Detail }) {
  const p = d.profesi
  const fakta: [string, string][] = [
    ['Rentang gaji', `${rupiah(p.gaji_min)} – ${rupiah(p.gaji_maks)} per bulan (median ${rupiah(p.gaji_median)})`],
    ['Pendidikan minimum', p.pendidikan_min_label],
    ['Pengalaman minimum', p.pengalaman_min_tahun === 0 ? 'Tanpa pengalaman' : `${p.pengalaman_min_tahun} tahun`],
    ['Pola kerja', p.pola_kerja.join(' / ')],
    ['Lokasi lowongan', p.semua_kota ? 'Semua kota besar' : p.lokasi.join(', ')],
    ['Jenjang karier', p.jenjang_karier],
  ]
  return (
    <>
      <section className={kartu}>
        <p className="text-sm leading-relaxed text-slate-700">{p.deskripsi}</p>
        <dl className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {fakta.map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs text-slate-500">{k}</dt>
              <dd className="text-sm text-slate-900">{v}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section className={kartu}>
        <h2 className="font-semibold text-slate-900">Tanggung jawab utama</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {p.tanggung_jawab.map((t) => <li key={t}>{t}</li>)}
        </ul>
      </section>
      {d.prodi_terkait.length > 0 && (
        <section className={kartu}>
          <h2 className="font-semibold text-slate-900">Program studi yang relevan</h2>
          <p className="mt-2 text-sm text-slate-700">{d.prodi_terkait.join(' · ')}</p>
        </section>
      )}
    </>
  )
}
