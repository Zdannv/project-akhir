/**
 * Roadmap skill menuju profesi tujuan.
 *
 * Skill yang belum dikuasai disusun tiga tahap (Pondasi, Penguatan, Pelengkap)
 * dari data yang sama dengan yang dipakai mesin. Mencentang skill tidak
 * mengubah rekomendasi tersimpan; ia menghitung proyeksi: kalau skill ini
 * sudah dikuasai, cakupan, skor, dan peringkatnya jadi berapa.
 */
import { ArrowRight, Check, CheckCircle2, Repeat, TrendingUp } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { ambilRoadmap, centangRoadmap, persen, pilihTarget, type Roadmap as DataRoadmap } from '../api'
import { AppBottomNav, AppTopNav, KepalaLayar } from '../komponen/AppNav'
import { Batang, Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

export default function Roadmap() {
  const { id = '' } = useParams()
  const { data, galat, muat, setData } = useData(() => ambilRoadmap(id), `roadmap/${id}`)

  async function centang(skill_id: string, selesai: boolean) {
    try {
      await centangRoadmap(id, skill_id, selesai)
      setData(await ambilRoadmap(id)) // skor proyeksi dihitung server
    } catch {
      // Biarkan tampilan apa adanya; centangnya tidak tersimpan.
    }
  }

  async function ganti() {
    await pilihTarget(id, null)
    setData({ target: null })
  }

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      <KepalaLayar ke={`/explore/${id}`} judul="Roadmap" subjudul={data?.target?.nama} />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-2xl flex-1 p-6"><Galat pesan={galat ?? 'Gagal memuat roadmap.'} /></div>
      ) : data.target === null ? <Kosong id={id} /> : <Isi id={id} d={data} centang={centang} ganti={ganti} />}
      <AppBottomNav id={id} />
    </div>
  )
}

function Kosong({ id }: { id: string }) {
  return (
    <main className="mx-auto w-full max-w-[486px] flex-1 px-4 py-8 sm:px-0">
      <div className="rounded-2xl bg-slate-50/80 p-6 text-center">
        <img src="/ilustrasi/gunung.webp" alt="" className="mx-auto h-auto w-[220px]" aria-hidden />
        <h1 className="mt-4 text-[17px] font-bold tracking-tight text-slate-900">Belum ada profesi tujuan</h1>
        <p className="mx-auto mt-1 max-w-[380px] text-[13.5px] leading-relaxed text-slate-600">
          Buka salah satu profesi yang direkomendasikan, lalu tekan “Jadikan Profesi Tujuan”. Roadmap skill-nya akan disusun di sini.
        </p>
      </div>
      <Link to={`/explore/${id}`} className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-violet-600 py-3.5 text-[14px] font-semibold text-white transition-colors hover:bg-violet-700">
        Lihat Rekomendasi <ArrowRight className="size-4" aria-hidden />
      </Link>
    </main>
  )
}

type Terisi = Extract<DataRoadmap, { tahap: unknown }>

function Isi({ id, d, centang, ganti }: { id: string; d: Terisi; centang: (skill: string, selesai: boolean) => void; ganti: () => void }) {
  const { selesai, total } = d.progres
  const naik = d.awal && d.proyeksi ? d.proyeksi.cakupan - d.awal.cakupan : 0
  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-12 pt-5 sm:px-6">
      <section className="rounded-2xl bg-violet-600 p-5 text-white">
        <p className="text-[12px] font-bold text-violet-200">Profesi Tujuan · {d.target.sektor}</p>
        <h1 className="mt-1 text-[20px] font-bold leading-tight tracking-tight">{d.target.nama}</h1>
        <div className="mt-4 flex items-baseline justify-between text-[12.5px] text-violet-100">
          <span>{total === 0 ? 'Semua skill profesi ini sudah kamu kuasai' : `${selesai} dari ${total} skill dipelajari`}</span>
          <span className="font-semibold text-white">{total === 0 ? '100%' : persen(selesai / total)}</span>
        </div>
        <div className="mt-1.5"><Batang nilai={total === 0 ? 1 : selesai / total} warna="bg-white" alas="bg-violet-400/60" /></div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link to={`/explore/${id}/profesi/${d.target.profesi_id}`} className="inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-[12.5px] font-semibold text-violet-700 hover:bg-violet-50">
            Detail profesi <ArrowRight className="size-3.5" aria-hidden />
          </Link>
          <button type="button" onClick={ganti} className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-[12.5px] font-semibold text-white ring-1 ring-violet-300 hover:bg-violet-700">
            <Repeat className="size-3.5" aria-hidden /> Ganti tujuan
          </button>
        </div>
      </section>

      {d.awal && d.proyeksi && (
        <section className="mt-4 rounded-2xl border border-slate-200 p-4">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold text-slate-900"><TrendingUp className="size-4 text-violet-600" aria-hidden /> Simulasi kecocokan</h2>
          <p className="mt-1 text-[12.5px] leading-relaxed text-slate-500">
            Centang skill yang sudah atau akan kamu pelajari untuk melihat perubahannya. Rekomendasi aslimu tidak berubah.
          </p>
          <dl className="mt-4 grid grid-cols-3 gap-3 text-center">
            <Angka label="Cakupan skill" awal={persen(d.awal.cakupan)} kini={persen(d.proyeksi.cakupan)} berubah={naik > 0.0005} />
            <Angka label="Skor akhir" awal={persen(d.awal.skor)} kini={persen(d.proyeksi.skor)} berubah={Math.round(d.awal.skor * 100) !== Math.round(d.proyeksi.skor * 100)} />
            <Angka label="Peringkat" awal={`#${d.awal.peringkat}`} kini={`#${d.proyeksi.peringkat}`} berubah={d.awal.peringkat !== d.proyeksi.peringkat} />
          </dl>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-400">
            **Cakupan = porsi bobot skill profesi yang dikuasai. Skill yang dicentang dihitung pada tingkat Menengah. Skor akhir memakai
            cosine similarity, yang mengukur kemiripan arah, sehingga kenaikannya tidak selalu sebesar cakupan.
          </p>
        </section>
      )}

      {d.target.skill_sumber !== 'lowongan' && (
        <p className="mt-3 text-[11.5px] leading-relaxed text-amber-700">
          Sebagian daftar skill profesi ini hasil kurasi dan belum divalidasi dengan data lowongan.
        </p>
      )}

      <ol className="mt-6 flex flex-col">
        {d.tahap.map((t, i) => {
          const beres = t.skill.every((s) => s.dicentang)
          return (
            <li key={t.kode} className="flex gap-3">
              <span className="flex flex-col items-center">
                <span className={`grid size-7 shrink-0 place-items-center rounded-full text-[12px] font-bold ${beres ? 'bg-emerald-500 text-white' : 'bg-violet-600 text-white'}`} aria-hidden>
                  {beres ? <Check className="size-4" strokeWidth={3} /> : i + 1}
                </span>
                {i < d.tahap.length - 1 && <span className="my-1 w-px flex-1 bg-slate-200" aria-hidden />}
              </span>
              <div className="min-w-0 flex-1 pb-7">
                <h2 className="text-[15px] font-bold text-slate-900">{t.nama} <span className="text-[12.5px] font-normal text-slate-400">({t.skill.filter((s) => s.dicentang).length}/{t.skill.length})</span></h2>
                <p className="mt-0.5 text-[12.5px] leading-snug text-slate-500">{t.keterangan}</p>
                <ul className="mt-3 flex flex-col gap-2">
                  {t.skill.map((s) => (
                    <li key={s.skill_id}>
                      <button type="button" aria-pressed={s.dicentang} onClick={() => centang(s.skill_id, !s.dicentang)}
                        className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${s.dicentang ? 'border-violet-500 bg-violet-50/60' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
                        <span className={`grid size-[18px] shrink-0 place-items-center rounded-[5px] border ${s.dicentang ? 'border-violet-600 bg-violet-600' : 'border-slate-300 bg-white'}`} aria-hidden>
                          {s.dicentang && <Check className="size-3 text-white" strokeWidth={3} />}
                        </span>
                        <span className={`min-w-0 flex-1 text-[13.5px] font-semibold leading-snug ${s.dicentang ? 'text-slate-500 line-through' : 'text-slate-900'}`}>{s.nama}</span>
                        {s.bobot > 0 && <span className="shrink-0 text-[11.5px] tabular-nums text-slate-400">bobot {s.bobot}</span>}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </li>
          )
        })}
      </ol>

      {d.dikuasai.length > 0 && (
        <section className="rounded-2xl border border-slate-200 p-4">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold text-slate-900"><CheckCircle2 className="size-4 text-emerald-600" aria-hidden /> Sudah kamu kuasai <span className="text-[12.5px] font-normal text-slate-400">({d.dikuasai.length})</span></h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {d.dikuasai.map((s) => (
              <li key={s.skill_id} className="rounded-full bg-emerald-50 px-3 py-1.5 text-[12.5px] font-medium text-emerald-700">{s.nama}</li>
            ))}
          </ul>
        </section>
      )}
    </main>
  )
}

function Angka({ label, awal, kini, berubah }: { label: string; awal: string; kini: string; berubah: boolean }) {
  return (
    <div className="rounded-xl bg-slate-50 px-2 py-3">
      <dt className="text-[11.5px] text-slate-500">{label}</dt>
      <dd className="mt-1 text-[19px] font-bold leading-none text-slate-900">{kini}</dd>
      <dd className={`mt-1 text-[11.5px] ${berubah ? 'font-semibold text-violet-700' : 'text-slate-400'}`}>{berubah ? `dari ${awal}` : 'belum berubah'}</dd>
    </div>
  )
}
