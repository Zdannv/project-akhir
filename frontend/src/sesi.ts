// Tanpa login: hasil terakhir diingat di peramban supaya bisa dibuka lagi.
const KUNCI = 'pa.hasil_terakhir'

export function hasilTerakhir(): string | null {
  try {
    return localStorage.getItem(KUNCI)
  } catch {
    return null
  }
}

export function ingatHasil(id: string): void {
  try {
    localStorage.setItem(KUNCI, id)
  } catch {
    // Penyimpanan diblokir: aplikasinya tetap jalan, hanya tidak mengingat.
  }
}
