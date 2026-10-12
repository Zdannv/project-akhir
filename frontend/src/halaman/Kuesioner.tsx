/**
 * Alur profiling: layar pembuka, empat langkah
 * dengan daftar langkah di kiri (desktop) atau chip STEP (ponsel), lalu layar
 * penutup yang mengantar ke rekomendasi.
 */
import { ArrowLeft, ArrowRight, Check, ChevronRight, CornerUpLeft, Home, Loader2, Plus, Search, Timer, X } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ambilKuesioner, ambilMasukan, kirimMasukan, type Butir, type Kuesioner as DataKuesioner, type Masukan } from '../api'
import { Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'
import { ingatHasil } from '../sesi'

const LANGKAH = [
  { nama: 'Latar Belakang', tanya: 'Ceritakan pendidikan dan kondisimu saat ini.', gambar: '/ilustrasi/langkah-latar.webp' },
  { nama: 'Minat', tanya: 'Kegiatan seperti apa yang kamu sukai?', gambar: '/ilustrasi/langkah-minat.webp' },
  { nama: 'Kepribadian', tanya: 'Seperti apa dirimu sehari-hari?', gambar: '/ilustrasi/langkah-kepribadian.webp' },
  { nama: 'Keahlian', tanya: 'Skill apa saja yang sudah kamu kuasai?', gambar: '/ilustrasi/langkah-keahlian.webp' },
]

const AWAL: Masukan = {
  nama: '', jenis_responden: 'mahasiswa', profesi_aktual: null,
  jenjang: '', prodi_id: null, domisili: '', bersedia_relokasi: true,
  ekspektasi_gaji: 0, punya_tanggungan: false,
  riasec: {}, big5: {}, skill: {}, skill_lain: [],
}

export default function Kuesioner() {
  // ?dari=<id> berarti mengubah jawaban lama: formulirnya diisi dari isian itu.
  const [param] = useSearchParams()
  const dari = param.get('dari')
  const { data, galat, muat } = useData(
    async () => ({ k: await ambilKuesioner(), awal: dari ? await ambilMasukan(dari) : null }),
    `kuesioner/${dari ?? ''}`,
  )
  if (muat) return <Kerangka step={null}><Memuat /></Kerangka>
  if (galat || !data) return <Kerangka step={null}><div className="mx-auto max-w-md p-6"><Galat pesan={galat ?? 'Gagal memuat kuesioner.'} /></div></Kerangka>
  return <Formulir key={dari ?? 'baru'} k={data.k} awal={data.awal} dari={dari} />
}

function Formulir({ k, awal, dari }: { k: DataKuesioner; awal: Masukan | null; dari: string | null }) {
  // 0 = pembuka, 1..4 = langkah, 5 = penutup. Saat mengubah jawaban, pembuka
  // dilewati dan semua langkah langsung bisa dilompati.
  const [step, setStep] = useState(awal ? 1 : 0)
  const [capai, setCapai] = useState(awal ? LANGKAH.length : 1)
  const [m, setM] = useState<Masukan>(awal ? { ...AWAL, ...awal } : AWAL)
  const [kirim, setKirim] = useState(false)
  const [gagal, setGagal] = useState<string | null>(null)
  const [idHasil, setIdHasil] = useState<string | null>(null)
  const ubah = (bagian: Partial<Masukan>) => setM((lama) => ({ ...lama, ...bagian }))

  if (step === 0) return <Kerangka step={null}><Pembuka onMulai={() => setStep(1)} /></Kerangka>
  if (step === 5 && idHasil) return <Kerangka step={null}><Penutup id={idHasil} /></Kerangka>

  const lengkap = [
    m.nama.trim() !== '' && m.jenjang !== '' && m.domisili !== '' &&
      (m.jenis_responden === 'mahasiswa' || m.profesi_aktual !== null),
    k.riasec.butir.every((b) => m.riasec[b.kode]),
    k.big5.butir.every((b) => m.big5[b.kode]),
    true, // skill boleh kosong: mesin tetap jalan dengan KBF saja
  ][step - 1]

  function pindah(ke: number) {
    setStep(ke)
    setCapai((c) => Math.max(c, ke))
    window.scrollTo({ top: 0 })
  }

  // Tingkat 0 berarti skill dilepas.
  function aturSkill(id: string, tingkat: number) {
    setM((lama) => {
      const skill = { ...lama.skill }
      if (tingkat === 0) delete skill[id]
      else skill[id] = tingkat
      return { ...lama, skill }
    })
  }

  async function selesai() {
    setKirim(true)
    setGagal(null)
    try {
      const { id } = await kirimMasukan({ ...m, nama: m.nama.trim(), induk: dari })
      ingatHasil(id)
      setIdHasil(id)
      setStep(5)
      window.scrollTo({ top: 0 })
    } catch (e) {
      setGagal((e as Error).message)
    } finally {
      setKirim(false)
    }
  }

  const kini = LANGKAH[step - 1]
  const terakhir = step === LANGKAH.length

  return (
    <Kerangka step={step}>
      <div className="mx-auto flex w-full max-w-[1160px] gap-10 lg:px-8 lg:py-8">
        <aside className="hidden w-[300px] shrink-0 flex-col gap-6 lg:flex">
          <div className="overflow-hidden rounded-2xl bg-violet-50/60">
            <img key={kini.gambar} src={kini.gambar} alt="" className="h-auto w-full" aria-hidden />
          </div>
          <div>
            <p className="text-[13px] font-bold text-slate-900">STEP {step}/{LANGKAH.length}</p>
            <ol className="mt-4 flex flex-col">
              {LANGKAH.map((s, i) => {
                const no = i + 1
                const beres = no < capai
                const aktif = no === step
                const bisa = no <= capai
                return (
                  <li key={s.nama} className="flex gap-3">
                    <span className="flex flex-col items-center">
                      <span className={`grid size-6 shrink-0 place-items-center rounded-full text-[11px] font-bold ${beres && !aktif ? 'bg-emerald-500 text-white' : aktif ? 'bg-violet-600 text-white' : 'text-slate-400'}`} aria-hidden>
                        {beres && !aktif ? <Check className="size-3.5" strokeWidth={3} /> : no}
                      </span>
                      {i < LANGKAH.length - 1 && <span className="my-1 w-px flex-1 bg-slate-200" aria-hidden />}
                    </span>
                    <button type="button" disabled={!bisa} onClick={() => pindah(no)} aria-current={aktif ? 'step' : undefined} className="flex-1 pb-6 text-left disabled:cursor-not-allowed">
                      <span className={`block text-[14px] font-semibold ${bisa ? 'text-violet-700' : 'text-slate-400'}`}>{s.nama}</span>
                      <span className="mt-0.5 block text-[12.5px] leading-snug text-slate-500">{s.tanya}</span>
                    </button>
                  </li>
                )
              })}
            </ol>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden border-slate-200 lg:rounded-2xl lg:border">
          <div className="border-b border-slate-200 bg-slate-50/80 px-4 pb-4 pt-3.5 sm:px-6">
            <div className="flex items-center gap-3">
              <span className="inline-flex shrink-0 items-center rounded-md bg-violet-600 px-2 py-1 text-[11px] font-bold text-white">
                STEP {step}/{LANGKAH.length}
              </span>
              <p className="truncate text-[14px] font-bold text-slate-900">{kini.nama}</p>
            </div>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-violet-100" role="progressbar" aria-valuenow={step} aria-valuemin={1} aria-valuemax={LANGKAH.length} aria-label={`Langkah ${step} dari ${LANGKAH.length}`}>
              <div className="h-full rounded-full bg-violet-600 transition-[width] duration-300" style={{ width: `${(step / LANGKAH.length) * 100}%` }} />
            </div>
          </div>

          <div className="flex-1 px-4 py-6 sm:px-6">
            {step === 1 && <LatarBelakang k={k} m={m} ubah={ubah} />}
            {step === 2 && (
              <Likert
                judul="Seberapa suka kamu melakukan kegiatan berikut?"
                keterangan="Bayangkan kegiatannya, bukan apakah kamu sudah bisa melakukannya."
                butir={k.riasec.butir} skala={k.riasec.skala} jawaban={m.riasec}
                pilih={(kode, n) => setM((lama) => ({ ...lama, riasec: { ...lama.riasec, [kode]: n } }))}
              />
            )}
            {step === 3 && (
              <Likert
                judul={k.big5.awalan}
                keterangan="Tidak ada jawaban benar atau salah. Jawab sesuai dirimu sehari-hari."
                butir={k.big5.butir} skala={k.big5.skala} jawaban={m.big5}
                pilih={(kode, n) => setM((lama) => ({ ...lama, big5: { ...lama.big5, [kode]: n } }))}
              />
            )}
            {step === 4 && <PilihSkill k={k} skill={m.skill} atur={aturSkill} lain={m.skill_lain} ubahLain={(skill_lain) => ubah({ skill_lain })} />}
            {gagal && <div className="mt-5"><Galat pesan={gagal} /></div>}
          </div>

          <div className="sticky bottom-0 flex flex-col gap-2.5 border-t border-slate-200 bg-violet-50/95 px-4 py-4 backdrop-blur sm:px-6 lg:flex-row-reverse lg:items-center lg:justify-between lg:bg-white">
            <button
              type="button" disabled={!lengkap || kirim}
              onClick={() => (terakhir ? void selesai() : pindah(step + 1))}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-violet-600 px-6 py-3 text-[13.5px] font-semibold text-white transition-colors hover:bg-violet-700 disabled:opacity-50"
            >
              {kirim ? <><Loader2 className="size-4 animate-spin" aria-hidden /> Menghitung…</> : <>{terakhir ? 'Simpan & Lihat Rekomendasi' : `Lanjut ke Step ${step + 1}`} <ArrowRight className="size-4" aria-hidden /></>}
            </button>
            {step > 1 ? (
              <button type="button" disabled={kirim} onClick={() => pindah(step - 1)} className="inline-flex items-center justify-center gap-2 rounded-full py-3 text-[13.5px] font-semibold text-slate-600 transition-colors hover:bg-slate-100 lg:px-5">
                <CornerUpLeft className="size-4" aria-hidden /> Kembali ke Step {step - 1}
              </button>
            ) : (
              <Link to="/" className="hidden items-center justify-center gap-2 rounded-full py-3 text-[13.5px] font-semibold text-slate-600 transition-colors hover:bg-slate-100 lg:inline-flex lg:px-5">
                <X className="size-4" aria-hidden /> Batalkan
              </Link>
            )}
          </div>
        </div>
      </div>
    </Kerangka>
  )
}

/** Kepala layar ponsel dan breadcrumb desktop. `step` null = pembuka/penutup. */
function Kerangka({ step, children }: { step: number | null; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="sticky top-0 z-20 flex items-center border-b border-slate-200 bg-white px-4 py-3.5 lg:hidden">
        <Link to="/" className="flex items-center gap-3 text-slate-900">
          <ArrowLeft className="size-[18px]" aria-hidden />
          <span className="text-[14px] font-bold">Profil Karier</span>
        </Link>
      </header>
      <nav aria-label="Breadcrumb" className="hidden border-b border-slate-200 bg-white px-8 py-3.5 lg:block">
        <ol className="mx-auto flex max-w-[1160px] items-center gap-2 text-[13px] text-slate-500">
          <li><Link to="/" aria-label="Beranda" className="grid place-items-center text-slate-500 hover:text-slate-800"><Home className="size-4" aria-hidden /></Link></li>
          <ChevronRight className="size-3.5 text-slate-300" aria-hidden />
          <li className={step === null ? 'text-slate-800' : ''}>Kenali Profil Kariermu</li>
          {step !== null && (
            <>
              <ChevronRight className="size-3.5 text-slate-300" aria-hidden />
              <li className="font-semibold text-slate-800">STEP {step}/{LANGKAH.length}</li>
            </>
          )}
        </ol>
      </nav>
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  )
}

function Pembuka({ onMulai }: { onMulai: () => void }) {
  return (
    <div className="mx-auto w-full max-w-[486px] px-4 py-8 sm:px-0">
      <div className="rounded-2xl bg-slate-50/80 p-6 text-center">
        <img src="/ilustrasi/pembuka.webp" alt="" className="mx-auto h-auto w-[218px]" aria-hidden />
        <h1 className="mt-4 text-[17px] font-bold tracking-tight text-slate-900">Kenali Profil Kariermu</h1>
        <p className="mx-auto mt-1 max-w-[380px] text-[13.5px] leading-relaxed text-slate-600">
          Temukan profesi TI yang sesuai dengan minat, kepribadian, keahlian, dan kondisimu.
        </p>
      </div>
      <div className="mt-4 flex items-center gap-3 rounded-xl bg-slate-100/80 px-4 py-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-violet-100 text-violet-600"><Timer className="size-4" aria-hidden /></span>
        <span>
          <span className="block text-[12.5px] font-bold text-slate-900">Estimasi penyelesaian</span>
          <span className="block text-[12.5px] text-slate-600">~7 menit · 4 langkah</span>
        </span>
      </div>
      <button type="button" onClick={onMulai} className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-violet-600 py-3.5 text-[14px] font-semibold text-white transition-colors hover:bg-violet-700">
        Ayo Mulai! <ArrowRight className="size-4" aria-hidden />
      </button>
    </div>
  )
}

function Penutup({ id }: { id: string }) {
  return (
    <div className="mx-auto w-full max-w-[860px] px-4 py-10 sm:px-6">
      <div className="rounded-2xl bg-slate-50/70 px-6 py-10 text-center">
        <img src="/ilustrasi/selesai.webp" alt="" className="mx-auto h-auto w-[240px]" aria-hidden />
        <h1 className="mt-4 text-[17px] font-bold tracking-tight text-slate-900">Yay! Data kamu tersimpan 🎉</h1>
        <p className="mx-auto mt-2 max-w-[460px] text-[13.5px] leading-relaxed text-slate-600">
          Terima kasih! Profilmu sudah dicocokkan dengan 35 profesi TI. Rekomendasinya siap dilihat.
        </p>
        <div className="mx-auto mt-6 max-w-[520px] border-t border-slate-200 pt-6">
          <Link to={`/explore/${id}`} className="inline-flex items-center justify-center gap-2 rounded-full bg-violet-600 px-5 py-3 text-[13.5px] font-semibold text-white transition-colors hover:bg-violet-700">
            Tampilkan Rekomendasi Profesi <ArrowRight className="size-4" aria-hidden />
          </Link>
        </div>
      </div>
    </div>
  )
}

// ── Isi tiap langkah ────────────────────────────────────────────────────────
const kolom = 'mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-[13.5px] text-slate-900 outline-none placeholder:text-slate-400 focus:border-violet-400'
const judulKolom = 'text-[14.5px] font-bold text-slate-900'

function Pil({ pilihan, nilai, pilih, nama }: { pilihan: { nilai: string; label: string }[]; nilai: string; pilih: (v: string) => void; nama: string }) {
  return (
    <div className="mt-3 flex flex-wrap gap-2.5">
      {pilihan.map((o) => {
        const on = nilai === o.nilai
        return (
          <label key={o.nilai} className={`cursor-pointer select-none rounded-full px-4 py-2.5 text-[13.5px] font-medium shadow-sm ring-1 transition-colors focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-violet-600 ${on ? 'bg-[#F1EBFF] text-[#7033FF] ring-[#DDD0FF]' : 'bg-white text-slate-900 ring-slate-200 hover:bg-slate-50'}`}>
            <input type="radio" name={nama} value={o.nilai} checked={on} onChange={() => pilih(o.nilai)} className="sr-only" />
            {o.label}
          </label>
        )
      })}
    </div>
  )
}

function Centang({ aktif, onUbah, judul, keterangan }: { aktif: boolean; onUbah: (v: boolean) => void; judul: string; keterangan?: string }) {
  return (
    <button type="button" aria-pressed={aktif} onClick={() => onUbah(!aktif)} className={`flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${aktif ? 'border-violet-500 bg-violet-50/60' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
      <span className={`mt-0.5 grid size-[18px] shrink-0 place-items-center rounded-[5px] border ${aktif ? 'border-violet-600 bg-violet-600' : 'border-slate-300 bg-white'}`} aria-hidden>
        {aktif && <Check className="size-3 text-white" strokeWidth={3} />}
      </span>
      <span className="min-w-0">
        <span className="block text-[13.5px] font-semibold leading-snug text-slate-900">{judul}</span>
        {keterangan && <span className="mt-0.5 block text-[12.5px] leading-relaxed text-slate-500">{keterangan}</span>}
      </span>
    </button>
  )
}

function LatarBelakang({ k, m, ubah }: { k: DataKuesioner; m: Masukan; ubah: (b: Partial<Masukan>) => void }) {
  return (
    <div className="flex flex-col gap-7">
      <label className="block">
        <span className={judulKolom}>Siapa namamu?</span>
        <input className={kolom} value={m.nama} maxLength={80} placeholder="Nama lengkap atau panggilan" onChange={(e) => ubah({ nama: e.target.value })} />
      </label>

      <fieldset>
        <legend className={judulKolom}>Kamu mengisi sebagai</legend>
        <Pil nama="jenis" nilai={m.jenis_responden}
          pilihan={[{ nilai: 'mahasiswa', label: 'Mahasiswa / pencari kerja' }, { nilai: 'profesional', label: 'Profesional TI' }]}
          pilih={(v) => ubah({ jenis_responden: v as Masukan['jenis_responden'], profesi_aktual: v === 'mahasiswa' ? null : m.profesi_aktual })} />
      </fieldset>

      {m.jenis_responden === 'profesional' && (
        <label className="block">
          <span className={judulKolom}>Profesimu saat ini</span>
          <span className="mt-0.5 block text-[12.5px] text-slate-500">Dipakai untuk menguji ketepatan sistem; tidak memengaruhi rekomendasimu.</span>
          <select className={kolom} value={m.profesi_aktual ?? ''} onChange={(e) => ubah({ profesi_aktual: e.target.value || null })}>
            <option value="">Pilih profesi…</option>
            {k.profesi.map((p) => <option key={p.id} value={p.id}>{p.nama}</option>)}
          </select>
        </label>
      )}

      <fieldset>
        <legend className={judulKolom}>Pendidikan terakhir atau yang sedang ditempuh</legend>
        <Pil nama="jenjang" nilai={m.jenjang} pilihan={k.jenjang.map((j) => ({ nilai: j.kode, label: j.nama }))} pilih={(v) => ubah({ jenjang: v })} />
      </fieldset>

      <label className="block">
        <span className={judulKolom}>Program studi <span className="font-normal text-slate-400">(opsional)</span></span>
        <select className={kolom} value={m.prodi_id ?? ''} onChange={(e) => ubah({ prodi_id: e.target.value || null })}>
          <option value="">Tidak ada / lainnya</option>
          {k.prodi.map((p) => <option key={p.id} value={p.id}>{p.nama}</option>)}
        </select>
      </label>

      <fieldset>
        <legend className={judulKolom}>Domisili saat ini</legend>
        <Pil nama="domisili" nilai={m.domisili} pilihan={k.kota.map((c) => ({ nilai: c, label: c }))} pilih={(v) => ubah({ domisili: v })} />
      </fieldset>

      <label className="block">
        <span className={judulKolom}>Ekspektasi gaji per bulan <span className="font-normal text-slate-400">(juta rupiah, opsional)</span></span>
        <input className={kolom} type="number" min={0} max={200} step={0.5} inputMode="decimal" placeholder="Contoh: 7"
          value={m.ekspektasi_gaji ? m.ekspektasi_gaji / 1_000_000 : ''}
          onChange={(e) => ubah({ ekspektasi_gaji: Math.max(0, Math.round(Number(e.target.value) * 1_000_000)) || 0 })} />
      </label>

      <div className="flex flex-col gap-2.5">
        <p className={judulKolom}>Kondisi pribadimu</p>
        <Centang aktif={m.bersedia_relokasi} onUbah={(v) => ubah({ bersedia_relokasi: v })} judul="Bersedia pindah kota untuk bekerja" keterangan="Kalau tidak, profesi yang hanya ada di kota lain dan tidak bisa remote akan disaring." />
        <Centang aktif={m.punya_tanggungan} onUbah={(v) => ubah({ punya_tanggungan: v })} judul="Menanggung kebutuhan keluarga" keterangan="Kalau ya, stabilitas pekerjaan ikut dipertimbangkan." />
      </div>
    </div>
  )
}

function Likert({ judul, keterangan, butir, skala, jawaban, pilih }: {
  judul: string; keterangan: string; butir: Butir[]; skala: string[]
  jawaban: Record<string, number>; pilih: (kode: string, nilai: number) => void
}) {
  const terisi = butir.filter((b) => jawaban[b.kode]).length
  return (
    <div>
      <h1 className="text-[17px] font-bold tracking-tight text-slate-900">{judul}</h1>
      <p className="mt-1 text-[13px] leading-relaxed text-slate-500">{keterangan}</p>
      <p className="mt-2 inline-flex rounded-md bg-violet-50 px-2 py-1 text-[11.5px] font-semibold text-violet-700">{terisi} dari {butir.length} terjawab</p>
      <ol className="mt-4 flex flex-col gap-2.5">
        {butir.map((b, i) => {
          const sudah = !!jawaban[b.kode]
          return (
            <li key={b.kode} className={`rounded-xl border px-4 py-3.5 transition-colors ${sudah ? 'border-violet-200 bg-violet-50/40' : 'border-slate-200 bg-white'}`}>
              <p className="text-[13.5px] font-semibold leading-snug text-slate-900">{i + 1}. {b.teks}</p>
              <div className="mt-3 flex items-center justify-between gap-2" role="radiogroup" aria-label={b.teks}>
                <span className="hidden w-24 text-[11.5px] leading-tight text-slate-400 sm:block">{skala[0]}</span>
                <div className="flex flex-1 items-center justify-between gap-1.5 sm:justify-center sm:gap-3">
                  {skala.map((nama, n) => {
                    const on = jawaban[b.kode] === n + 1
                    return (
                      <button key={nama} type="button" role="radio" aria-checked={on} aria-label={nama} title={nama} onClick={() => pilih(b.kode, n + 1)}
                        className={`grid size-10 place-items-center rounded-full border text-[13.5px] font-semibold transition-colors ${on ? 'border-violet-600 bg-violet-600 text-white' : 'border-slate-300 bg-white text-slate-600 hover:border-violet-400'}`}>
                        {n + 1}
                      </button>
                    )
                  })}
                </div>
                <span className="hidden w-24 text-right text-[11.5px] leading-tight text-slate-400 sm:block">{skala[4]}</span>
              </div>
              <div className="mt-1.5 flex justify-between text-[11px] text-slate-400 sm:hidden"><span>{skala[0]}</span><span>{skala[4]}</span></div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

/**
 * Langkah keahlian.
 *
 * Tiga hal yang membuat daftar 160-an skill tetap bisa dipakai:
 *   1. Pencarian mengenali nama lain ("ReactJS", "Postgres", "PBO").
 *   2. Skill yang sudah dipilih dikumpulkan di atas, tingkatnya diatur di sana.
 *   3. Skill yang tidak ada di daftar bisa diketik sendiri. Skill itu dicatat
 *      untuk memperluas basis data, tetapi belum ikut dihitung dalam skor.
 */
function PilihSkill({ k, skill, atur, lain, ubahLain }: {
  k: DataKuesioner; skill: Record<string, number>; atur: (id: string, tingkat: number) => void
  lain: string[]; ubahLain: (v: string[]) => void
}) {
  const [cari, setCari] = useState('')
  const kata = cari.trim().toLowerCase()
  const nama = useMemo(() => new Map(k.skill.map((s) => [s.id, s.nama])), [k])
  const kelompok = useMemo(() => {
    const peta = new Map<string, DataKuesioner['skill']>()
    for (const s of k.skill) {
      const kena = !kata || s.nama.toLowerCase().includes(kata) || s.kategori.toLowerCase().includes(kata) ||
        s.alias.some((a) => a.toLowerCase().includes(kata))
      if (kena) peta.set(s.kategori, [...(peta.get(s.kategori) ?? []), s])
    }
    return [...peta.entries()]
  }, [k, kata])

  const ketik = cari.trim()
  const sudahAda = k.skill.some((s) => s.nama.toLowerCase() === kata || s.alias.some((a) => a.toLowerCase() === kata)) ||
    lain.some((s) => s.toLowerCase() === kata)
  const bisaTambah = ketik.length >= 2 && ketik.length <= 40 && !sudahAda && lain.length < 20
  const terpilih = Object.entries(skill).sort((a, b) => b[1] - a[1])

  function tambahLain() {
    if (!bisaTambah) return
    ubahLain([...lain, ketik])
    setCari('')
  }

  return (
    <div>
      <h1 className="text-[17px] font-bold tracking-tight text-slate-900">Skill apa saja yang sudah kamu kuasai?</h1>
      <p className="mt-1 text-[13px] leading-relaxed text-slate-500">
        Pilih yang benar-benar pernah kamu pakai, lalu atur tingkatnya. Tidak perlu memilih sebanyak mungkin:
        yang dinilai adalah kemiripan dengan kebutuhan profesi, bukan jumlahnya.
      </p>

      {(terpilih.length > 0 || lain.length > 0) && (
        <section className="mt-4 rounded-2xl border border-violet-200 bg-violet-50/50 p-4">
          <h2 className="text-[13px] font-bold text-slate-900">Skill pilihanmu <span className="font-normal text-slate-500">({terpilih.length + lain.length})</span></h2>
          <ul className="mt-3 flex flex-col gap-2">
            {terpilih.map(([id, t]) => (
              <li key={id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white px-3 py-2 ring-1 ring-slate-200">
                <span className="min-w-0 flex-1 truncate text-[13.5px] font-semibold text-slate-900">{nama.get(id) ?? id}</span>
                <div className="flex items-center gap-1" role="radiogroup" aria-label={`Tingkat ${nama.get(id)}`}>
                  {[1, 2, 3].map((n) => (
                    <button key={n} type="button" role="radio" aria-checked={t === n} onClick={() => atur(id, n)}
                      className={`rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors ${t === n ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                      {k.tingkat_skill[String(n)]}
                    </button>
                  ))}
                  <button type="button" aria-label={`Hapus ${nama.get(id)}`} onClick={() => atur(id, 0)} className="ml-1 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
                    <X className="size-3.5" aria-hidden />
                  </button>
                </div>
              </li>
            ))}
          </ul>
          {lain.length > 0 && (
            <>
              <p className="mt-3 text-[11.5px] leading-relaxed text-slate-500">Skill lain yang kamu tambahkan (dicatat, belum ikut dihitung dalam skor):</p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {lain.map((s) => (
                  <li key={s} className="inline-flex items-center gap-1 rounded-full bg-white py-1 pl-3 pr-1.5 text-[12.5px] font-medium text-slate-700 ring-1 ring-slate-200">
                    {s}
                    <button type="button" aria-label={`Hapus ${s}`} onClick={() => ubahLain(lain.filter((x) => x !== s))} className="rounded-full p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
                      <X className="size-3" aria-hidden />
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      <div className="relative mt-4">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
        <input type="search" value={cari} onChange={(e) => setCari(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && kelompok.length === 0) { e.preventDefault(); tambahLain() } }}
          placeholder="Cari skill, mis. Python, ReactJS, Figma, jaringan"
          className="w-full rounded-full border border-slate-200 bg-white py-3 pl-11 pr-4 text-[13.5px] text-slate-900 outline-none placeholder:text-slate-400 focus:border-violet-400" />
      </div>

      {bisaTambah && (
        <button type="button" onClick={tambahLain} className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-dashed border-violet-400 px-3.5 py-2 text-[13px] font-semibold text-violet-700 hover:bg-violet-50">
          <Plus className="size-4" aria-hidden /> Tidak ada di daftar? Tambahkan “{ketik}”
        </button>
      )}

      <div className="mt-5 flex flex-col gap-5">
        {kelompok.length === 0 && <p className="text-[13px] text-slate-400">Tidak ada skill yang cocok dengan “{ketik}”.</p>}
        {kelompok.map(([kategori, daftar]) => (
          <section key={kategori}>
            <h2 className="text-[12px] font-bold uppercase tracking-wide text-slate-500">{kategori}</h2>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {daftar.map((s) => {
                const on = (skill[s.id] ?? 0) > 0
                return (
                  <button key={s.id} type="button" aria-pressed={on} onClick={() => atur(s.id, on ? 0 : 2)}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[13px] font-medium shadow-sm ring-1 transition-colors ${on ? 'bg-[#F1EBFF] text-[#7033FF] ring-[#DDD0FF]' : 'bg-white text-slate-900 ring-slate-200 hover:bg-slate-50'}`}>
                    {on && <Check className="size-3.5" strokeWidth={3} aria-hidden />}
                    {s.nama}
                  </button>
                )
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
