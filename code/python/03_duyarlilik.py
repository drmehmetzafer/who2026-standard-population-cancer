"""03 — Registered sensitivity analyses: all cancers excluding non-melanoma skin cancer, countries with ≥1 million
inhabitants (total population), and stratification by sex. Writes results/tables/T_S1_duyarlilik.csv.
Run from the repository root: python3 code/python/03_duyarlilik.py
Comments in the code body are in Turkish."""
import csv, gzip
from collections import defaultdict
from scipy import stats
A = defaultdict(dict)
for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt")):
    A[(r["yil"], r["olcut"], r["cinsiyet"], r["kanser_kodu"])][r["ulke_kodu"].replace("160", "156")] = (float(r["asr_segi_doll"]), float(r["asr_who2026"]), int(r["nufus_toplam"]), int(r["vaka_toplam"]))
NAME = {"39": "All cancers", "40": "All cancers excl. C44", "15": "Lung", "41": "Colorectum", "7": "Stomach", "32": "Thyroid", "11": "Liver",
        "30": "Bladder", "34": "NHL", "13": "Pancreas", "6": "Oesophagus", "36": "Leukaemia", "20": "Breast", "27": "Prostate", "23": "Cervix"}
MEAS = {"0": "insidans", "1": "mortalite"}; SEX = {"0": "her_iki", "1": "erkek", "2": "kadin"}
out = []
POP = {(k[0], c): v[2] for k, d in A.items() if k[1] == "0" and k[2] == "0" and k[3] == "39" for c, v in d.items()}  # both-sexes population
def rho(d, popmin=0, yr=None):
    # the ≥1 million threshold is applied to the country's total (both-sexes) population (corrected 11 Oct 2026)
    v = [x for c, x in d.items() if x[3] > 0 and (popmin == 0 or POP[(yr, c)] >= popmin)]
    a, b = [x[0] for x in v], [x[1] for x in v]
    return len(v), stats.spearmanr(a, b)[0]
for yr in ("2024", "2022"):
    for m in ("0", "1"):
        for site in ["39", "40", "15", "41", "7", "32", "11", "30", "34", "13", "6", "36"]:
            for sx in ("0", "1", "2"):
                d = A[(yr, m, sx, site)]
                n, r = rho(d); n2, r2 = rho(d, 1_000_000, yr)
                out.append(dict(yil=yr, olcut=MEAS[m], kanser=NAME[site], cinsiyet=SEX[sx], n=n, rho=round(r, 6), n_1milyon_ustu=n2, rho_1milyon_ustu=round(r2, 6)))
        for site, sx in (("20", "2"), ("27", "1"), ("23", "2")):
            d = A[(yr, m, sx, site)]; n, r = rho(d); n2, r2 = rho(d, 1_000_000, yr)
            out.append(dict(yil=yr, olcut=MEAS[m], kanser=NAME[site], cinsiyet=SEX[sx], n=n, rho=round(r, 6), n_1milyon_ustu=n2, rho_1milyon_ustu=round(r2, 6)))
with open("results/tables/T_S1_duyarlilik.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for r in out:
    if r["yil"] == "2024" and r["kanser"].startswith("All"): print(r)
