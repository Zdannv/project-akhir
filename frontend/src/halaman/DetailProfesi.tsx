/**
 * Detail profesi — tiga tab, mengikuti susunan Navika.
 *
 *   Analisa            skor kecocokan, alasan, rincian komponen, perbandingan profil
 *   Skill & Kompetensi syarat, kesenjangan skill, skill yang sudah dimiliki
 *   Insight            gaji, pola kerja, tanggung jawab, jenjang karier
 */
import { ArrowRight, Building2, Check, GraduationCap, Info, ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { ambilDetail, kirimUmpanBalik, NAMA_BIG5, NAMA_RIASEC, persen, rupiah, type Alasan, type Detail, type SkillProfesi } from '../api'
import { AppTopNav, KepalaLayar } from '../komponen/AppNav'
import { BusurSkor, LencanaPita, TabSwitch } from '../komponen/profesi'
import { Batang, Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

type Tab = 'analisa' | 'skill' | 'insight'
const TABS = [
  { kode: 'analisa' as const, label: 'Analisa' },
  { kode: 'skill' as const, label: 'Skill & Kompetensi' },
  { kode: 'insight' as const, label: 'Insight' },
]

const NAMA_KOMPONEN = {
  riasec: 'Kongruensi minat (RIASEC)',
  big5: 'Kecocokan kepribadian (Big Five)',
  finansial: 'Kecocokan finansial',
  stabilitas: 'Stabilitas kerja',
} as const

export default function DetailProfesi() {
  const { id = '', pid = '' } = useParams()
  const { data, galat, muat, setData } = useData(() => ambilDetail(id, pid), `${id}/${pid}`)
  const [tab, setTab] = useState<Tab>('analisa')

  // Tampilan diperbarui lebih dulu dan dikembalikan kalau penyimpanannya gagal.
  async function nilai(relevan: boolean) {
    if (!data) return
    const lama = data
    setData({ ...lama, relevan })
    try {
      await kirimUmpanBalik(id, { [pid]: relevan })
    } catch {
      setData(lama)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      <KepalaLayar ke={`/explore/${id}`} judul={data?.profesi.nama ?? 'Detail Profesi'} subjudul={data?.profesi.sektor} />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-3xl flex-1 p-6"><Galat pesan={galat ?? 'Profesi tidak ditemukan.'} /></div>
      ) : (
        <>
          <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-10 pt-5 sm:px-6">
            <span className="inline-flex items-center gap-1 rounded-md bg-indigo-50 px-2 py-1 text-[11px] font-medium text-indigo-700">
              <Building2 className="size-3 shrink-0" aria-hidden /> {data.profesi.sektor}
            </span>
            <h1 className="mt-2 text-[22px] font-bold leading-tight tracking-tight text-slate-900">{data.profesi.nama}</h1>
            <p className="mt-2 text-[13.5px] leading-relaxed text-slate-600">{data.profesi.deskripsi}</p>

            <div className="mt-5"><TabSwitch tabs={TABS} aktif={tab} onPilih={setTab} /></div>

            {tab === 'analisa' && <TabAnalisa d={data} />}
            {tab === 'skill' && <TabSkill d={data} />}
            {tab === 'insight' && <TabInsight d={data} />}
          </main>

          {data.penilaian && (
            <div className="sticky bottom-0 z-20 border-t border-violet-100 bg-[#EDEBFA] px-4 py-3 sm:px-6" style={{ paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom))' }}>
              <div className="mx-auto flex max-w-3xl flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[13.5px] font-semibold text-slate-900">Menurutmu, apakah rekomendasi ini relevan?</p>
                <div className="flex gap-2">
                  <button type="button" aria-pressed={data.relevan === false} onClick={() => nilai(false)}
                    className={`inline-flex flex-1 items-center justify-center gap-2 rounded-full px-5 py-3 text-[13.5px] font-semibold transition-colors sm:flex-none ${data.relevan === false ? 'bg-slate-900 text-white' : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50'}`}>
                    <ThumbsDown className="size-4" aria-hidden /> Tidak
                  </button>
                  <button type="button" aria-pressed={data.relevan === true} onClick={() => nilai(true)}
                    className={`inline-flex flex-1 items-center justify-center gap-2 rounded-full px-5 py-3 text-[13.5px] font-semibold transition-colors sm:flex-none ${data.relevan === true ? 'bg-violet-600 text-white' : 'bg-white text-violet-700 ring-1 ring-violet-300 hover:bg-violet-50'}`}>
                    <ThumbsUp className="size-4" aria-hidden /> Ya, relevan
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function DaftarAlasan({ alasan }: { alasan: Alasan[] }) {
  return (
    <ul className="flex flex-col gap-3.5">
      {alasan.map((a) => (
        <li key={a.teks} className="flex items-start gap-2.5">
          <span className={`mt-0.5 grid size-[18px] shrink-0 place-items-center rounded-full border ${a.nada === 'cocok' ? 'border-emerald-500 text-emerald-600' : 'border-amber-500 text-amber-600'}`} aria-hidden>
            {a.nada === 'cocok' ? <Check className="size-3" /> : <Info className="size-3" />}
          </span>
          <p className="text-[13.5px] leading-relaxed text-slate-600">{a.teks}</p>
        </li>
      ))}
    </ul>
  )
}

function Blok({ judul, keterangan, children }: { judul: string; keterangan?: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="text-[15px] font-semibold text-slate-900">
        {judul} {keterangan && <span className="text-[12.5px] font-normal text-slate-400">{keterangan}</span>}
      </h3>
      <div className="mt-3">{children}</div>
    </section>
  )
}

function TabAnalisa({ d }: { d: Detail }) {
  const p = d.profesi
  const n = d.penilaian
  const skor = d.ringkas?.skor ?? null
  return (
    <div className="mt-7 flex flex-col gap-7">
      <section className="flex flex-col items-center">
        <BusurSkor skor={skor} />
        <h2 className="mt-1 text-[15px] font-semibold text-slate-900">Skor Kecocokan dengan Profesi</h2>
        {skor !== null && <div className="mt-2.5"><LencanaPita skor={skor} /></div>}
        {d.ringkas && <p className="mt-2 text-[12.5px] text-slate-500">Peringkat {d.ringkas.peringkat} untukmu</p>}
        {d.tersaring && (
          <p className="mt-3 max-w-sm text-center text-[12.5px] leading-relaxed text-amber-700">
            Profesi ini tidak dinilai karena syarat mutlaknya tidak terpenuhi. {d.tersaring.alasan.map((a) => a.pesan).join(' ')}
          </p>
        )}
        {n && <div className="mt-5 w-full"><DaftarAlasan alasan={n.alasan} /></div>}
      </section>

      {n ? (
        <section className="rounded-2xl border border-slate-200 p-4">
          <h3 className="text-[15px] font-semibold text-slate-900">Rincian Skor</h3>
          <p className="mt-1 text-[12.5px] leading-relaxed text-slate-500">
            Kecocokan profil (KBF) {persen(n.kbf.skor)} dan kemiripan skill (CBF) {persen(n.cbf.skor)} digabung menjadi {persen(n.skor)}.
          </p>
          <dl className="mt-4 flex flex-col gap-3.5">
            {(Object.keys(NAMA_KOMPONEN) as (keyof typeof NAMA_KOMPONEN)[]).map((k) => (
              <div key={k} className={n.kbf.bobot[k] === 0 ? 'opacity-45' : ''}>
                <div className="mb-1.5 flex justify-between gap-3 text-[13px]">
                  <dt className="text-slate-700">{NAMA_KOMPONEN[k]} <span className="text-[11.5px] text-slate-400">· bobot {persen(n.kbf.bobot[k])}</span></dt>
                  <dd className="font-semibold tabular-nums text-slate-900">{persen(n.kbf.komponen[k])}</dd>
                </div>
                <Batang nilai={n.kbf.komponen[k]} />
              </div>
            ))}
            <div>
              <div className="mb-1.5 flex justify-between gap-3 text-[13px]">
                <dt className="text-slate-700">Kemiripan skill <span className="text-[11.5px] text-slate-400">· cosine similarity</span></dt>
                <dd className="font-semibold tabular-nums text-slate-900">{persen(n.cbf.skor)}</dd>
              </div>
              <Batang nilai={n.cbf.skor} warna="bg-indigo-500" alas="bg-indigo-100" />
            </div>
          </dl>
        </section>
      ) : d.ringkas && (
        <section className="rounded-2xl bg-violet-50 px-4 py-3.5">
          <p className="text-[13px] leading-relaxed text-slate-700">
            Profesi ini di luar rekomendasi teratasmu: kecocokan profil (KBF) {persen(d.ringkas.skor_kbf)}, kemiripan skill (CBF) {persen(d.ringkas.skor_cbf)}.
          </p>
        </section>
      )}

      <Blok judul="Minat" keterangan={`(kamu ${d.kode_holland_pengguna} · profesi ${p.kode_holland})`}>
        <Banding baris={[...'RIASEC'].map((t) => ({ nama: NAMA_RIASEC[t], kamu: d.profil.riasec[t], profesi: (p.riasec[t] - 1) / 6 }))} />
      </Blok>
      <Blok judul="Kepribadian" keterangan="(kamu dan profil ideal profesi)">
        <Banding baris={[...'OCEAN'].map((k) => ({ nama: NAMA_BIG5[k], kamu: d.profil.big5[k], profesi: p.big5_ideal[k] }))} />
      </Blok>
      <p className="text-[11px] leading-relaxed text-slate-400">
        **Profil profesi dari O*NET: {p.soc_judul} ({p.soc_code}), keyakinan padanan {p.soc_keyakinan}.{p.soc_catatan && ` ${p.soc_catatan}.`}
      </p>
    </div>
  )
}

function Banding({ baris }: { baris: { nama: string; kamu: number; profesi: number }[] }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-4 text-[11.5px] text-slate-500">
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-violet-600" /> Kamu</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-slate-400" /> Profesi</span>
      </div>
      {baris.map((b) => (
        <div key={b.nama}>
          <p className="mb-1.5 text-[13px] text-slate-700">{b.nama}</p>
          <div className="flex flex-col gap-1">
            <Batang nilai={b.kamu} />
            <Batang nilai={b.profesi} warna="bg-slate-400" alas="bg-slate-100" />
          </div>
        </div>
      ))}
    </div>
  )
}

function TabSkill({ d }: { d: Detail }) {
  const p = d.profesi
  const g = d.kesenjangan
  return (
    <div className="mt-7 flex flex-col gap-7">
      <Blok judul="Pendidikan & Pengalaman">
        <div className="flex items-start gap-3 rounded-2xl border border-slate-200 px-3.5 py-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-violet-50 text-violet-600"><GraduationCap className="size-5" aria-hidden /></span>
          <div className="min-w-0">
            <p className="text-[13.5px] font-semibold leading-snug text-slate-900">Minimum {p.pendidikan_min_label}</p>
            <p className="mt-0.5 text-[12.5px] leading-snug text-slate-400">
              {p.pengalaman_min_tahun === 0 ? 'Terbuka untuk lulusan baru' : `Pengalaman minimum ${p.pengalaman_min_tahun} tahun`}
            </p>
          </div>
        </div>
      </Blok>

      <section className="relative overflow-hidden rounded-2xl border border-violet-100 bg-violet-50 p-4">
        <img src="/profesi/skill-gap-banner.webp" alt="" className="pointer-events-none absolute -right-6 bottom-0 h-[86%] w-auto object-contain" />
        <div className="relative max-w-[64%]">
          <p className="text-[15px] font-bold text-violet-700">Skill Gap Analysis</p>
          <p className="mt-1 text-[12.5px] leading-relaxed text-slate-600">
            Kamu memenuhi <strong className="font-semibold text-slate-900">{g.wajib_terpenuhi} dari {g.wajib_total}</strong> skill wajib. Masih ada {g.belum.length} skill yang bisa dikembangkan.
          </p>
        </div>
      </section>
      {p.skill_sumber === 'kurasi' && (
        <p className="-mt-3 text-[11.5px] leading-relaxed text-amber-700">Daftar skill profesi ini hasil kurasi dan belum divalidasi dengan data lowongan.</p>
      )}

      <Blok judul="Perlu Dikembangkan" keterangan={`(${g.belum.length} skill, dari yang paling penting)`}>
        <DaftarSkill daftar={g.belum} kosong="Semua skill profesi ini sudah kamu miliki." />
      </Blok>
      <Blok judul="Sudah Kamu Miliki" keterangan={`(${g.dimiliki.length} skill)`}>
        <DaftarSkill daftar={g.dimiliki} kosong="Belum ada skill-mu yang beririsan dengan profesi ini." />
      </Blok>
    </div>
  )
}

function DaftarSkill({ daftar, kosong }: { daftar: SkillProfesi[]; kosong: string }) {
  if (daftar.length === 0) return <p className="text-[13px] text-slate-400">{kosong}</p>
  return (
    <ul>
      {daftar.map((s) => (
        <li key={s.skill_id} className="flex items-start justify-between gap-3 border-b border-slate-200 py-3 last:border-b-0">
          <div className="min-w-0">
            <p className="text-[13.5px] font-semibold leading-snug text-slate-900">
              {s.nama}
              {s.wajib && <span className="ml-2 rounded-md bg-amber-50 px-1.5 py-0.5 align-middle text-[11px] font-medium text-amber-700">Wajib</span>}
            </p>
            {s.catatan && <p className="mt-0.5 text-[12.5px] leading-snug text-slate-400">{s.catatan}</p>}
          </div>
          <div className="shrink-0 text-right">
            {s.label_tingkat && <p className="rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">{s.label_tingkat}</p>}
            {s.bobot > 0 && <p className="mt-0.5 text-[11.5px] tabular-nums text-slate-400">bobot {s.bobot}</p>}
          </div>
        </li>
      ))}
    </ul>
  )
}

function TabInsight({ d }: { d: Detail }) {
  const p = d.profesi
  const jenjang = p.jenjang_karier.split('→').map((s) => s.trim()).filter(Boolean)
  return (
    <div className="mt-7 flex flex-col gap-7">
      <Blok judul="Kisaran Gaji (Indonesia)">
        <ul>
          {[['Batas bawah', p.gaji_min], ['Median', p.gaji_median], ['Batas atas', p.gaji_maks]].map(([nama, nilai]) => (
            <li key={nama} className="flex items-center justify-between gap-3 border-b border-slate-200 py-3 last:border-b-0">
              <p className="text-[13.5px] font-semibold text-slate-900">{nama}</p>
              <p className="shrink-0 text-[13.5px] font-bold text-slate-900">{rupiah(nilai as number)}/bulan</p>
            </li>
          ))}
        </ul>
        <p className="mt-2.5 text-[11px] text-slate-400">**Jenjang {p.senioritas}. Sumber: pengolahan lowongan kerja LinkedIn Indonesia 2025.</p>
      </Blok>

      <section className="flex items-center justify-between gap-3 rounded-2xl bg-violet-50 px-4 py-3.5">
        <div className="min-w-0">
          <h3 className="text-[14.5px] font-semibold text-slate-900">Pola Kerja</h3>
          <p className="mt-0.5 text-[11.5px] leading-snug text-slate-500">{p.semua_kota ? 'Semua kota besar Indonesia' : p.lokasi.join(', ')}</p>
        </div>
        <p className="shrink-0 text-[15px] font-bold capitalize text-slate-900">{p.pola_kerja.join(' / ')}</p>
      </section>

      <Blok judul="Tanggung Jawab Utama">
        <ul>
          {p.tanggung_jawab.map((t) => (
            <li key={t} className="border-b border-slate-200 py-3 text-[13.5px] leading-snug text-slate-900 first-letter:uppercase last:border-b-0">{t}</li>
          ))}
        </ul>
      </Blok>

      <Blok judul="Jenjang Karier">
        <ol className="flex flex-wrap items-center gap-2">
          <li className="rounded-md bg-violet-600 px-2.5 py-1.5 text-[12px] font-medium text-white">{p.nama}</li>
          {jenjang.map((j) => (
            <li key={j} className="flex items-center gap-2">
              <ArrowRight className="size-3.5 text-slate-400" aria-hidden />
              <span className="rounded-md bg-indigo-50 px-2.5 py-1.5 text-[12px] font-medium text-indigo-700">{j}</span>
            </li>
          ))}
        </ol>
      </Blok>

      {d.prodi_terkait.length > 0 && (
        <Blok judul="Program Studi yang Relevan">
          <ul className="flex flex-wrap gap-2">
            {d.prodi_terkait.map((x) => (
              <li key={x} className="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 px-2.5 py-1.5 text-[12px] font-medium text-indigo-700">
                <GraduationCap className="size-3.5 shrink-0" aria-hidden /> {x}
              </li>
            ))}
          </ul>
        </Blok>
      )}
    </div>
  )
}
