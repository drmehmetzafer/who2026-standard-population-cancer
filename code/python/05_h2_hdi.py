"""05 — H2: Huber robust regression (k = 1.345) of the ASR ratio WHO 2026/Segi–Doll on the share aged ≥60, HDI group
and their interaction (registered model), plus main-effects and log-ratio models; country bootstrap inference.
HDI 2023 from the UNDP Human Development Report 2025 (data/raw/HDI_2023_UNDP_HDR2025.csv).
Run from the repository root: python3 code/python/05_h2_hdi.py
Comments in the code body are in Turkish."""
import csv, gzip, json
import numpy as np
from scipy import stats
RNG = np.random.default_rng(20261010); B = 2000
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
ISO = {}
for y in ("2022", "2024"):
    for p in meta["meta" + y]["p"]:
        if int(p["country"]) < 900: ISO[str(p["country"])] = p["country_iso3"]
HDI = {r["iso3"]: r["hdi_group"] for r in csv.DictReader(open("data/raw/HDI_2023_UNDP_HDR2025.csv"))}
GROUPS = ["Very High", "High", "Medium", "Low"]

raw = {}
with gzip.open("data/raw/globocan_yasaozgu_2022_2024.csv.gz", "rt") as f:
    for r in csv.DictReader(f):
        if r["kanser_kodu"] == "39" and r["cinsiyet"] == "0" and r["olcut"] == "0":
            raw.setdefault((r["yil"], r["ulke_kodu"]), {})[int(r["age_code"])] = int(r["nufus"])
P60 = {k: (v[12] + v[13] + v[14] + v[117] - v[14]) / v[99] for k, v in raw.items()}
ASR = {}
for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt")):
    if r["kanser_kodu"] == "39" and r["cinsiyet"] == "0":
        ASR[(r["yil"], r["olcut"], r["ulke_kodu"])] = float(r["asr_who2026"]) / float(r["asr_segi_doll"])

def huber(X, y, k=1.345, it=100):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(it):
        r = y - X @ b; s = np.median(np.abs(r - np.median(r))) / 0.6745 or 1e-9
        u = np.abs(r / s); w = np.where(u <= k, 1.0, k / u)
        bn = np.linalg.lstsq(X * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)[0]
        if np.max(np.abs(bn - b)) < 1e-10: b = bn; break
        b = bn
    return b, w

def design(sh, g, inter):
    cols = [np.ones_like(sh), sh] + [(g == G).astype(float) for G in GROUPS[1:]]
    if inter: cols += [sh * (g == G) for G in GROUPS[1:]]
    return np.column_stack(cols)

def bp(bs): return 2 * min((bs <= 0).mean(), (bs >= 0).mean())

out = []; lines = []
H3P = {"2024": 0.003418, "2022": 0.003418}; H4P = {"2024": 7.451e-09, "2022": 7.451e-09}
for yr in ("2024", "2022"):
    for m, mn in (("0", "insidans"), ("1", "mortalite")):
        ids = [c for (y, mm, c) in ASR if y == yr and mm == m and HDI.get(ISO.get(c)) in GROUPS]
        miss = len([c for (y, mm, c) in ASR if y == yr and mm == m]) - len(ids)
        y_ = np.array([ASR[(yr, m, c)] for c in ids]); sh = np.array([100 * P60[(yr, c)] for c in ids])
        shc = sh - np.median(sh); g = np.array([HDI[ISO[c]] for c in ids])
        for tr, yy in (("oran", y_), ("log_oran", np.log(y_))):
            for inter in (False, True):
                X = design(shc, g, inter); b, w = huber(X, yy)
                idx = RNG.integers(0, len(ids), size=(B, len(ids)))
                bs = np.array([huber(design(shc[i], g[i], inter), yy[i])[0] for i in idx])
                row = dict(yil=yr, olcut=mn, bagimli=tr, model="etkilesimli" if inter else "ana_etki", n=len(ids), hdi_eksik=miss,
                           egim_60plus_refVH=round(b[1], 5), lo=round(np.percentile(bs[:, 1], 2.5), 5), hi=round(np.percentile(bs[:, 1], 97.5), 5),
                           p_boot=round(bp(bs[:, 1]), 5), dusuk_agirlikli_ulke=int((w < 1).sum()))
                if inter:
                    for j, G in enumerate(GROUPS[1:]):
                        sl = bs[:, 1] + bs[:, 5 + j]
                        row[f"egim_{G.replace(' ', '')}"] = f"{b[1] + b[5 + j]:.5f} ({np.percentile(sl, 2.5):.5f}–{np.percentile(sl, 97.5):.5f})"
                out.append(row)
                if tr == "oran" and not inter:
                    lines.append(f"H2 [{yr} {mn}] Huber, ana etki (60+ % + HDI): eğim {b[1]:.4f} / 1 puan 60+ (%95 GA {row['lo']:.4f}–{row['hi']:.4f}), bootstrap p = {row['p_boot']:.4g}, n = {len(ids)}, HDI eksik {miss}")
    # Holm — registered family per release: H2 incidence and H2 mortality (registered interaction model, ratio scale), H3, H4
    ps = {f"H2_{m}": max(r["p_boot"], 1 / B) for r in out for m in [r["olcut"]] if r["yil"] == yr and r["bagimli"] == "oran" and r["model"] == "etkilesimli"}
    ps.update({"H3": H3P[yr], "H4": H4P[yr]})
    order = sorted(ps, key=ps.get); adj = {}; prev = 0
    for i, h in enumerate(order):
        prev = max(prev, min(1, (len(ps) - i) * ps[h])); adj[h] = prev
    lines.append(f"Holm [{yr}]: " + " · ".join(f"{h} p={ps[h]:.3g} → adjusted {adj[h]:.3g}" for h in sorted(ps)))
keys = sorted({k for r in out for k in r}, key=lambda k: list(out[-1]).index(k) if k in out[-1] else 99)
with open("results/tables/T_H2_huber_hdi.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(out[-1].keys())); wr.writeheader(); wr.writerows(out)
open("results/tables/analiz_ozeti_H2.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
