"""
01_dogrulama_ve_asr.py — Proje 1 (WHO 2026 standart nüfusu)
Girdi : 03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz , 02_agirliklar/agirliklar_100bin_ANALIZ.csv
Çıktı : 05_ciktilar/asr_dort_standart.csv.gz (ASR tam hassasiyet, 10.10.2026 düzeltmesi) , 05_ciktilar/dogrulama_raporu.txt
İşlem : (1) 75-79, 80-84, 85+ gruplarını kümülatif aralıklardan fark alarak türetir
        (2) yaş toplamlarını resmî 0_17 toplamıyla karşılaştırır
        (3) Segi ASR'sini IARC'ın yayımladığı ASR ile karşılaştırır (geçiş kapısı)
        (4) dört standartla ASR hesaplar
Çalıştırma: python3 04_betikler/01_dogrulama_ve_asr.py   (proje kök klasöründen)
"""
import csv, gzip
from collections import defaultdict

STD = ["segi_doll", "who2001", "gbd2021", "who2026"]
w = defaultdict(list)
for r in csv.DictReader(open("02_agirliklar/agirliklar_100bin_ANALIZ.csv")):
    for s in STD:
        w[s].append(float(r[s]))
for s in STD:
    assert len(w[s]) == 18 and abs(sum(w[s]) - 100000) < 0.01, s

cell = defaultdict(dict)
with gzip.open("03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz", "rt") as f:
    for r in csv.DictReader(f):
        k = (r["yil"], r["olcut"], r["cinsiyet"], r["ulke_kodu"], r["kanser_kodu"])
        cell[k][int(r["age_code"])] = (int(r["vaka"]), int(r["nufus"]), float(r["asr_iarc"]))

n = eksik = top_bozuk = negatif = sifir_nufus = 0
maxfark = 0.0; maxfark_k = None; fark_gt_005 = 0
out = gzip.open("05_ciktilar/asr_dort_standart.csv.gz", "wt", newline="")
wr = csv.writer(out)
wr.writerow(["yil", "olcut", "cinsiyet", "ulke_kodu", "kanser_kodu", "vaka_toplam", "nufus_toplam", "asr_iarc"] + ["asr_" + s for s in STD])
for k, v in cell.items():
    n += 1
    if not all(a in v for a in list(range(15)) + [115, 116, 117, 99]):
        eksik += 1; continue
    c = [v[a][0] for a in range(15)] + [v[115][0] - v[14][0], v[116][0] - v[115][0], v[117][0] - v[116][0]]
    p = [v[a][1] for a in range(15)] + [v[115][1] - v[14][1], v[116][1] - v[115][1], v[117][1] - v[116][1]]
    if sum(c) != v[99][0] or sum(p) != v[99][1]: top_bozuk += 1
    if min(c) < 0 or min(p) < 0: negatif += 1
    if min(p) == 0: sifir_nufus += 1; continue
    rate = [ci / pi * 1e5 for ci, pi in zip(c, p)]
    asr = {s: sum(ri * wi for ri, wi in zip(rate, w[s])) / 1e5 for s in STD}
    d = abs(round(asr["segi_doll"], 2) - v[99][2])
    if d > maxfark: maxfark, maxfark_k = d, k
    if d > 0.05: fark_gt_005 += 1
    wr.writerow(list(k) + [v[99][0], v[99][1], v[99][2]] + [repr(asr[s]) for s in STD])
out.close()

rapor = f"""DOĞRULAMA RAPORU
Hücre (yıl×ölçüt×cinsiyet×ülke×kanser): {n}
18 yaş grubu eksik olan            : {eksik}
Yaş toplamı ≠ resmî toplam         : {top_bozuk}
Negatif türetilmiş değer           : {negatif}
Sıfır nüfuslu yaş grubu (atlandı)  : {sifir_nufus}
Segi ASR − IARC ASR  en büyük |fark|: {maxfark:.2f}  ({maxfark_k})
|fark| > 0,05 olan hücre            : {fark_gt_005}
"""
open("05_ciktilar/dogrulama_raporu.txt", "w").write(rapor)
print(rapor)
