"""Memeriksa semua tautan bahan belajar masih bisa dibuka.

Jalankan sebelum demo atau pengujian:  python scripts/cek_tautan.py

Kode 200 berarti hidup. 403 dan 429 biasanya situs yang menolak permintaan
otomatis (bukan tautan mati); 302 pada situs Google adalah pengalihan bahasa.
Yang perlu diperiksa manual adalah 404, 5xx, dan ERR.
"""

from __future__ import annotations

import collections
import concurrent.futures as cf
import csv
import subprocess
from pathlib import Path

SUMBER = Path(__file__).resolve().parents[2] / "data" / "sumber"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def cek(url: str) -> tuple[str, str]:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-m", "25", "-A", UA,
                        "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() or "ERR", url


def main() -> None:
    urls: set[str] = set()
    for berkas in ("sumber_belajar.csv", "panduan_karier.csv"):
        with open(SUMBER / berkas, newline="", encoding="utf-8") as f:
            urls |= {b["url"] for b in csv.DictReader(f, delimiter="|")}
    with cf.ThreadPoolExecutor(12) as ex:
        hasil = sorted(ex.map(cek, sorted(urls)))
    print(dict(collections.Counter(kode for kode, _ in hasil)))
    for kode, url in hasil:
        if kode != "200":
            print(kode, url)


if __name__ == "__main__":
    main()
