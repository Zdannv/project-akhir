"""Mengambil video tutorial YouTube untuk tiap technical skill.

Tautan video TIDAK ditulis tangan. Untuk tiap skill, skrip ini:

  1. membuka halaman pencarian YouTube ("tutorial <skill> bahasa indonesia",
     lalu tanpa "bahasa indonesia" kalau tidak ada yang cocok);
  2. menyaring hasilnya: durasi minimal 8 menit (bukan Shorts atau cuplikan)
     dan judulnya memuat nama skill atau salah satu aliasnya;
  3. mengambil dua teratas dan memastikan videonya masih ada lewat oEmbed.

Hasilnya ditulis ke data/sumber/video_tutorial.csv beserta judul, kanal, dan
durasi, supaya pengguna tahu apa yang akan dibukanya.

PENTING: pemilihannya otomatis. Tidak ada yang menonton video-video ini untuk
menilai mutunya; yang dijamin hanya bahwa videonya ada, cukup panjang, dan
judulnya sesuai. Saringan judul tidak sempurna ("dbt" bisa berarti terapi,
"Helm" bisa berarti helm motor), jadi hasilnya ditinjau dengan membaca
judulnya, dan yang meleset dicatat di data/sumber/video_ditolak.csv. Video di
daftar itu tidak akan dipilih lagi. Jalankan ulang untuk menyegarkan daftar:

    python scripts/ambil_video.py            # semua skill
    python scripts/ambil_video.py SK016      # skill tertentu
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
KB = AKAR / "data" / "kb" / "basis_pengetahuan.json"
KELUARAN = AKAR / "data" / "sumber" / "video_tutorial.csv"
DITOLAK = AKAR / "data" / "sumber" / "video_ditolak.csv"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
MENIT_MIN = 8
PER_SKILL = 2

# Kata yang terlalu umum untuk membuktikan sebuah judul membahas skill-nya.
UMUM = {"and", "the", "for", "with", "basic", "basics", "design", "data", "management", "tools",
        "tool", "testing", "test", "system", "systems", "security", "concepts", "konsep", "web",
        "mobile", "cloud", "network", "networking", "analysis", "programming", "development",
        "software", "process", "processes", "learning", "model", "platform", "framework",
        "administration", "architecture", "optimization", "engineering", "product", "project",
        "game", "writing", "skill", "technical", "digital", "marketing", "database", "computing"}


def buka(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "id-ID,id;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def kunci(nama: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*", " ", nama).strip()


def kata_penanda(skill: dict) -> set[str]:
    """Kata dan frasa yang, kalau muncul di judul, menandakan videonya relevan."""
    sumber = [kunci(skill["nama"]), *re.findall(r"\((.*?)\)", skill["nama"]), *skill.get("alias", [])]
    penanda: set[str] = set()
    for teks in sumber:
        for bagian in re.split(r"[/,&]| dan ", teks):
            bagian = bagian.strip().lower()
            if not bagian:
                continue
            if bagian not in UMUM and len(bagian) >= 2:
                penanda.add(bagian)                      # frasa utuh: "power bi", "c++"
            for kata in re.findall(r"[a-z0-9+#.]+", bagian):
                if len(kata) >= 4 and kata not in UMUM:
                    penanda.add(kata)
    return penanda


def relevan(judul: str, penanda: set[str]) -> bool:
    j = f" {judul.lower()} "
    for p in penanda:
        # Penanda pendek ("r", "go", "c#") harus berdiri sebagai kata sendiri.
        if len(p) <= 3:
            if re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9+#])", j):
                return True
        elif p in j:
            return True
    return False


def detik(teks: str | None) -> int:
    if not teks:
        return 0
    bagian = [int(x) for x in re.findall(r"\d+", teks)]
    return sum(b * 60 ** i for i, b in enumerate(reversed(bagian)))


def cari(kueri: str) -> list[dict]:
    html = buka("https://www.youtube.com/results?hl=id&gl=ID&search_query=" + urllib.parse.quote_plus(kueri))
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        return []
    hasil: list[dict] = []

    def jalan(o) -> None:
        if isinstance(o, dict):
            v = o.get("videoRenderer")
            if v and v.get("videoId") and "lengthText" in v:      # siaran langsung tidak punya durasi
                hasil.append({
                    "id": v["videoId"],
                    "judul": "".join(r["text"] for r in v["title"].get("runs", [])),
                    "kanal": (v.get("ownerText", {}).get("runs") or [{}])[0].get("text", ""),
                    "durasi": v["lengthText"].get("simpleText", ""),
                })
            for x in o.values():
                jalan(x)
        elif isinstance(o, list):
            for x in o:
                jalan(x)

    jalan(json.loads(m.group(1)))
    return hasil


def masih_ada(video_id: str) -> dict | None:
    """oEmbed hanya menjawab untuk video yang publik dan belum dihapus."""
    try:
        return json.loads(buka("https://www.youtube.com/oembed?format=json&url="
                               + urllib.parse.quote(f"https://www.youtube.com/watch?v={video_id}")))
    except Exception:
        return None


def ditolak() -> set[str]:
    if not DITOLAK.exists():
        return set()
    with open(DITOLAK, newline="", encoding="utf-8") as f:
        return {b["url"].rsplit("=", 1)[-1] for b in csv.DictReader(f, delimiter="|")}


def untuk_skill(skill: dict, tolak: set[str] = frozenset()) -> list[dict]:
    penanda = kata_penanda(skill)
    nama = kunci(skill["nama"])
    terpilih: list[dict] = []
    # Nama satu-dua huruf ("R", "C#") terlalu rancu sebagai kata kunci tunggal.
    jelas = f"bahasa pemrograman {nama}" if len(nama) <= 2 else nama
    for kueri in (f"tutorial {jelas} bahasa indonesia", f"{jelas} tutorial for beginners"):
        try:
            kandidat = cari(kueri)
        except Exception as e:  # jaringan: lewati kueri ini, jangan gagalkan seluruh proses
            print(f"   ! {kueri}: {e}", file=sys.stderr)
            kandidat = []
        for v in kandidat:
            if len(terpilih) >= PER_SKILL:
                break
            if detik(v["durasi"]) < MENIT_MIN * 60 or not relevan(v["judul"], penanda):
                continue
            if v["id"] in tolak or any(t["id"] == v["id"] for t in terpilih):
                continue
            info = masih_ada(v["id"])
            if info:
                terpilih.append({**v, "judul": info["title"], "kanal": info["author_name"]})
        if len(terpilih) >= PER_SKILL:
            break
        time.sleep(0.4)
    return terpilih


def main() -> None:
    skill = [s for s in json.loads(KB.read_text(encoding="utf-8"))["skill"] if s["tipe"] == "hard_skill"]
    hanya = set(sys.argv[1:])

    lama: dict[str, list[list[str]]] = {}
    if KELUARAN.exists():
        with open(KELUARAN, newline="", encoding="utf-8") as f:
            for b in csv.DictReader(f, delimiter="|"):
                lama.setdefault(b["skill_id"], []).append([b[k] for k in ("skill_id", "judul", "kanal", "durasi", "url")])

    tolak = ditolak()
    baris: list[list[str]] = []
    kosong: list[str] = []
    for i, s in enumerate(skill, 1):
        if hanya and s["id"] not in hanya:
            baris += lama.get(s["id"], [])
            continue
        video = untuk_skill(s, tolak)
        print(f"[{i}/{len(skill)}] {s['id']} {s['nama']}: {len(video)} video", flush=True)
        if not video:
            kosong.append(s["nama"])
        for v in video:
            # '|' di judul akan merusak pemisah kolom.
            bersih = lambda t: " ".join(t.replace("|", "-").replace("\\", "").split())  # noqa: E731
            baris.append([s["id"], bersih(v["judul"]), bersih(v["kanal"]), v["durasi"],
                          f"https://www.youtube.com/watch?v={v['id']}"])
        time.sleep(0.5)

    with open(KELUARAN, "w", newline="", encoding="utf-8") as f:
        # Tanpa tanda kutip dan tanpa escape: judul ditulis apa adanya, "|" sudah dibuang.
        w = csv.writer(f, delimiter="|", quoting=csv.QUOTE_NONE, quotechar=None)
        w.writerow(["skill_id", "judul", "kanal", "durasi", "url"])
        w.writerows(baris)
    print(f"\n{len(baris)} video untuk {len({b[0] for b in baris})} skill -> {KELUARAN.relative_to(AKAR)}")
    if kosong:
        print("Tanpa video yang lolos saringan:", "; ".join(kosong))


if __name__ == "__main__":
    main()
