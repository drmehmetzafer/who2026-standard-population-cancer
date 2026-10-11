"""
02_ana_analiz.py — Proje 1 · OSF ön kaydını (10.10.2026 18:29 TSİ, osf.io/stb6m) birebir uygular. Çıktı hassasiyeti 6 ondalık (10.10.2026 düzeltmesi; sonuçlar 4 ondalıklı önceki çalıştırmayla birebir aynı).
Girdi : 03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz , 03_veri_ham/globocan_meta_2022_2024.json ,
        02_agirliklar/agirliklar_100bin_ANALIZ.csv
Çıktı : 05_ciktilar/T*_*.csv , 05_ciktilar/analiz_ozeti.txt
Çalıştırma (proje kökünden): python3 04_betikler/02_ana_analiz.py
Not   : HDI gerektiren H2 regresyonu ayrı betikte (03_h2_hdi.py), HDI dosyası gelince.
"""
import csv, gzip, json, math
from collections import defaultdict
import numpy as np
from scipy import stats

RNG = np.random.default_rng(20261010)
B = 2000
STD = ["segi_doll", "who2001", "gbd2021", "who2026"]
PAIRS = [(a, b) for i, a in enumerate(STD) for b in STD[i + 1:]]
OUT = "05_ciktilar/"

# ---------- ağırlıklar ----------
W = {s: [] for s in STD}
for r in csv.DictReader(open("02_agirliklar/agirliklar_100bin_ANALIZ.csv")):
    for s in STD: W[s].append(float(r[s]))
W = {s: np.array(v) for s, v in W.items()}

# ---------- meta ----------
meta = json.load(open("03_veri_ham/globocan_meta_2022_2024.json"))
SITE = {str(x["cancer"]): x["label"] for x in meta["meta2024"]["c"]}
CTRY = {}
for y in ("2022", "2024"):
    for x in meta["meta" + y]["p"]:
        if int(x["country"]) < 900: CTRY[str(x["country"])] = x["label"]
CHINA = {"160": "156"}  # 2022 kodu → 2024 kodu
def ckey(c): return CHINA.get(c, c)

# ---------- ham veri → yaşa özgü vektörler ----------
raw = defaultdict(dict)
with gzip.open("03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz", "rt") as f:
    for r in csv.DictReader(f):
        raw[(r["yil"], r["olcut"], r["cinsiyet"], ckey(r["ulke_kodu"]), r["kanser_kodu"])][int(r["age_code"])] = (int(r["vaka"]), int(r["nufus"]))
CELL = {}
for k, v in raw.items():
    c = [v[a][0] for a in range(15)] + [v[115][0] - v[14][0], v[116][0] - v[115][0], v[117][0] - v[116][0]]
    p = [v[a][1] for a in range(15)] + [v[115][1] - v[14][1], v[116][1] - v[115][1], v[117][1] - v[116][1]]
    c, p = np.array(c, float), np.array(p, float)
    rate = np.where(p > 0, c / np.where(p > 0, p, 1) * 1e5, 0.0)
    CELL[k] = dict(c=c, p=p, asr={s: float(rate @ W[s] / 1e5) for s in STD})
del raw

# ---------- kapsam (ön kayıt) ----------
MAIN = [("39", "0"), ("15", "0"), ("20", "2"), ("41", "0"), ("27", "1"), ("7", "0"), ("32", "0"),
        ("11", "0"), ("30", "0"), ("23", "2"), ("34", "0"), ("13", "0"), ("6", "0"), ("36", "0")]
EXCL = {"37", "38", "39", "40"}
MEAS = {"0": "insidans", "1": "mortalite"}
SEXN = {"0": "her_iki", "1": "erkek", "2": "kadin"}
common = {k[3] for k in CELL if k[0] == "2022"} & {k[3] for k in CELL if k[0] == "2024"}

def countries(yr):
    return sorted({k[3] for k in CELL if k[0] == yr} & (common if yr == "2022" else {k[3] for k in CELL}))

def vec(yr, m, sx, site, cs):
    ids, X = [], []
    for c in cs:
        d = CELL.get((yr, m, sx, c, site))
        if d is None or d["c"].sum() == 0: continue
        ids.append(c); X.append([d["asr"][s] for s in STD])
    return ids, np.array(X)

# ---------- ölçütler ----------
def rank_desc(x): return stats.rankdata(-x, method="average")
def spearman_mat(A, Bm):  # sütun bazında, A,B: (B, n)
    ra = np.apply_along_axis(stats.rankdata, 1, A); rb = np.apply_along_axis(stats.rankdata, 1, Bm)
    ra -= ra.mean(1, keepdims=True); rb -= rb.mean(1, keepdims=True)
    return (ra * rb).sum(1) / np.sqrt((ra ** 2).sum(1) * (rb ** 2).sum(1))
def rbo_ext(l1, l2, p=0.9):
    k = len(l1); s1, s2 = set(), set(); A = 0.0; X = 0
    for d in range(1, k + 1):
        a, b = l1[d - 1], l2[d - 1]
        if a == b: X += 1
        else: X += (a in s2) + (b in s1)
        s1.add(a); s2.add(b); A += (X / d) * p ** d
    return (X / k) * p ** k + (1 - p) / p * A
def boot_idx(n): return RNG.integers(0, n, size=(B, n))
def ci(x): return np.percentile(x, [2.5, 97.5])

summary = []
def say(s): print(s); summary.append(s)

# ================= H1 =================
tot = gt1 = 0
for k, d in CELL.items():
    if k[4] in ("37", "38"): continue
    if d["c"][12:].sum() > 0:
        tot += 1; gt1 += d["asr"]["who2026"] > d["asr"]["segi_doll"]
say(f"H1: WHO2026/Segi > 1 olan hücre {gt1}/{tot} ({100*gt1/tot:.2f}%) [60+ yaşta vakası olan tüm hücreler]")

# ================= Ana tablo: sıra uyumu =================
T2 = []; H3 = {}; H4 = []
for yr in ("2024", "2022"):
    cs = countries(yr)
    for site, sx in MAIN:
        rho_m = {}
        for m in ("0", "1"):
            ids, X = vec(yr, m, sx, site, cs); n = len(ids)
            idx = boot_idx(n)
            ratio = X[:, 3] / X[:, 0]
            rows = {}
            for (a, b) in PAIRS:
                ia, ib = STD.index(a), STD.index(b)
                rho = stats.spearmanr(X[:, ia], X[:, ib])[0]
                tau = stats.kendalltau(X[:, ia], X[:, ib], variant="b")[0]
                rb = spearman_mat(X[idx, ia], X[idx, ib])
                tb = np.array([stats.kendalltau(X[j, ia], X[j, ib], variant="b")[0] for j in idx])
                ra, rbk = rank_desc(X[:, ia]), rank_desc(X[:, ib])
                la = [ids[i] for i in np.argsort(-X[:, ia], kind="stable")]
                lb = [ids[i] for i in np.argsort(-X[:, ib], kind="stable")]
                top = len(set(la[:10]) & set(lb[:10])) / 10
                dr = np.abs(ra - rbk)
                qa = np.ceil(5 * ra / n); qb = np.ceil(5 * rbk / n)
                rows[(a, b)] = dict(rho=rho, rb=rb)
                T2.append(dict(yil=yr, olcut=MEAS[m], kanser=SITE[site], cinsiyet=SEXN[sx], n=n, std_a=a, std_b=b,
                               rho=round(rho, 6), rho_lo=round(ci(rb)[0], 6), rho_hi=round(ci(rb)[1], 6),
                               tau_b=round(tau, 6), tau_lo=round(ci(tb)[0], 6), tau_hi=round(ci(tb)[1], 6),
                               top10=top, rbo=round(rbo_ext(la, lb), 4), kayma10=int((dr >= 10).sum()),
                               kayma20=int((dr >= 20).sum()), dilim_degisen=round(float((qa != qb).mean()), 6),
                               oran_ortanca=round(float(np.median(ratio)), 3) if (a, b) == ("segi_doll", "who2026") else "",
                               oran_q1=round(float(np.percentile(ratio, 25)), 3) if (a, b) == ("segi_doll", "who2026") else "",
                               oran_q3=round(float(np.percentile(ratio, 75)), 3) if (a, b) == ("segi_doll", "who2026") else ""))
            # H4
            prim = rows[("segi_doll", "who2026")]
            ex = [("segi_doll", "who2001"), ("segi_doll", "gbd2021"), ("who2001", "gbd2021")]
            mn = min(rows[e]["rho"] for e in ex)
            diff_b = prim["rb"] - np.min(np.vstack([rows[e]["rb"] for e in ex]), axis=0)
            H4.append(dict(yil=yr, olcut=MEAS[m], kanser=SITE[site], rho_segi_who26=round(prim["rho"], 6),
                           min_rho_mevcut=round(mn, 6), fark=round(prim["rho"] - mn, 6),
                           fark_lo=round(ci(diff_b)[0], 6), fark_hi=round(ci(diff_b)[1], 6)))
            rho_m[m] = (ids, X)
        # H3: eşleşmiş bootstrap (her iki ölçütte ortak ülkeler)
        (i0, X0), (i1, X1) = rho_m["0"], rho_m["1"]
        cm = sorted(set(i0) & set(i1)); a0 = X0[[i0.index(c) for c in cm]]; a1 = X1[[i1.index(c) for c in cm]]
        r0 = stats.spearmanr(a0[:, 0], a0[:, 3])[0]; r1 = stats.spearmanr(a1[:, 0], a1[:, 3])[0]
        idx = boot_idx(len(cm))
        d = spearman_mat(a0[idx, 0], a0[idx, 3]) - spearman_mat(a1[idx, 0], a1[idx, 3])
        H3[(yr, site)] = dict(yil=yr, kanser=SITE[site], cinsiyet=SEXN[sx], n=len(cm), rho_ins=round(r0, 6),
                              rho_mort=round(r1, 6), fark=round(r0 - r1, 6), fark_lo=round(ci(d)[0], 6), fark_hi=round(ci(d)[1], 6))

def wcsv(name, rows):
    with open(OUT + name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
wcsv("T2_sira_uyumu.csv", T2); wcsv("T_H3_ins_vs_mort.csv", list(H3.values())); wcsv("T_H4_yeni_vs_mevcut.csv", H4)

# H3 ve H4 testleri (2024 ve 2022 ayrı aileler)
for yr in ("2024", "2022"):
    sites13 = [v for (y, s), v in H3.items() if y == yr and s != "39"]
    k3 = sum(v["fark"] > 0 for v in sites13)
    p3 = stats.binomtest(k3, len(sites13), 0.5).pvalue
    h4 = [v for v in H4 if v["yil"] == yr]
    k4 = sum(v["fark"] < 0 for v in h4)
    p4 = stats.binomtest(k4, len(h4), 0.5).pvalue
    say(f"H3 [{yr}]: 13 bölgenin {k3}'ünde ρ_insidans > ρ_mortalite; işaret testi p = {p3:.4g}")
    say(f"H4 [{yr}]: {len(h4)} tabakanın {k4}'ünde ρ(Segi,WHO2026) < mevcut standart çiftlerinin en düşük ρ'su; işaret testi p = {p4:.4g}")

# ================= H2 (Spearman; regresyon HDI ile ayrı) =================
for yr in ("2024", "2022"):
    cs = countries(yr)
    for m in ("0", "1"):
        ids, X = vec(yr, m, "0", "39", cs)
        sh = np.array([CELL[(yr, m, "0", c, "39")]["p"][12:].sum() / CELL[(yr, m, "0", c, "39")]["p"].sum() for c in ids])
        ratio = X[:, 3] / X[:, 0]
        rho, p = stats.spearmanr(ratio, sh)
        idx = boot_idx(len(ids)); rb = spearman_mat(ratio[idx], sh[idx])
        lo, hi = ci(rb)
        say(f"H2 [{yr} {MEAS[m]}]: ρ(ASR oranı, 60+ payı) = {rho:.3f} (%95 GA {lo:.3f}–{hi:.3f}), p = {p:.3g}, n = {len(ids)}")

# ================= H5: ülke içi en sık kanser =================
H5 = []; H5L = []
for yr in ("2024", "2022"):
    cs = countries(yr)
    for m in ("0", "1"):
        for sx in ("0", "1", "2"):
            ch = n = 0
            for c in cs:
                best = {}
                for s in STD:
                    cand = [(CELL[k]["asr"][s], k[4]) for k in [(yr, m, sx, c, st) for st in SITE] if k in CELL and k[4] not in EXCL and CELL[k]["c"].sum() > 0]
                    if cand: best[s] = max(cand)[1]
                if len(best) < 4: continue
                n += 1
                if best["segi_doll"] != best["who2026"]:
                    ch += 1
                    H5L.append(dict(yil=yr, olcut=MEAS[m], cinsiyet=SEXN[sx], ulke=CTRY.get(c, c),
                                    segi=SITE[best["segi_doll"]], who2026=SITE[best["who2026"]]))
            lo, hi = stats.binomtest(ch, n).proportion_ci(method="wilson")
            H5.append(dict(yil=yr, olcut=MEAS[m], cinsiyet=SEXN[sx], n=n, degisen=ch, oran=round(ch / n, 6), lo=round(lo, 6), hi=round(hi, 6)))
            say(f"H5 [{yr} {MEAS[m]} {SEXN[sx]}]: en sık kanseri değişen ülke {ch}/{n} ({100*ch/n:.1f}%, Wilson %95 GA {100*lo:.1f}–{100*hi:.1f})")
wcsv("T3_en_sik_kanser_ozet.csv", H5); wcsv("T3_en_sik_kanser_ulkeler.csv", H5L)

open(OUT + "analiz_ozeti.txt", "w").write("\n".join(summary) + "\n")
