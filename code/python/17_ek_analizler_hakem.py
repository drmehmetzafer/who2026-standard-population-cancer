"""17_ek_analizler_hakem.py — Additional (post hoc) analyses added after internal review, and registered H3 within sex.
All are post hoc (not preregistered) and are reported as such.
Run from the project root. Inputs: data/raw/globocan_yasaozgu_2022_2024.csv.gz, data/raw/globocan_meta_2022_2024.json,
data/weights/agirliklar_100bin_ANALIZ.csv, results/tables/T_H2_huber_hdi.csv.
Outputs: results/tables/T_S8_benchmark.csv, T_S9_veri_kalitesi.csv, T_S10_standarttan_bagimsiz.csv,
T_S11_erkek_kadin_orani.csv, T_S6b_1milyon_duzeltilmis.csv, ek_analiz_ozeti.txt
A1 benchmark: rank change between releases (Segi–Doll, 2022 vs 2024) and between existing standards, vs Segi–Doll → WHO 2026.
A2 data quality: GLOBOCAN mortality method (1, 2a, 2b = national/subnational death records; 3a–3c, 4 = estimated from incidence).
A3 standard-free and truncated measures: cumulative risk 0–74, ASR truncated 0–74 and 0–84.
A4 registered index 8: change in male:female ASR ratio (non-sex-specific sites).
A5 corrected ≥1 million sensitivity (threshold on both-sexes population, not the sex-specific population).
"""
import csv, gzip, json
from collections import defaultdict
import numpy as np
from scipy import stats

RNG = np.random.default_rng(20261010); B = 2000
STD = ["segi_doll", "who2001", "gbd2021", "who2026"]
LAB = {"segi_doll": "Segi–Doll", "who2001": "WHO 2000–2025", "gbd2021": "GBD 2021", "who2026": "WHO 2026"}
W = {s: [] for s in STD}
for r in csv.DictReader(open("data/weights/agirliklar_100bin_ANALIZ.csv")):
    for s in STD: W[s].append(float(r[s]))
W = {s: np.array(v) for s, v in W.items()}
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
SITE = {str(x["cancer"]): x["label"] for x in meta["meta2024"]["c"]}
P24 = {str(x["country"]): x for x in meta["meta2024"]["p"] if int(x["country"]) < 900}
CHINA = {"160": "156"}
raw = defaultdict(dict)
with gzip.open("data/raw/globocan_yasaozgu_2022_2024.csv.gz", "rt") as f:
    for r in csv.DictReader(f):
        raw[(r["yil"], r["olcut"], r["cinsiyet"], CHINA.get(r["ulke_kodu"], r["ulke_kodu"]), r["kanser_kodu"])][int(r["age_code"])] = (int(r["vaka"]), int(r["nufus"]))
CELL = {}
for k, v in raw.items():
    c = np.array([v[a][0] for a in range(15)] + [v[115][0] - v[14][0], v[116][0] - v[115][0], v[117][0] - v[116][0]], float)
    p = np.array([v[a][1] for a in range(15)] + [v[115][1] - v[14][1], v[116][1] - v[115][1], v[117][1] - v[116][1]], float)
    CELL[k] = dict(c=c, p=p, r=np.where(p > 0, c / np.where(p > 0, p, 1) * 1e5, 0.0))
del raw
def asr(d, s, upto=18):
    w = W[s][:upto]; return float(d["r"][:upto] @ w / w.sum())  # truncated ASR: weights renormalised over included ages
def cr74(d):  # cumulative risk 0–74 (%), standard-free
    return 100 * (1 - np.exp(-5 * d["r"][:15].sum() / 1e5))
c24 = {k[3] for k in CELL if k[0] == "2024"}; c22 = {k[3] for k in CELL if k[0] == "2022"}; COMMON = sorted(c24 & c22)
MAIN = [("39", "0"), ("15", "0"), ("20", "2"), ("41", "0"), ("27", "1"), ("7", "0"), ("32", "0"),
        ("11", "0"), ("30", "0"), ("23", "2"), ("34", "0"), ("13", "0"), ("6", "0"), ("36", "0")]
MEAS = {"0": "incidence", "1": "mortality"}
def rk(x): return stats.rankdata(-np.asarray(x), method="average")
def agree(x, y, ids):
    x, y = np.asarray(x), np.asarray(y); ra, rb = rk(x), rk(y); d = np.abs(ra - rb)
    la = [ids[i] for i in np.argsort(-x, kind="stable")][:10]; lb = [ids[i] for i in np.argsort(-y, kind="stable")][:10]
    return dict(n=len(ids), rho=stats.spearmanr(x, y)[0], top10=len(set(la) & set(lb)), mv10=int((d >= 10).sum()), mv20=int((d >= 20).sum()))
def boot_rho(x, y):
    x, y = np.asarray(x), np.asarray(y); n = len(x); idx = RNG.integers(0, n, size=(B, n))
    v = np.array([stats.spearmanr(x[i], y[i])[0] for i in idx]); return np.percentile(v, [2.5, 97.5])
def get(yr, m, sx, site, cs, f):
    ids, v = [], []
    for c in cs:
        d = CELL.get((yr, m, sx, c, site))
        if d is None or d["c"].sum() == 0: continue
        ids.append(c); v.append(f(d))
    return ids, v
summ = []
def say(s): print(s); summ.append(s)
def wcsv(name, rows):
    with open("results/tables/" + name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def r6(x): return round(float(x), 6)

# ---------- A1 benchmark ----------
T2ALL = list(csv.DictReader(open("results/tables/T2_sira_uyumu.csv")))
S8 = []
for site, sx in MAIN:
    for m in ("0", "1"):
        # release benchmark: same standard (Segi–Doll), 2022 vs 2024, 185 common countries with cases in both
        ids = [c for c in COMMON if all((y, m, sx, c, site) in CELL and CELL[(y, m, sx, c, site)]["c"].sum() > 0 for y in ("2022", "2024"))]
        a = [asr(CELL[("2022", m, sx, c, site)], "segi_doll") for c in ids]; b = [asr(CELL[("2024", m, sx, c, site)], "segi_doll") for c in ids]
        rows = [("release: Segi–Doll 2022 vs 2024", agree(a, b, ids), (a, b))]
        ids24, X = get("2024", m, sx, site, sorted(c24), lambda d: [asr(d, s) for s in STD]); X = np.array(X)
        for s1, s2 in [("segi_doll", "who2001"), ("segi_doll", "gbd2021"), ("who2001", "gbd2021"),
                       ("who2001", "who2026"), ("gbd2021", "who2026"), ("segi_doll", "who2026")]:
            rows.append((f"{LAB[s1]} vs {LAB[s2]}", agree(X[:, STD.index(s1)], X[:, STD.index(s2)], ids24), (X[:, STD.index(s1)], X[:, STD.index(s2)])))
        for lab, g, xy in rows:
            lo, hi = ("", "")
            if site == "39":
                if lab.startswith("release"): lo, hi = boot_rho(*xy)
                else:  # standard pairs: use the CI already reported in T2 (same seed/procedure) for consistency
                    s1, s2 = [k for k, v in LAB.items() if v == lab.split(" vs ")[0]][0], [k for k, v in LAB.items() if v == lab.split(" vs ")[1]][0]
                    t = [r for r in T2ALL if r["yil"] == "2024" and r["kanser"] == SITE[site] and r["olcut"] == {"0": "insidans", "1": "mortalite"}[m]
                         and {r["std_a"], r["std_b"]} == {s1, s2}][0]
                    lo, hi = float(t["rho_lo"]), float(t["rho_hi"])
            S8.append(dict(site=SITE[site], sex={"0": "both", "1": "male", "2": "female"}[sx], measure=MEAS[m], comparison=lab, n=g["n"],
                           rho=r6(g["rho"]), rho_lo=r6(lo) if lo != "" else "", rho_hi=r6(hi) if hi != "" else "",
                           top10=g["top10"], moved_ge10=g["mv10"], moved_ge20=g["mv20"]))
wcsv("T_S8_benchmark.csv", S8)
for m in ("incidence", "mortality"):
    for r in S8:
        if r["site"] == "All cancers" and r["measure"] == m:
            say(f"A1 {m}: {r['comparison']}: n={r['n']} rho={r['rho']:.3f} ({r['rho_lo']}–{r['rho_hi']}) top10={r['top10']}/10 ≥10={r['moved_ge10']} ≥20={r['moved_ge20']}")
# strata where Segi→WHO2026 moves more countries ≥20 places than the release change
for m in ("incidence", "mortality"):
    sub = [r for r in S8 if r["measure"] == m]
    k = sum(1 for site, sx in MAIN if [r for r in sub if r["site"] == SITE[site] and r["comparison"] == "Segi–Doll vs WHO 2026"][0]["moved_ge20"] >
            [r for r in sub if r["site"] == SITE[site] and r["comparison"].startswith("release")][0]["moved_ge20"])
    kr = sum(1 for site, sx in MAIN if [r for r in sub if r["site"] == SITE[site] and r["comparison"] == "Segi–Doll vs WHO 2026"][0]["rho"] <
             [r for r in sub if r["site"] == SITE[site] and r["comparison"].startswith("release")][0]["rho"])
    say(f"A1 {m}: Segi→WHO2026 ≥20-place movers exceed release-to-release movers in {k}/14 strata; rho lower than release rho in {kr}/14")
# size of a 20-place move: relative ASR difference between ranks r and r+20 (all-cancer mortality, Segi–Doll 2024)
ids, v = get("2024", "1", "0", "39", sorted(c24), lambda d: asr(d, "segi_doll")); v = np.sort(np.array(v))[::-1]
gap = np.array([v[i] / v[i + 20] - 1 for i in range(len(v) - 20)])
say(f"A1 size: all-cancer mortality (Segi–Doll 2024), ASR of rank r vs r+20: median relative difference {100*np.median(gap):.1f}% "
    f"(IQR {100*np.percentile(gap,25):.1f}–{100*np.percentile(gap,75):.1f}%); ranks 41–146: median {100*np.median(gap[40:126]):.1f}%")

# ---------- A2 data quality ----------
VR = {"1", "2a", "2b"}
def tier(c): return "death records (methods 1, 2a, 2b)" if P24[c]["method_mortality"] in VR else "estimated from incidence (methods 3a–3c, 4)"
S9 = []
for site, sx in MAIN:
    for m in ("0", "1"):
        ids, X = get("2024", m, sx, site, sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026")]); X = np.array(X)
        rf = np.abs(rk(X[:, 0]) - rk(X[:, 1]))
        for t in sorted({tier(c) for c in ids}):
            sel = [i for i, c in enumerate(ids) if tier(c) == t]
            g = agree(X[sel, 0], X[sel, 1], [ids[i] for i in sel])
            lo, hi = boot_rho(X[sel, 0], X[sel, 1]) if site == "39" else ("", "")
            S9.append(dict(site=SITE[site], measure=MEAS[m], tier=t, n=g["n"], rho_within_tier=r6(g["rho"]),
                           rho_lo=r6(lo) if lo != "" else "", rho_hi=r6(hi) if hi != "" else "",
                           moved_ge10_within_tier=g["mv10"], moved_ge20_within_tier=g["mv20"],
                           moved_ge20_in_full_ranking=int((rf[sel] >= 20).sum()), share_moved_ge20_full=r6((rf[sel] >= 20).mean())))
wcsv("T_S9_veri_kalitesi.csv", S9)
for r in S9:
    if r["site"] == "All cancers": say(f"A2 {r['measure']} | {r['tier']}: n={r['n']} rho={r['rho_within_tier']:.3f} ({r['rho_lo']}–{r['rho_hi']}) ≥20 within tier={r['moved_ge20_within_tier']}; ≥20 in full ranking {r['moved_ge20_in_full_ranking']} ({100*r['share_moved_ge20_full']:.1f}%)")
ids, X = get("2024", "1", "0", "39", sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026")]); X = np.array(X)
rf = np.abs(rk(X[:, 0]) - rk(X[:, 1])); mv = [ids[i] for i in np.where(rf >= 20)[0]]
tab = [[sum(1 for c in ids if (c in mv) == a and tier(c).startswith("death") == b) for b in (True, False)] for a in (True, False)]
say(f"A2 all-cancer mortality: movers ≥20 by tier (death records / estimated): {tab[0]}; non-movers: {tab[1]}; Fisher p = {stats.fisher_exact(tab)[1]:.3g}")

# ---------- A3 standard-free and truncated ----------
S10 = []
for site, sx in MAIN:
    for m in ("0", "1"):
        ids, X = get("2024", m, sx, site, sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026"), cr74(d),
                                                                  asr(d, "segi_doll", 15), asr(d, "who2026", 15), asr(d, "segi_doll", 17), asr(d, "who2026", 17)])
        X = np.array(X)
        for lab, i, j in [("cumulative risk 0–74 vs Segi–Doll ASR", 2, 0), ("cumulative risk 0–74 vs WHO 2026 ASR", 2, 1),
                          ("truncated ASR 0–74: Segi–Doll vs WHO 2026", 3, 4), ("truncated ASR 0–84: Segi–Doll vs WHO 2026", 5, 6)]:
            g = agree(X[:, i], X[:, j], ids)
            S10.append(dict(site=SITE[site], measure=MEAS[m], comparison=lab, n=g["n"], rho=r6(g["rho"]), top10=g["top10"], moved_ge10=g["mv10"], moved_ge20=g["mv20"]))
wcsv("T_S10_standarttan_bagimsiz.csv", S10)
for r in S10:
    if r["site"] == "All cancers": say(f"A3 {r['measure']}: {r['comparison']}: rho={r['rho']:.3f} top10={r['top10']} ≥20={r['moved_ge20']}")
for m in ("incidence", "mortality"):
    k = sum(1 for site, sx in MAIN if [r for r in S10 if r["site"] == SITE[site] and r["measure"] == m and r["comparison"].endswith("Segi–Doll ASR")][0]["rho"] >
            [r for r in S10 if r["site"] == SITE[site] and r["measure"] == m and r["comparison"].endswith("WHO 2026 ASR")][0]["rho"])
    say(f"A3 {m}: cumulative risk 0–74 agrees better with Segi–Doll than with WHO 2026 ASR in {k}/14 strata")

# ---------- A4 index 8: male:female ratio ----------
NONSEX = ["15", "41", "7", "32", "11", "30", "34", "13", "6", "36"]
S11 = []
for site in NONSEX:
    for m in ("0", "1"):
        ch = []
        for c in sorted(c24):
            dm, df = CELL.get(("2024", m, "1", c, site)), CELL.get(("2024", m, "2", c, site))
            if dm is None or df is None or dm["c"].sum() == 0 or df["c"].sum() == 0: continue
            sd = asr(dm, "segi_doll") / asr(df, "segi_doll"); wd = asr(dm, "who2026") / asr(df, "who2026")
            ch.append(wd / sd)
        ch = np.array(ch)
        S11.append(dict(site=SITE[site], measure=MEAS[m], n=len(ch), median_change=r6(np.median(ch)), q1=r6(np.percentile(ch, 25)), q3=r6(np.percentile(ch, 75)),
                        min=r6(ch.min()), max=r6(ch.max()), share_change_gt5pct=r6((np.abs(ch - 1) > 0.05).mean())))
wcsv("T_S11_erkek_kadin_orani.csv", S11)
allch = [r["median_change"] for r in S11]
say(f"A4 index 8: median change in M:F ASR ratio across 10 non-sex-specific sites × 2 measures ranged {min(allch):.3f}–{max(allch):.3f}; "
    f"share of countries with >5% change: {min(r['share_change_gt5pct'] for r in S11)*100:.1f}–{max(r['share_change_gt5pct'] for r in S11)*100:.1f}%")

# ---------- A5 corrected ≥1 million sensitivity ----------
POP = {(k[0], k[3]): CELL[k]["p"].sum() for k in CELL if k[1] == "0" and k[2] == "0" and k[4] == "39"}
S6b = []
for yr in ("2024", "2022"):
    cs = sorted(c24) if yr == "2024" else COMMON
    for site, sx in MAIN:
        for m in ("0", "1"):
            ids, X = get(yr, m, sx, site, cs, lambda d: [asr(d, "segi_doll"), asr(d, "who2026")]); X = np.array(X)
            sel = [i for i, c in enumerate(ids) if POP[(yr, c)] >= 1_000_000]
            S6b.append(dict(year=yr, site=SITE[site], sex={"0": "both", "1": "male", "2": "female"}[sx], measure=MEAS[m], n=len(sel),
                            rho=r6(stats.spearmanr(X[sel, 0], X[sel, 1])[0])))
            if site == "39":  # also sex-stratified all cancers
                for s2 in ("1", "2"):
                    ids2, X2 = get(yr, m, s2, site, cs, lambda d: [asr(d, "segi_doll"), asr(d, "who2026")]); X2 = np.array(X2)
                    sel2 = [i for i, c in enumerate(ids2) if POP[(yr, c)] >= 1_000_000]
                    S6b.append(dict(year=yr, site=SITE[site], sex={"1": "male", "2": "female"}[s2], measure=MEAS[m], n=len(sel2),
                                    rho=r6(stats.spearmanr(X2[sel2, 0], X2[sel2, 1])[0])))
wcsv("T_S6b_1milyon_duzeltilmis.csv", S6b)
for r in S6b:
    if r["site"] == "All cancers" and r["year"] == "2024": say(f"A5 ≥1 million (both-sexes population): {r['sex']} {r['measure']} n={r['n']} rho={r['rho']:.3f}")

# ---------- H2 registered model (with interaction) from existing output ----------
for r in csv.DictReader(open("results/tables/T_H2_huber_hdi.csv")):
    if r["bagimli"] == "oran" and r["model"] == "etkilesimli":
        say(f"H2 registered model (share ≥60 × HDI group, Huber): {r['yil']} {r['olcut']}: slope (Very high HDI reference) {float(r['egim_60plus_refVH']):+.4f} "
            f"(95% CI {float(r['lo']):+.4f} to {float(r['hi']):+.4f}), bootstrap p = {r['p_boot']}, n = {r['n']}")
open("results/tables/ek_analiz_ozeti.txt", "w").write("\n".join(summ) + "\n")

# ---------- A6 registered exploratory (3): Scandinavian and European 2013 standards ----------
for r in csv.DictReader(open("data/weights/agirliklar_ham_yuzde.csv")):
    W.setdefault("scandinavian", []); W.setdefault("european2013", [])
    if isinstance(W["scandinavian"], list): W["scandinavian"].append(float(r["scandinavian"])); W["european2013"].append(float(r["european2013"]))
W["scandinavian"] = np.array(W["scandinavian"]); W["european2013"] = np.array(W["european2013"])
LAB.update(scandinavian="Scandinavian", european2013="European 2013")
say(f"A6 share ≥60: Scandinavian {100*W['scandinavian'][12:].sum()/W['scandinavian'].sum():.1f}%, European 2013 {100*W['european2013'][12:].sum()/W['european2013'].sum():.1f}%")
S12 = []
for site, sx in MAIN:
    for m in ("0", "1"):
        ids, X = get("2024", m, sx, site, sorted(c24), lambda d: [asr(d, s) for s in ("segi_doll", "scandinavian", "european2013", "who2026")]); X = np.array(X)
        for lab, i, j in [("Segi–Doll vs Scandinavian", 0, 1), ("Segi–Doll vs European 2013", 0, 2), ("European 2013 vs WHO 2026", 2, 3), ("Scandinavian vs WHO 2026", 1, 3)]:
            g = agree(X[:, i], X[:, j], ids)
            S12.append(dict(site=SITE[site], measure=MEAS[m], comparison=lab, n=g["n"], rho=r6(g["rho"]), top10=g["top10"], moved_ge10=g["mv10"], moved_ge20=g["mv20"]))
wcsv("T_S12_iskandinav_avrupa2013.csv", S12)
for r in S12:
    if r["site"] == "All cancers": say(f"A6 {r['measure']}: {r['comparison']}: rho={r['rho']:.3f} top10={r['top10']} ≥20={r['moved_ge20']}")

# ---------- A7 registered exploratory (5): by GLOBOCAN world region ----------
S13 = []
REG = {c: P24[c]["grouping"] for c in P24}
for m in ("0", "1"):
    ids, X = get("2024", m, "0", "39", sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026")]); X = np.array(X)
    for g_ in sorted(set(REG.values())):
        sel = [i for i, c in enumerate(ids) if REG.get(c) == g_]
        if len(sel) < 5: continue
        ra, rb = rk(X[sel, 0]), rk(X[sel, 1])
        S13.append(dict(region=g_, measure=MEAS[m], n=len(sel), rho_within_region=r6(stats.spearmanr(X[sel, 0], X[sel, 1])[0]),
                        max_rank_change_within_region=int(np.abs(ra - rb).max())))
wcsv("T_S13_bolge.csv", S13)
for r in S13: say(f"A7 {r['measure']} {r['region']}: n={r['n']} rho={r['rho_within_region']:.3f} max shift={r['max_rank_change_within_region']}")

# ---------- A8 age truncation curve (mechanism) ----------
S14 = []
for site, sx in MAIN:
    for m in ("0", "1"):
        for upto, lab in ((13, "0–64"), (15, "0–74"), (16, "0–79"), (17, "0–84"), (18, "all ages")):
            ids, X = get("2024", m, sx, site, sorted(c24), lambda d: [asr(d, "segi_doll", upto), asr(d, "who2026", upto)]); X = np.array(X)
            g = agree(X[:, 0], X[:, 1], ids)
            S14.append(dict(site=SITE[site], measure=MEAS[m], ages=lab, n=g["n"], rho=r6(g["rho"]), top10=g["top10"], moved_ge20=g["mv20"]))
wcsv("T_S14_yas_kesme.csv", S14)
for r in S14:
    if r["site"] == "All cancers": say(f"A8 {r['measure']} ages {r['ages']}: rho={r['rho']:.3f} top10={r['top10']} ≥20={r['moved_ge20']}")

# ---------- A9 registered exploratory (7): reporting recommendation by main site ----------
S15 = []
T2 = {(r["kanser"], r["olcut"]): r for r in csv.DictReader(open("results/tables/T2_sira_uyumu.csv")) if r["yil"] == "2024" and r["std_a"] == "segi_doll" and r["std_b"] == "who2026"}
for site, sx in MAIN:
    for m, mt in (("0", "insidans"), ("1", "mortalite")):
        t = T2[(SITE[site], mt)]; tr = [r for r in S14 if r["site"] == SITE[site] and r["measure"] == MEAS[m] and r["ages"] == "0–74"][0]
        rho = float(t["rho"]); mv = int(t["kayma20"])
        rt = float(tr["rho"])
        rec = ("rankings comparable across standards" if rho >= 0.95 and mv <= 15 else
               "state the standard; report rankings of truncated (0–74) rates alongside" if rt >= 0.98 else
               "state the standard; report rankings under both standards (truncation does not stabilise the ranking)")
        S15.append(dict(site=SITE[site], measure=MEAS[m], rho_full=round(rho, 3), moved_ge20=mv, rho_truncated_0_74=round(tr["rho"], 3), recommendation=rec))
wcsv("T_S15_raporlama_onerisi.csv", S15)
open("results/tables/ek_analiz_ozeti.txt", "w").write("\n".join(summ) + "\n")

# ---------- A10 registered H3 for the sex-specific analyses (men, women) ----------
H3S = []
for sx, lab in (("1", "men"), ("2", "women")):
    for site, s0 in MAIN:
        if site == "39": continue
        if (site in ("20", "23") and sx == "1") or (site == "27" and sx == "2"): continue
        if s0 != "0" and s0 != sx: continue
        i0, X0 = get("2024", "0", sx, site, sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026")])
        i1, X1 = get("2024", "1", sx, site, sorted(c24), lambda d: [asr(d, "segi_doll"), asr(d, "who2026")])
        cm = sorted(set(i0) & set(i1)); a0 = np.array([X0[i0.index(c)] for c in cm]); a1 = np.array([X1[i1.index(c)] for c in cm])
        r0 = stats.spearmanr(a0[:, 0], a0[:, 1])[0]; r1 = stats.spearmanr(a1[:, 0], a1[:, 1])[0]
        idx = RNG.integers(0, len(cm), size=(B, len(cm)))
        d = np.array([stats.spearmanr(a0[j, 0], a0[j, 1])[0] - stats.spearmanr(a1[j, 0], a1[j, 1])[0] for j in idx])
        lo, hi = np.percentile(d, [2.5, 97.5])
        H3S.append(dict(sex=lab, site=SITE[site], n=len(cm), rho_incidence=r6(r0), rho_mortality=r6(r1), difference=r6(r0 - r1), lo=r6(lo), hi=r6(hi)))
wcsv("T_S16_H3_cinsiyet.csv", H3S)
for lab in ("men", "women"):
    v = [r for r in H3S if r["sex"] == lab]; k = sum(r["difference"] > 0 for r in v); kc = sum(r["lo"] > 0 for r in v)
    say(f"A10 H3 {lab}: mortality ρ lower in {k}/{len(v)} sites (CI excludes 0 in {kc}); sign test p = {stats.binomtest(k, len(v), 0.5).pvalue:.4g}")
open("results/tables/ek_analiz_ozeti.txt", "w").write("\n".join(summ) + "\n")
