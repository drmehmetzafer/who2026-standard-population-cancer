"""03_duyarlilik.py — ön kayıttaki duyarlılık analizleri (nokta tahminleri). Proje kökünden çalıştırın."""
import csv, gzip
from collections import defaultdict
from scipy import stats
A = defaultdict(dict)
for r in csv.DictReader(gzip.open("05_ciktilar/asr_dort_standart.csv.gz", "rt")):
    A[(r["yil"], r["olcut"], r["cinsiyet"], r["kanser_kodu"])][r["ulke_kodu"].replace("160", "156")] = (float(r["asr_segi_doll"]), float(r["asr_who2026"]), int(r["nufus_toplam"]), int(r["vaka_toplam"]))
NAME = {"39": "All cancers", "40": "All cancers excl. C44", "15": "Lung", "41": "Colorectum", "7": "Stomach", "32": "Thyroid", "11": "Liver",
        "30": "Bladder", "34": "NHL", "13": "Pancreas", "6": "Oesophagus", "36": "Leukaemia", "20": "Breast", "27": "Prostate", "23": "Cervix"}
MEAS = {"0": "insidans", "1": "mortalite"}; SEX = {"0": "her_iki", "1": "erkek", "2": "kadin"}
out = []
def rho(d, popmin=0):
    v = [x for x in d.values() if x[3] > 0 and x[2] >= popmin]
    a, b = [x[0] for x in v], [x[1] for x in v]
    return len(v), stats.spearmanr(a, b)[0]
for yr in ("2024", "2022"):
    for m in ("0", "1"):
        for site in ["39", "40", "15", "41", "7", "32", "11", "30", "34", "13", "6", "36"]:
            for sx in ("0", "1", "2"):
                d = A[(yr, m, sx, site)]
                n, r = rho(d); n2, r2 = rho(d, 1_000_000)
                out.append(dict(yil=yr, olcut=MEAS[m], kanser=NAME[site], cinsiyet=SEX[sx], n=n, rho=round(r, 6), n_1milyon_ustu=n2, rho_1milyon_ustu=round(r2, 6)))
        for site, sx in (("20", "2"), ("27", "1"), ("23", "2")):
            d = A[(yr, m, sx, site)]; n, r = rho(d); n2, r2 = rho(d, 1_000_000)
            out.append(dict(yil=yr, olcut=MEAS[m], kanser=NAME[site], cinsiyet=SEX[sx], n=n, rho=round(r, 6), n_1milyon_ustu=n2, rho_1milyon_ustu=round(r2, 6)))
with open("05_ciktilar/T_S1_duyarlilik.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for r in out:
    if r["yil"] == "2024" and r["kanser"].startswith("All"): print(r)
