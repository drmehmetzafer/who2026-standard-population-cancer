"""11_sayisal_denetim.py — Makale v0.2, Tablo 1–2, Ek Tablo S1 ve kapak yazısındaki her sayının kaynağına karşı denetimi.
Nokta tahminleri tam hassasiyetli ASR'den (05_ciktilar/asr_dort_standart.csv.gz, 01 betiğinin tam hassasiyetli çıktısı)
bu betikte yeniden hesaplanır; bootstrap GA'lar ve p değerleri analiz çıktılarından (T2, T_H3, T_H4, T_H2, analiz_ozeti) okunur.
Yuvarlama kuralı: yarım yukarı (ROUND_HALF_UP), tam hassasiyetli değerden TEK adımda.
GA sınırları 02 betiğinin 6 ondalıklı çıktısından (T2_sira_uyumu.csv) okunur.
Çıktı: 05_ciktilar/T_denetim_sayilar.csv · 05_ciktilar/00_SAYISAL_DENETIM_RAPORU.md
"""
import csv, gzip, json
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
from scipy import stats

O = "05_ciktilar/"
def q(x, nd):
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
def amb(s):  # kaynak değer ≤4 ondalıklıysa ve son basamak 5 ise 3 ondalığa yuvarlama belirsizdir
    return s.endswith("5") and len(s.split(".")[-1]) == 4

meta = json.load(open("03_veri_ham/globocan_meta_2022_2024.json"))
CN = {str(p["country"]): p["label"] for p in meta["meta2024"]["p"]}
SITE = {str(c["cancer"]): c["label"] for c in meta["meta2024"]["c"]}
A = {}
for r in csv.DictReader(gzip.open(O + "asr_dort_standart.csv.gz", "rt")):
    c = "156" if r["ulke_kodu"] == "160" else r["ulke_kodu"]
    A.setdefault((r["yil"], r["olcut"], r["cinsiyet"], r["kanser_kodu"]), {})[c] = (
        {s: float(r["asr_" + s]) for s in ("segi_doll", "who2001", "gbd2021", "who2026")}, int(r["vaka_toplam"]), int(r["nufus_toplam"]))
common = {c for k, v in A.items() if k[0] == "2022" for c in v} & {c for k, v in A.items() if k[0] == "2024" for c in v}

def strat(y, m, sx, k, sa="segi_doll", sb="who2026", popmin=0):
    d = {c: v for c, v in A[(y, m, sx, k)].items() if v[1] > 0 and v[2] >= popmin and (y == "2024" or c in common)}
    ids = sorted(d); a = np.array([d[c][0][sa] for c in ids]); b = np.array([d[c][0][sb] for c in ids])
    ra, rb = stats.rankdata(-a), stats.rankdata(-b); dr = np.abs(ra - rb)
    top = len(set(np.argsort(-a, kind="stable")[:10]) & set(np.argsort(-b, kind="stable")[:10]))
    ratio = b / a
    return dict(n=len(ids), ids=ids, ra=ra, rb=rb, rho=stats.spearmanr(a, b)[0], tau=stats.kendalltau(a, b)[0], top=top,
                m10=int((dr >= 10).sum()), m20=int((dr >= 20).sum()), med=np.median(ratio), q1=np.percentile(ratio, 25), q3=np.percentile(ratio, 75))

T2 = {(r["yil"], r["olcut"], r["kanser"], r["std_a"], r["std_b"]): r for r in csv.DictReader(open(O + "T2_sira_uyumu.csv"))}
MAIN = [("39", "0", "All cancers"), ("15", "0", "Lung"), ("20", "2", "Breast (women)"), ("41", "0", "Colorectum"), ("27", "1", "Prostate (men)"),
        ("7", "0", "Stomach"), ("32", "0", "Thyroid"), ("11", "0", "Liver"), ("30", "0", "Bladder"), ("23", "2", "Cervix uteri (women)"),
        ("34", "0", "NHL"), ("13", "0", "Pancreas"), ("6", "0", "Oesophagus"), ("36", "0", "Leukaemia")]
M = {"0": "insidans", "1": "mortalite"}
S = {(y, m, k): strat(y, m, sx, k) for y in ("2024", "2022") for m in ("0", "1") for k, sx, _ in MAIN}

rows = []
def chk(yer, ifade, metin, kaynak_deger, dogru, kaynak, not_=""):
    durum = "UYUMLU" if str(metin) == str(dogru) else "HATA"
    if "belirsiz" in not_: durum = "BELİRSİZ"
    rows.append(dict(yer=yer, ifade=ifade, metindeki=metin, kaynak_tam=kaynak_deger, dogru_yazim=dogru, durum=durum, kaynak=kaynak, not_=not_))

# ---- ağırlıklar (yayımlanmış yüzdeler)
W = list(csv.DictReader(open("02_agirliklar/agirliklar_ham_yuzde.csv")))
o60 = {k: sum(Decimal(w[k]) for w in W[12:]) for k in ("segi_doll", "who2001", "gbd2021", "who2026")}
u30 = sum(Decimal(w["who2026"]) for w in W[:6])
for k, t in (("segi_doll", "11.0"), ("who2001", "12.0"), ("gbd2021", "12.6"), ("who2026", "20.1")):
    chk("Özet; Giriş; Yöntem 2.3; Ek S1", f"≥60 yaş payı {k}", t, str(o60[k]), q(o60[k], 1), "agirliklar_ham_yuzde.csv")
chk("Giriş", "WHO 2026 <30 yaş payı", "42.8", str(u30), q(u30, 1), "agirliklar_ham_yuzde.csv")
for k, t in (("who2026", "100.02"), ("who2001", "100.03")):
    chk("Yöntem 2.3", f"{k} tablo toplamı", t, str(sum(Decimal(w[k]) for w in W)), q(sum(Decimal(w[k]) for w in W), 2), "agirliklar_ham_yuzde.csv")

# ---- veri
raw_n = sum(1 for _ in gzip.open("03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz", "rt")) - 1
seen = set(); uniq = 0
for r in csv.DictReader(gzip.open("03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz", "rt")):
    k = tuple(r.values())
    if k not in seen: seen.add(k); uniq += 1
del seen
chk("Yöntem 2.2", "kayıt sayısı", "1,480,290", f"ham {raw_n}; tekil {uniq}", f"{uniq:,}", "globocan_yasaozgu_2022_2024.csv.gz",
    "Ham dosyada kanser 39 satırları iki kez çekilmiş (birebir kopya); metin tekil sayıyı vermeli")
ncell = sum(1 for _ in gzip.open(O + "asr_dort_standart.csv.gz", "rt")) - 1
chk("Yöntem 2.2; Bulgular 3.1", "hücre sayısı", "75,684", ncell, f"{ncell:,}", "asr_dort_standart.csv.gz")
n24 = len({c for k, v in A.items() if k[0] == "2024" for c in v}); n22 = len({c for k, v in A.items() if k[0] == "2022" for c in v})
chk("Yöntem 2.2", "ülke 2024", "186", n24, str(n24), "asr"); chk("Yöntem 2.2", "ülke 2022 / ortak", "185", f"{n22}/{len(common)}", str(len(common)), "asr")

# ---- H1
h1 = open(O + "analiz_ozeti.txt", encoding="utf-8").read().splitlines()[0]
chk("Özet; Bulgular 3.1", "H1 hücre oranı", "99.7", "63541/63748", q(63541 / 63748 * 100, 1), "analiz_ozeti.txt: " + h1[:60])

# ---- ASR oranı
for m, med, iqr in (("0", "1.61", "1.55–1.70"), ("1", "1.76", "1.63–1.98")):
    s = S[("2024", m, "39")]
    chk("Özet; Bulgular 3.1", f"ortanca ASR oranı {M[m]}", med, f"{s['med']:.6f}", q(s["med"], 2), "asr (tam)")
    chk("Bulgular 3.1", f"IQR {M[m]}", iqr, f"{s['q1']:.6f}–{s['q3']:.6f}", f"{q(s['q1'], 2)}–{q(s['q3'], 2)}", "asr (tam)")

# ---- Tablo 1 (ve metindeki karşılıkları)
TAB1 = {  # metindeki değerler (v0.2 Tablo 1)
 "All cancers": ("0.983 (0.974–0.988)", "9/10", "12", "0.901 (0.857–0.930)", "6/10", "79"),
 "Lung": ("0.993 (0.988–0.994)", "7/10", "1", "0.990 (0.985–0.992)", "9/10", "2"),
 "Breast (women)": ("0.987 (0.977–0.992)", "8/10", "8", "0.912 (0.872–0.937)", "7/10", "71"),
 "Colorectum": ("0.992 (0.986–0.995)", "9/10", "4", "0.981 (0.970–0.986)", "6/10", "17"),
 "Prostate (men)": ("0.978 (0.965–0.985)", "5/10", "16", "0.960 (0.938–0.974)", "9/10", "33"),
 "Stomach": ("0.991 (0.985–0.993)", "8/10", "2", "0.985 (0.975–0.989)", "9/10", "9"),
 "Thyroid": ("0.984 (0.971–0.991)", "7/10", "11", "0.909 (0.867–0.936)", "6/10", "53"),
 "Liver": ("0.977 (0.963–0.985)", "9/10", "13", "0.971 (0.954–0.979)", "9/10", "19"),
 "Bladder": ("0.989 (0.983–0.992)", "7/10", "3", "0.970 (0.958–0.977)", "7/10", "24"),
 "Cervix uteri (women)": ("0.992 (0.986–0.994)", "8/10", "1", "0.995 (0.992–0.996)", "9/10", "0"),
 "NHL": ("0.986 (0.975–0.991)", "8/10", "9", "0.920 (0.877–0.946)", "4/10", "52"),
 "Pancreas": ("0.991 (0.985–0.994)", "9/10", "4", "0.991 (0.985–0.993)", "8/10", "5"),
 "Oesophagus": ("0.984 (0.975–0.989)", "10/10", "7", "0.982 (0.971–0.987)", "9/10", "12"),
 "Leukaemia": ("0.965 (0.946–0.976)", "9/10", "29", "0.874 (0.827–0.910)", "5/10", "76"),
}
for k, sx, lab in MAIN:
    for j, m in enumerate(("0", "1")):
        s = S[("2024", m, k)]; t = T2[("2024", M[m], SITE[k], "segi_doll", "who2026")]
        assert s["n"] == int(t["n"]) and s["m20"] == int(t["kayma20"]) and s["top"] == round(float(t["top10"]) * 10) and abs(s["rho"] - float(t["rho"])) < 5e-5, (k, m)
        lo, hi = t["rho_lo"], t["rho_hi"]; note = "GA sınırı belirsiz (4. ondalık 5)" if amb(lo) or amb(hi) else ""
        dogru = f"{q(s['rho'], 3)} ({q(lo, 3)}–{q(hi, 3)})"
        txt = TAB1[lab][3 * j]
        chk("Tablo 1", f"{lab} {M[m]} ρ (GA)", txt, f"{s['rho']:.6f} ({lo}–{hi})", dogru, "asr (tam) + T2 GA", note)
        chk("Tablo 1", f"{lab} {M[m]} ilk-10", TAB1[lab][3 * j + 1], s["top"], f"{s['top']}/10", "asr (tam)")
        chk("Tablo 1", f"{lab} {M[m]} ≥20 sıra", TAB1[lab][3 * j + 2], s["m20"], str(s["m20"]), "asr (tam)")

# ---- metindeki sıralama bulguları
s = S[("2024", "1", "39")]; t = T2[("2024", "mortalite", "All cancers", "segi_doll", "who2026")]
chk("Özet; Bulgular 3.2; Giriş-kapak", "tüm kanser mortalite ρ", "0.902", f"{s['rho']:.6f}", q(s["rho"], 3), "asr (tam)")
chk("Bulgular 3.2", "tüm kanser mortalite GA", "0.857–0.930", f"{t['rho_lo']}–{t['rho_hi']}", f"{q(t['rho_lo'], 3)}–{q(t['rho_hi'], 3)}", "T2")
chk("Bulgular 3.2", "τb", "0.743", f"{s['tau']:.6f}", q(s["tau"], 3), "asr (tam)")
chk("Bulgular 3.2", "≥10 sıra", "115", s["m10"], str(s["m10"]), "asr (tam)")
chk("Bulgular 3.2", "dilim değişen %", "44.6", t["dilim_degisen"], q(float(t["dilim_degisen"]) * 100, 1), "T2")
si = S[("2024", "0", "39")]; ti = T2[("2024", "insidans", "All cancers", "segi_doll", "who2026")]
chk("Özet; Bulgular 3.2", "tüm kanser insidans ρ (GA)", "0.983 (0.974–0.988)", f"{si['rho']:.6f}", f"{q(si['rho'], 3)} ({q(ti['rho_lo'], 3)}–{q(ti['rho_hi'], 3)})", "asr + T2")
mn = min(S[("2024", "0", k)]["rho"] for k, _, _ in MAIN)
chk("Özet; Bulgular 3.2", "insidans en düşük ρ (≥0.965)", "≥0.965", f"{mn:.6f}", "≥0.965" if mn >= 0.965 else f"≥{q(mn, 3)}", "asr (tam)")
chk("Tartışma", "insidans hiçbir ana bölge <0.96 değil", "0.96", f"{mn:.6f}", "0.96" if mn >= 0.96 else "YANLIŞ", "asr (tam)")
r = dict(zip(s["ids"], zip(s["ra"], s["rb"])))
for nm, txt in (("Denmark", "41st→19th"), ("Barbados", "35th→20th"), ("Chad", "13th→55th"), ("Korea, Democratic People's Republic of", "14th→36th")):
    c = [k for k, v in CN.items() if v == nm][0]; a_, b_ = r[c]
    sfx = lambda n: f"{int(n)}{'th' if 10 <= int(n) % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(int(n) % 10, 'th')}"
    chk("Bulgular 3.2", f"{nm} sıra", txt, f"{a_}→{b_}", f"{sfx(a_)}→{sfx(b_)}", "asr (tam)")
for k, lab, txt in (("36", "lösemi", "0.874"), ("32", "tiroid", "0.909"), ("20", "meme", "0.912"), ("34", "NHL", "0.920")):
    chk("Bulgular 3.2; Tartışma", f"{lab} mortalite ρ", txt, f"{S[('2024', '1', k)]['rho']:.6f}", q(S[("2024", "1", k)]["rho"], 3), "asr (tam)")
mv = [S[("2024", "1", k)]["m20"] for k in ("36", "32", "20", "34")]
chk("Bulgular 3.2", "52–76 ülke ≥20 sıra", "52 to 76", mv, f"{min(mv)} to {max(mv)}", "asr (tam)")
hi_ = {k: S[("2024", "1", k)]["rho"] for k in ("15", "7", "13", "6", "23")}
chk("Bulgular 3.2", "akciğer, mide, pankreas, özofagus, serviks ρ≥0.98", "≥0.98", {SITE[k]: round(v, 4) for k, v in hi_.items()}, "≥0.98" if min(hi_.values()) >= 0.98 else "YANLIŞ", "asr (tam)")
for k, lab, txt in (("21", "vulva", "0.93"), ("22", "vagina", "0.92"), ("2", "tükürük bezi", "0.92"), ("25", "over", "0.93")):
    sx = "2" if k in ("21", "22", "25") else "0"
    v = strat("2024", "1", sx, k)["rho"]
    chk("Bulgular 3.2", f"{lab} mortalite ρ (0.92–0.93 aralığı)", txt, f"{v:.6f}", q(v, 2), "asr (tam)")
for (a_, b_), txt in ((("segi_doll", "who2001"), "0.989"), (("segi_doll", "gbd2021"), "0.964"), (("who2001", "gbd2021"), "0.992")):
    v = strat("2024", "1", "0", "39", a_, b_)["rho"]
    chk("Bulgular 3.2; Tartışma", f"{a_}↔{b_} tüm kanser mortalite ρ", txt, f"{v:.6f}", q(v, 3), "asr (tam)")

# ---- H3 / H4
h3 = sum(1 for k, _, _ in MAIN[1:] if S[("2024", "0", k)]["rho"] > S[("2024", "1", k)]["rho"])
h4 = sum(1 for r_ in csv.DictReader(open(O + "T_H4_yeni_vs_mevcut.csv")) if r_["yil"] == "2024" and float(r_["fark"]) < 0)
chk("Özet; Bulgular 3.2", "H3 12/13", "12", h3, str(h3), "asr (tam)")
chk("Özet; Bulgular 3.2", "H4 28/28", "28", h4, str(h4), "T_H4")
p3 = stats.binomtest(12, 13, 0.5).pvalue; p4 = stats.binomtest(28, 28, 0.5).pvalue
chk("Bulgular 3.2", "H3 p", "0.003", f"{p3:.6g}", q(p3, 3), "binom"); chk("Bulgular 3.2", "H3 Holm", "0.007", f"{2 * p3:.6g}", q(2 * p3, 3), "Holm (2. sıra ×2)")
chk("Bulgular 3.2", "H4 p", "7.5 × 10^−9", f"{p4:.6g}", f"{float(q(p4 * 1e9, 1))} × 10^−9".replace(".0 ", " "), "binom")
chk("Bulgular 3.2", "H4 Holm", "2.2 × 10^−8", f"{3 * p4:.6g}", f"{q(3 * p4 * 1e8, 1)} × 10^−8", "Holm (1. sıra ×3)")

# ---- H2
H2 = {(r_["yil"], r_["olcut"], r_["bagimli"], r_["model"]): r_ for r_ in csv.DictReader(open(O + "T_H2_huber_hdi.csv"))}
for m, txt_s, txt_p in (("insidans", "−0.0014", "0.35"), ("mortalite", "+0.0086", "0.007")):
    r_ = H2[("2024", m, "oran", "ana_etki")]; v = float(r_["egim_60plus_refVH"])
    chk("Bulgular 3.3", f"H2 eğim {m}", txt_s, r_["egim_60plus_refVH"], ("+" if v > 0 else "−") + q(abs(v), 4), "T_H2")
    chk("Bulgular 3.3", f"H2 p {m}", txt_p, r_["p_boot"], q(float(r_["p_boot"]), 2 if float(r_["p_boot"]) >= 0.1 else 3), "T_H2")
p2 = max(float(H2[("2024", m, "oran", "ana_etki")]["p_boot"]) for m in ("insidans", "mortalite"))
chk("Bulgular 3.3", "H2 Holm (2024)", "0.35", p2, q(max(p2, 3 * 0) if p2 >= 0.0068 else p2, 2), "Holm: H2 en büyük p (3. sıra ×1)")
for m in ("insidans", "mortalite"):
    chk("Bulgular 3.3", f"H2 2022 {m} p (destek yok)", "n.s.", H2[("2022", m, "oran", "ana_etki")]["p_boot"],
        "n.s." if float(H2[("2022", m, "oran", "ana_etki")]["p_boot"]) >= 0.05 else "ANLAMLI", "T_H2")
meta24 = meta["meta2024"]["p"]; ISO = {str(p["country"]): p.get("country_iso3") for p in meta24}
HDI = {r_["iso3"]: float(r_["hdi_value"]) for r_ in csv.DictReader(open("03_veri_ham/HDI_2023_E6_Makale1den.csv")) if r_["hdi_value"]}
raw = {}
for r_ in csv.DictReader(gzip.open("03_veri_ham/globocan_yasaozgu_2022_2024.csv.gz", "rt")):
    if r_["yil"] == "2024" and r_["kanser_kodu"] == "39" and r_["cinsiyet"] == "0" and r_["olcut"] == "0":
        raw.setdefault(r_["ulke_kodu"], {})[int(r_["age_code"])] = int(r_["nufus"])
P60 = {c: (v[12] + v[13] + v[14] + v[117] - v[14]) / v[99] for c, v in raw.items()}
for m, txt in (("0", "0.33"), ("1", "0.63")):
    d = A[("2024", m, "0", "39")]; ids = sorted(d)
    v = stats.spearmanr([d[c][0]["who2026"] / d[c][0]["segi_doll"] for c in ids], [P60[c] for c in ids])[0]
    chk("Bulgular 3.3", f"ρ(oran, 60+) {M[m]}", txt, f"{v:.6f}", q(v, 2), "asr + ham nüfus")
ok = [c for c in raw if ISO.get(c) in HDI]
v = stats.spearmanr([P60[c] for c in ok], [HDI[ISO[c]] for c in ok])[0]
chk("Bulgular 3.3", "ρ(60+ payı, HDI)", "0.82", f"{v:.6f} (n={len(ok)})", q(v, 2), "ham nüfus + HDI")
d = A[("2024", "1", "0", "39")]
v = stats.spearmanr([d[c][0]["who2026"] / d[c][0]["segi_doll"] for c in ok], [HDI[ISO[c]] for c in ok])[0]
chk("Bulgular 3.3", "ρ(mortalite oranı, HDI)", "0.70", f"{v:.6f} (n={len(ok)})", q(v, 2), "asr + HDI")

# ---- H5 / Tablo 2
T3 = {(r_["yil"], r_["olcut"], r_["cinsiyet"]): r_ for r_ in csv.DictReader(open(O + "T3_en_sik_kanser_ozet.csv"))}
T3b = {(r_["yil"], r_["olcut"], r_["surum"]): r_ for r_ in csv.DictReader(open(O + "T3b_en_sik_kanser_duzeltilmis_ozet.csv"))}
TAB2 = {("Registered", "her_iki"): ["50/186 (26.9%; 21.0–33.7)", "47/186 (25.3%; 19.6–32.0)", "48/185 (25.9%; 20.2–32.7)", "45/185 (24.3%; 18.7–31.0)"],
        ("Corrected", "her_iki_cinsiyete_ozgu_haric"): ["18/186 (9.7%; 6.2–14.8)", "14/186 (7.5%; 4.5–12.2)", "16/185 (8.6%; 5.4–13.6)", "18/185 (9.7%; 6.2–14.8)"],
        ("Men", "erkek"): ["17/186 (9.1%; 5.8–14.1)", "19/186 (10.2%; 6.6–15.4)", "9/185 (4.9%; 2.6–9.0)", "23/185 (12.4%; 8.4–18.0)"],
        ("Women", "kadin"): ["6/186 (3.2%; 1.5–6.9)", "18/186 (9.7%; 6.2–14.8)", "6/185 (3.2%; 1.5–6.9)", "17/185 (9.2%; 5.8–14.2)"]}
for (lab, key), vals in TAB2.items():
    for i, (y, m) in enumerate((("2024", "insidans"), ("2024", "mortalite"), ("2022", "insidans"), ("2022", "mortalite"))):
        r_ = T3[(y, m, key)] if lab == "Registered" else T3b[(y, m, key)]
        n, k_ = int(r_["n"]), int(r_["degisen"]); lo, hi = stats.binomtest(k_, n).proportion_ci(method="wilson")
        chk("Tablo 2; Bulgular 3.4", f"{lab} {y} {m}", vals[i], f"{k_}/{n}; {lo:.6f}–{hi:.6f}", f"{k_}/{n} ({q(k_ / n * 100, 1)}%; {q(lo * 100, 1)}–{q(hi * 100, 1)})", "T3/T3b + Wilson (tam)")

# ---- duyarlılık
for k, sx, pm, lab, txt in (("40", "0", 0, "C44 hariç", "0.901"), ("39", "0", 1_000_000, "≥1 milyon", "0.911"), ("39", "1", 0, "erkek", "0.949"), ("39", "2", 0, "kadın", "0.814")):
    v = strat("2024", "1", sx, k, popmin=pm)["rho"]
    chk("Bulgular 3.5; Özet (kadın)", f"mortalite ρ {lab}", txt, f"{v:.6f}", q(v, 3), "asr (tam)")
v = S[("2022", "1", "39")]["rho"]
chk("Bulgular 3.5", "2022 tüm kanser mortalite ρ", "0.928", f"{v:.6f}", q(v, 3), "asr (tam)")
h3_22 = sum(1 for k, _, _ in MAIN[1:] if S[("2022", "0", k)]["rho"] > S[("2022", "1", k)]["rho"])
chk("Bulgular 3.5", "2022 H3", "12", h3_22, str(h3_22), "asr (tam)")
chk("Özet", "kadınlarda en düşük (ρ = 0.81)", "0.81", f"{strat('2024', '1', '2', '39')['rho']:.6f}", q(strat("2024", "1", "2", "39")["rho"], 2), "asr (tam)")

# ---- Tartışma / Novelty / kapak
chk("Novelty; Tartışma", "≥20 sıra kayan ülke ≈ 'two in five'", "two in five", f"{79 / 186:.4f}", "two in five" if 0.35 <= 79 / 186 <= 0.45 else "?", "asr")
chk("Tartışma", "ASR artışı 'roughly 60–80%'", "60–80%", f"{S[('2024', '0', '39')]['med']:.3f}/{S[('2024', '1', '39')]['med']:.3f}", "60–80%", "asr")
chk("Novelty", "'almost twice' (20.1 / 11.0)", "almost twice", f"{float(o60['who2026'] / o60['segi_doll']):.3f}", "almost twice", "ağırlıklar")

with open(O + "T_denetim_sayilar.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
bad = [r_ for r_ in rows if r_["durum"] != "UYUMLU"]
print(f"Denetlenen ifade: {len(rows)} · UYUMLU: {sum(r_['durum'] == 'UYUMLU' for r_ in rows)} · HATA: {sum(r_['durum'] == 'HATA' for r_ in rows)} · BELİRSİZ: {sum(r_['durum'] == 'BELİRSİZ' for r_ in rows)}")
for r_ in bad: print(r_)
