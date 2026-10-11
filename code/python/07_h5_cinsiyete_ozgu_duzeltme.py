"""07 — Within-country top site corrected for the sex-specific denominator of GLOBOCAN both-sexes rates:
(a) both sexes excluding sex-specific sites; (b) within sex. Writes results/tables/T3b_*.csv.
Run from the repository root: python3 code/python/07_h5_cinsiyete_ozgu_duzeltme.py
Comments in the code body are in Turkish."""
import csv, gzip, json
from collections import defaultdict
from scipy import stats
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
S = {str(x["cancer"]): x["label"] for x in meta["meta2024"]["c"]}
SEXSPEC = {"20", "21", "22", "23", "24", "25", "26", "27", "28"}
EXCL = {"37", "38", "39", "40"}
A = defaultdict(dict)
for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt")):
    if r["kanser_kodu"] in EXCL or int(r["vaka_toplam"]) == 0: continue
    A[(r["yil"], r["olcut"], r["cinsiyet"], r["ulke_kodu"])][r["kanser_kodu"]] = (float(r["asr_segi_doll"]), float(r["asr_who2026"]))
out = []; lst = []
for (yr, m, sx, c), d in sorted(A.items()):
    pass
for yr in ("2024", "2022"):
    for m, mn in (("0", "insidans"), ("1", "mortalite")):
        for sx, variant in (("0", "her_iki_cinsiyete_ozgu_haric"), ("1", "erkek"), ("2", "kadin")):
            ch = n = 0
            for (y, mm, s, c), d in A.items():
                if (y, mm, s) != (yr, m, sx): continue
                dd = {k: v for k, v in d.items() if not (sx == "0" and k in SEXSPEC)}
                if not dd: continue
                a = max(dd, key=lambda k: dd[k][0]); b = max(dd, key=lambda k: dd[k][1]); n += 1
                if a != b:
                    ch += 1; lst.append(dict(yil=yr, olcut=mn, surum=variant, ulke_kodu=c, segi=S[a], who2026=S[b]))
            lo, hi = stats.binomtest(ch, n).proportion_ci(method="wilson")
            out.append(dict(yil=yr, olcut=mn, surum=variant, n=n, degisen=ch, oran=round(ch / n, 6), lo=round(lo, 6), hi=round(hi, 6)))
for f, rows in (("T3b_en_sik_kanser_duzeltilmis_ozet.csv", out), ("T3b_en_sik_kanser_duzeltilmis_ulkeler.csv", lst)):
    with open("results/tables/" + f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in out: print(r)
from collections import Counter
print(Counter((r["segi"], r["who2026"]) for r in lst if r["yil"] == "2024" and r["surum"].startswith("her")).most_common(6))
