"""06_ek_tablo_tum_bolgeler.py — Ek Tablo: 33 bölgenin tamamı, Segi–Doll ↔ WHO 2026 (nokta tahminleri). Proje kökünden."""
import csv, gzip, json
from collections import defaultdict
import numpy as np
from scipy import stats
meta = json.load(open("03_veri_ham/globocan_meta_2022_2024.json"))
SITE = {str(x["cancer"]): x["label"] for x in meta["meta2024"]["c"]}
MALE = {"26", "27", "28"}; FEM = {"20", "21", "22", "23", "24", "25"}
A = defaultdict(dict)
for r in csv.DictReader(gzip.open("05_ciktilar/asr_dort_standart.csv.gz", "rt")):
    A[(r["yil"], r["olcut"], r["cinsiyet"], r["kanser_kodu"])][r["ulke_kodu"].replace("160", "156")] = (float(r["asr_segi_doll"]), float(r["asr_who2026"]), int(r["vaka_toplam"]))
out = []
for yr in ("2024", "2022"):
    for site in sorted({k[3] for k in A if k[3] not in ("37", "38", "39", "40")}, key=int):
        sx = "1" if site in MALE else "2" if site in FEM else "0"
        for m, mn in (("0", "insidans"), ("1", "mortalite")):
            v = [x for x in A[(yr, m, sx, site)].values() if x[2] > 0]
            if len(v) < 10: continue
            a = np.array([x[0] for x in v]); b = np.array([x[1] for x in v])
            ra, rb = stats.rankdata(-a), stats.rankdata(-b)
            ia, ib = np.argsort(-a)[:10], np.argsort(-b)[:10]
            out.append(dict(yil=yr, kanser=SITE[site], cinsiyet={"0": "her_iki", "1": "erkek", "2": "kadin"}[sx], olcut=mn, n=len(v),
                            rho=round(stats.spearmanr(a, b)[0], 6), tau_b=round(stats.kendalltau(a, b)[0], 6),
                            top10=len(set(ia) & set(ib)) / 10, kayma20=int((np.abs(ra - rb) >= 20).sum()),
                            oran_ortanca=round(float(np.median(b / a)), 3)))
with open("05_ciktilar/T_S2_tum_bolgeler.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
low = sorted([r for r in out if r["yil"] == "2024"], key=lambda r: r["rho"])[:8]
for r in low: print(r["kanser"], r["olcut"], r["n"], r["rho"], r["top10"], r["kayma20"], r["oran_ortanca"])
print(len(out))
