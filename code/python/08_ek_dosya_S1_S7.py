"""08_ek_dosya_S1_S7.py — Supporting Information (Tables S1–S7, Figure S1) tek .docx dosyası.
Yalnız mevcut analiz çıktılarını biçimlendirir; hiçbir istatistik yeniden hesaplanmaz.
Değerler kaynak CSV'deki hassasiyetle (ρ, τb, RBO 4 basamak) aynen yazılır; çift yuvarlama yoktur.
Girdi : 02_agirliklar/agirliklar_100bin_ANALIZ.csv · 03_veri_ham/globocan_meta_2022_2024.json
        05_ciktilar/{T2_sira_uyumu, T_S2_tum_bolgeler, T3_en_sik_kanser_ulkeler, T3b_en_sik_kanser_duzeltilmis_ulkeler,
        T3_en_sik_kanser_ozet, T3b_en_sik_kanser_duzeltilmis_ozet, T_H2_huber_hdi, T_H3_ins_vs_mort, T_H4_yeni_vs_mevcut,
        T_S1_duyarlilik}.csv · 05_ciktilar/sekiller/EkSekil_S1_harita_ASR_orani.png (09 betiği)
Çıktı : 07_gonderim/Supporting_Information_S1-S7.docx
"""
import csv, json, re
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor

R = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
O = "05_ciktilar/"
meta = json.load(open("03_veri_ham/globocan_meta_2022_2024.json"))
CNAME = {}
for y in ("2022", "2024"):
    for p in meta["meta" + y]["p"]:
        CNAME.setdefault(str(p["country"]), p["label"])
CNAME["160"] = CNAME.get("156", CNAME.get("160"))
MEAS = {"insidans": "Incidence", "mortalite": "Mortality"}
SEX = {"her_iki": "Both", "erkek": "Men", "kadin": "Women"}
STD = {"segi_doll": "Segi–Doll", "who2001": "WHO 2000–2025", "gbd2021": "GBD 2021", "who2026": "WHO 2026"}
SHORT_SITE = {"Trachea, bronchus and lung": "Lung", "Liver and intrahepatic bile ducts": "Liver",
              "Non-Hodgkin lymphoma": "Non-Hodgkin lymphoma"}

def site_lab(name, sex):
    n = SHORT_SITE.get(name, name)
    return n + (" (women)" if sex == "kadin" else " (men)" if sex == "erkek" else "")

def f4(x): return f"{float(x):.4f}" if x not in ("", None) else "–"
def f5(x): return f"{float(x):.5f}"
def pct(x, d=1): return f"{100 * float(x):.{d}f}"
def ci(e, lo, hi):
    e, lo, hi = str(e), str(lo), str(hi)
    return f"{e} ({lo} to {hi})" if (lo.startswith("-") or hi.startswith("-")) else f"{e} ({lo}–{hi})"
def frac10(x): return f"{round(float(x) * 10)}/10"

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
for s in ("Heading 1", "Heading 2", "Title"):
    doc.styles[s].font.name = "Arial"; doc.styles[s].font.color.rgb = RGBColor(0, 0, 0)
doc.styles["Heading 1"].font.size = Pt(11); doc.styles["Heading 2"].font.size = Pt(9.5)
sec = doc.sections[0]
for s_ in (sec,):
    s_.left_margin = s_.right_margin = Cm(2); s_.top_margin = s_.bottom_margin = Cm(2)

def landscape(on):
    s = doc.add_section()
    w, h = s.page_width, s.page_height
    if (on and w < h) or (not on and w > h):
        s.orientation = WD_ORIENT.LANDSCAPE if on else WD_ORIENT.PORTRAIT
        s.page_width, s.page_height = h, w
    s.left_margin = s.right_margin = Cm(1.6 if on else 2)

def borders(cell, top=None, bottom=None):
    tcPr = cell._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
    for edge, val in (("top", top), ("bottom", bottom)):
        if val:
            e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(val)); e.set(qn("w:color"), "000000"); b.append(e)
    tcPr.append(b)

def table(header, rows, widths=None, size=7.5, first_left=1):
    t = doc.add_table(rows=1, cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if i < first_left else WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].paragraph_format.space_after = Pt(0)
        borders(c, top=8, bottom=6)
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; p = cells[i].paragraphs[0]; r = p.add_run(re.sub(r"(?<![0-9])-(?=[0-9])", "\u2212", str(v))); r.font.size = Pt(size)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i < first_left else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            if k == len(rows) - 1: borders(cells[i], bottom=8)
    if widths:
        t.autofit = False
        tblPr = t._tbl.tblPr; lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        for i, w in enumerate(widths): t.columns[i].width = Cm(w)
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    return t

def note(text, italic=False):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(7.5); r.italic = italic
    p.paragraph_format.space_before = Pt(3)

def heading(text, lvl=1): doc.add_heading(text, level=lvl)

# ---------------- Title page
doc.add_heading("Supporting Information", 0)
doc.add_paragraph("A new world standard, a new cancer map? Impact of the WHO 2026 standard population on age-standardised "
                  "cancer incidence, mortality and country rankings")
for line in [
    "Table S1. Age distribution of the four standard populations",
    "Table S2. Rank agreement between Segi–Doll and WHO 2026 for all 33 cancer sites, GLOBOCAN 2024",
    "Table S3. Countries whose highest-ASR cancer site differs between Segi–Doll and WHO 2026",
    "Table S4. Rank agreement for all six pairs of standards, and tests of H3 and H4, GLOBOCAN 2024",
    "Table S5. Determinants of the ASR ratio (H2): Huber robust regression adjusted for HDI group",
    "Table S6. Sensitivity analyses: exclusion of C44, exclusion of countries with <1 million inhabitants, and stratification by sex",
    "Table S7. Replication in GLOBOCAN 2022",
    "Figure S1. ASR ratio WHO 2026 / Segi–Doll by country, all cancers, GLOBOCAN 2024",
]:
    doc.add_paragraph(line, style="List Bullet")
note("General notes. ASR, age-standardised rate per 100,000; ρ, Spearman rank correlation; τb, Kendall tau-b; CI, confidence "
     "interval (percentile, 2,000 country bootstrap resamples, seed 20261010); RBO, rank-biased overlap (p = 0.9); Top-10, number of "
     "the ten highest-ranked countries shared by both standards. Countries are ranked from the highest ASR (rank 1). "
     "Correlation statistics are reported to four decimals exactly as produced by the analysis scripts (02_ana_analiz.py, "
     "03_duyarlilik.py, 05_h2_hdi.py, 06_ek_tablo_tum_bolgeler.py, 07_h5_cinsiyete_ozgu_duzeltme.py). Sex-specific sites are "
     "analysed in the relevant sex. Unless stated otherwise, the comparison is Segi–Doll versus WHO 2026.")

# ---------------- S1
doc.add_page_break(); heading("Table S1. Age distribution of the four standard populations")
from decimal import Decimal, ROUND_HALF_UP
W = R("02_agirliklar/agirliklar_ham_yuzde.csv"); keys = ["segi_doll", "who2001", "gbd2021", "who2026"]
q = lambda d, n: str(Decimal(d).quantize(Decimal(n), rounding=ROUND_HALF_UP))
rows = [[w["age_group"]] + [q(w[k], "0.01") for k in keys] for w in W]
u30 = [sum(Decimal(w[k]) for w in W[:6]) for k in keys]; o60 = [sum(Decimal(w[k]) for w in W[12:]) for k in keys]
tot = [sum(Decimal(w[k]) for w in W) for k in keys]
rows += [["Total"] + [q(v, "0.01") for v in tot], ["<30 years"] + [q(v, "0.1") for v in u30], ["≥60 years"] + [q(v, "0.1") for v in o60]]
table(["Age group (years)"] + [STD[k] for k in keys], rows, widths=[3.2, 3, 3, 3, 3], size=8)
note("Values are the published percentages of each standard population (GBD 2021 aggregated from its 25 published groups). "
     "For all analyses each standard was rescaled to sum to 100,000 (file agirliklar_100bin_ANALIZ.csv); after rescaling, the share "
     "aged ≥60 is 11.0%, 11.9%, 12.6% and 20.1%, respectively. Sources: Segi–Doll, WHO 2000–2025 and WHO 2026, Table 1 of WHO Technical Paper "
     "WHO/HSA/DDA/GHE/2026.4 ; Segi–Doll cross-checked against the SEER "
     "World (Segi 1960) standard million; GBD 2021, Appendix Table S14 of the GBD 2021 demographic analysis, aggregated from 25 to "
     "18 age groups.")

# ---------------- S2
landscape(True); heading("Table S2. Rank agreement between Segi–Doll and WHO 2026 for all 33 cancer sites, GLOBOCAN 2024")
S2 = [r for r in R(O + "T_S2_tum_bolgeler.csv")]
def s2_rows(yr):
    by = {}
    for r in S2:
        if r["yil"] == yr: by.setdefault((r["kanser"], r["cinsiyet"]), {})[r["olcut"]] = r
    out = []
    for (k, sx), d in by.items():
        row = [site_lab(k, sx)]
        for m in ("insidans", "mortalite"):
            r = d.get(m)
            row += [r["n"], f4(r["rho"]), f4(r["tau_b"]), frac10(r["top10"]), r["kayma20"], f"{float(r['oran_ortanca']):.3f}"] if r else ["–"] * 6
        out.append(row)
    return out
H2HDR = ["Site", "n", "ρ", "τb", "Top-10", "≥20 places", "Median ASR ratio", "n", "ρ", "τb", "Top-10", "≥20 places", "Median ASR ratio"]
p = doc.add_paragraph(); p.add_run("Columns 2–7: incidence; columns 8–13: mortality.").font.size = Pt(7.5)
table(H2HDR, s2_rows("2024"), widths=[3.6] + [1.6] * 12, size=7)
note("Sites in GLOBOCAN order. n, countries with at least one case or death of that site. ≥20 places, number of countries whose rank "
     "differs by 20 or more places. ASR ratio, WHO 2026 ASR divided by Segi–Doll ASR (median across countries). "
     "Source: 06_ek_tablo_tum_bolgeler.py (T_S2_tum_bolgeler.csv). The 2022 values are in Table S7D.")

# ---------------- S3
landscape(False); heading("Table S3. Countries whose highest-ASR cancer site differs between Segi–Doll and WHO 2026")
heading("S3A. Summary (n/N, %, Wilson 95% CI)", 2)
T3 = R(O + "T3_en_sik_kanser_ozet.csv"); T3b = R(O + "T3b_en_sik_kanser_duzeltilmis_ozet.csv")
def summ(rows_, key, val, yr, m):
    r = [x for x in rows_ if x["yil"] == yr and x["olcut"] == m and x[key] == val][0]
    return f"{r['degisen']}/{r['n']} ({pct(r['oran'])}%; {pct(r['lo'])}–{pct(r['hi'])})"
rows = []
for lab, src, key, val in (("Registered: both sexes, all 33 sites†", T3, "cinsiyet", "her_iki"),
                           ("Corrected: both sexes, sex-specific sites excluded", T3b, "surum", "her_iki_cinsiyete_ozgu_haric"),
                           ("Men", T3b, "surum", "erkek"), ("Women", T3b, "surum", "kadin")):
    rows.append([lab] + [summ(src, key, val, y, m) for y in ("2024", "2022") for m in ("insidans", "mortalite")])
table(["Analysis", "2024 incidence", "2024 mortality", "2022 incidence", "2022 mortality"], rows, widths=[4.6, 3.1, 3.1, 3.1, 3.1], size=7)
note("† In the GLOBOCAN interface, both-sexes rates for sex-specific sites (e.g., breast, cervix uteri, prostate) use the population of "
     "the relevant sex as denominator; the registered both-sexes comparison is therefore reported for transparency, and the corrected "
     "analyses are the measure of magnitude (Methods 2.6).")
heading("S3B. Countries with a change: site under Segi–Doll → site under WHO 2026", 2)
L3 = R(O + "T3_en_sik_kanser_ulkeler.csv"); L3b = R(O + "T3b_en_sik_kanser_duzeltilmis_ulkeler.csv")
rows = []
SV = {"her_iki_cinsiyete_ozgu_haric": "Both sexes, sex-specific sites excluded", "erkek": "Men", "kadin": "Women"}
for yr in ("2024", "2022"):
    for m in ("insidans", "mortalite"):
        for r in sorted([x for x in L3b if x["yil"] == yr and x["olcut"] == m], key=lambda x: (list(SV).index(x["surum"]), CNAME[x["ulke_kodu"]])):
            rows.append([yr, MEAS[m], SV[r["surum"]], CNAME[r["ulke_kodu"]], SHORT_SITE.get(r["segi"], r["segi"]), SHORT_SITE.get(r["who2026"], r["who2026"])])
        for r in sorted([x for x in L3 if x["yil"] == yr and x["olcut"] == m and x["cinsiyet"] == "her_iki"], key=lambda x: x["ulke"]):
            rows.append([yr, MEAS[m], "Registered: both sexes, all sites†", r["ulke"], SHORT_SITE.get(r["segi"], r["segi"]), SHORT_SITE.get(r["who2026"], r["who2026"])])
table(["Release", "Measure", "Analysis", "Country", "Segi–Doll", "WHO 2026"], rows, widths=[1.5, 1.7, 5.1, 4.1, 2.6, 2.6], size=7, first_left=6)
note("Country names as labelled by GLOBOCAN. Sources: 02_ana_analiz.py (T3_en_sik_kanser_*.csv) and 07_h5_cinsiyete_ozgu_duzeltme.py (T3b_*.csv). "
     "Men and women rows are identical in both sources.")

# ---------------- S4
landscape(True); heading("Table S4. Rank agreement for all six pairs of standards, and tests of H3 and H4, GLOBOCAN 2024")
heading("S4A. Agreement between each pair of standards, 14 main strata", 2)
T2 = R(O + "T2_sira_uyumu.csv")
def t2_rows(yr, pairs=None):
    out = []
    for r in sorted(T2, key=lambda r: r["olcut"] == "mortalite"):
        if r["yil"] != yr or (pairs and (r["std_a"], r["std_b"]) not in pairs): continue
        ratio = ci(f"{float(r['oran_ortanca']):.3f}", f"{float(r['oran_q1']):.3f}", f"{float(r['oran_q3']):.3f}").replace(" to ", "–") if r["oran_ortanca"] else "–"
        out.append([MEAS[r["olcut"]], site_lab(r["kanser"], r["cinsiyet"]), f"{STD[r['std_a']]} vs {STD[r['std_b']]}", r["n"],
                    ci(f4(r["rho"]), f4(r["rho_lo"]), f4(r["rho_hi"])), ci(f4(r["tau_b"]), f4(r["tau_lo"]), f4(r["tau_hi"])), frac10(r["top10"]), f4(r["rbo"]),
                    r["kayma10"], r["kayma20"], pct(r["dilim_degisen"]), ratio])
    return out
T2W = [1.6, 2.6, 4.0, 0.9, 3.3, 3.3, 1.2, 1.3, 1.3, 1.3, 1.6, 3.0]
T2HDR = ["Measure", "Site", "Standards compared", "n", "ρ (95% CI)", "τb (95% CI)", "Top-10", "RBO", "≥10 places", "≥20 places",
         "Quintile changed (%)", "ASR ratio, median (IQR)"]
table(T2HDR, t2_rows("2024"), widths=T2W, size=6.5, first_left=3)
note("Source: 02_ana_analiz.py (T2_sira_uyumu.csv). ASR ratio (WHO 2026 / Segi–Doll) is given for the Segi–Doll vs WHO 2026 pair only.")
heading("S4B. H3 — rank agreement for incidence versus mortality (Segi–Doll vs WHO 2026)", 2)
H3 = R(O + "T_H3_ins_vs_mort.csv")
def h3_rows(yr):
    return [[site_lab(r["kanser"], r["cinsiyet"]), r["n"], f4(r["rho_ins"]), f4(r["rho_mort"]), ci(f4(r["fark"]), f4(r["fark_lo"]), f4(r["fark_hi"]))] for r in H3 if r["yil"] == yr]
table(["Site", "n", "ρ incidence", "ρ mortality", "Difference (95% CI)"], h3_rows("2024"), widths=[5, 1.5, 3, 3, 5], size=7)
note("Difference = ρ incidence − ρ mortality; paired country bootstrap. Sign test across the 13 sites (all cancers excluded): 12 of 13 "
     "positive, p = 0.003 (Holm-adjusted 0.007). n, countries with cases and deaths. Source: T_H3_ins_vs_mort.csv; analiz_ozeti.txt.")
heading("S4C. H4 — agreement Segi–Doll vs WHO 2026 compared with the lowest agreement among the three existing standards", 2)
H4 = R(O + "T_H4_yeni_vs_mevcut.csv")
def h4_rows(yr):
    return [[MEAS[r["olcut"]], SHORT_SITE.get(r["kanser"], r["kanser"]), f4(r["rho_segi_who26"]), f4(r["min_rho_mevcut"]), ci(f4(r["fark"]), f4(r["fark_lo"]), f4(r["fark_hi"]))] for r in H4 if r["yil"] == yr]
table(["Measure", "Site", "ρ Segi–Doll vs WHO 2026", "Lowest ρ among existing standards", "Difference (95% CI)"], h4_rows("2024"), widths=[2.5, 4, 4, 5, 5.5], size=7, first_left=2)
note("Existing standards: Segi–Doll, WHO 2000–2025 and GBD 2021 (three pairs). Difference = ρ(Segi–Doll, WHO 2026) − lowest ρ among the "
     "three existing pairs; country bootstrap. Sign test across the 28 strata: 28 of 28 negative, p = 7.5 × 10⁻⁹ (Holm-adjusted 2.2 × 10⁻⁸). "
     "Source: T_H4_yeni_vs_mevcut.csv; analiz_ozeti.txt.")

# ---------------- S5
landscape(False); heading("Table S5. Determinants of the ASR ratio (H2): Huber robust regression adjusted for HDI group")
H2 = R(O + "T_H2_huber_hdi.csv")
rows = []
for r in H2:
    rows.append([r["yil"], MEAS[r["olcut"]], "Ratio" if r["bagimli"] == "oran" else "log(ratio)", "Main effects" if r["model"] == "ana_etki" else "With interaction",
                 r["n"], ci(f5(r["egim_60plus_refVH"]), f5(r["lo"]), f5(r["hi"])), f"{float(r['p_boot']):.3f}", r["dusuk_agirlikli_ulke"]])
table(["Release", "Measure", "Outcome", "Model", "n", "Slope per percentage point aged ≥60 (95% CI)", "Bootstrap p", "Down-weighted countries"],
      rows, widths=[1.4, 1.8, 1.8, 2.4, 1, 4.4, 1.6, 2], size=7, first_left=4)
heading("Slopes within HDI groups (interaction models)", 2)
rows = [[r["yil"], MEAS[r["olcut"]], "Ratio" if r["bagimli"] == "oran" else "log(ratio)", ci(f5(r["egim_60plus_refVH"]), f5(r["lo"]), f5(r["hi"])),
         r["egim_High"], r["egim_Medium"], r["egim_Low"]] for r in H2 if r["model"] == "etkilesimli"]
table(["Release", "Measure", "Outcome", "Very high HDI", "High HDI", "Medium HDI", "Low HDI"], rows, widths=[1.3, 1.7, 1.7, 3.1, 3.1, 3.1, 3.1], size=6.5, first_left=3)
note("Outcome: country ASR ratio WHO 2026 / Segi–Doll, all cancers, both sexes. Exposure: national share of population aged ≥60 (percentage "
     "points, centred on the median). Adjustment: HDI 2023 group (reference Very high; UNDP Human Development Report 2025). Huber "
     "M-estimator (k = 1.345, MAD scale, IRLS); 95% CI and two-sided p from 2,000 country bootstrap resamples. Main-effects models give "
     "the common slope; interaction models give the slope in the Very high group (column 'Slope' above) and, in the lower panel, in each "
     "HDI group. Countries without an HDI value were excluded (10 in 2024, 9 in 2022). The registered test of H2 is the main-effects "
     "model on the ratio scale; Holm-adjusted p for H2 (larger of the incidence and mortality p values): 0.35 (2024) and 0.81 (2022). "
     "Source: 05_h2_hdi.py (T_H2_huber_hdi.csv).")

# ---------------- S6
heading("Table S6. Sensitivity analyses (Segi–Doll vs WHO 2026, Spearman ρ)")
S6 = R(O + "T_S1_duyarlilik.csv")
idx = {}
for r in S6: idx[(r["yil"], r["olcut"], r["kanser"], r["cinsiyet"])] = r
order = []
for r in S6:
    k = (r["kanser"], r["cinsiyet"])
    if k not in order: order.append(k)
for m in ("insidans", "mortalite"):
    heading(f"S6{'A' if m == 'insidans' else 'B'}. {MEAS[m]}", 2)
    rows = []
    for k, sx in order:
        row = [k, SEX[sx]]
        for yr in ("2024", "2022"):
            r = idx.get((yr, m, k, sx))
            row += [r["n"], f4(r["rho"]), r["n_1milyon_ustu"], f4(r["rho_1milyon_ustu"])] if r else ["–"] * 4
        rows.append(row)
    table(["Site", "Sex", "n", "ρ, all countries", "n", "ρ, ≥1 million", "n", "ρ, all countries", "n", "ρ, ≥1 million"], rows, widths=[2.6, 1.3, 1.1, 1.8, 1.1, 1.8, 1.1, 1.8, 1.1, 1.8], size=6.5, first_left=2)
    note("Columns 3–6: GLOBOCAN 2024; columns 7–10: GLOBOCAN 2022.", italic=True)
note("All cancers excl. C44 = GLOBOCAN code 40 (all cancers excluding non-melanoma skin cancer); 'All cancers' = code 39 (default). ≥1 million, "
     "countries with at least one million inhabitants. Analyses by sex were registered as secondary/exploratory. Source: 03_duyarlilik.py "
     "(T_S1_duyarlilik.csv).")

# ---------------- S7
landscape(True); heading("Table S7. Replication in GLOBOCAN 2022 (185 countries common to both releases)")
heading("S7A. Segi–Doll vs WHO 2026, 14 main strata", 2)
table(T2HDR, t2_rows("2022", {("segi_doll", "who2026")}), widths=T2W, size=6.5, first_left=3)
heading("S7B. H3 — incidence versus mortality", 2)
table(["Site", "n", "ρ incidence", "ρ mortality", "Difference (95% CI)"], h3_rows("2022"), widths=[5, 1.5, 3, 3, 5], size=7)
note("Sign test: 12 of 13 sites positive, p = 0.003 (Holm-adjusted 0.007).")
heading("S7C. H4 — Segi–Doll vs WHO 2026 compared with the lowest agreement among existing standards", 2)
table(["Measure", "Site", "ρ Segi–Doll vs WHO 2026", "Lowest ρ among existing standards", "Difference (95% CI)"], h4_rows("2022"), widths=[2.5, 4, 4, 5, 5.5], size=7, first_left=2)
note("Sign test: 28 of 28 strata negative, p = 7.5 × 10⁻⁹ (Holm-adjusted 2.2 × 10⁻⁸).")
heading("S7D. All 33 cancer sites", 2)
p = doc.add_paragraph(); p.add_run("Columns 2–7: incidence; columns 8–13: mortality.").font.size = Pt(7.5)
table(H2HDR, s2_rows("2022"), widths=[3.6] + [1.6] * 12, size=7)
note("Results for the six pairs of standards in 2022 and for H2 in 2022 are given in the source file T2_sira_uyumu.csv and in Table S5. "
     "China changed GLOBOCAN country code between releases (160 in 2022, 156 in 2024) and was matched manually.")

# ---------------- Figure S1
landscape(False); heading("Figure S1. ASR ratio WHO 2026 / Segi–Doll by country, all cancers, both sexes, GLOBOCAN 2024")
doc.add_picture("05_ciktilar/sekiller/EkSekil_S1_harita_ASR_orani.png", width=Cm(16.5))
note("(A) Incidence; (B) mortality. Classes are identical in both panels. Grey, no GLOBOCAN estimate. Equal Earth projection. Boundaries: "
     "Natural Earth 1:50m admin-0 countries (public domain); Somaliland is shown with Somalia and Northern Cyprus with Cyprus, consistent "
     "with the population coverage of the GLOBOCAN estimates; French Guiana, Guadeloupe, Martinique and La Réunion are shown separately "
     "from metropolitan France, as in GLOBOCAN. Boundaries do not imply any judgement on the legal status of any territory. "
     "Source: 09_harita_ek_sekil_S1.py.")

doc.save("07_gonderim/Supporting_Information_S1-S7.docx")
print("ok")
