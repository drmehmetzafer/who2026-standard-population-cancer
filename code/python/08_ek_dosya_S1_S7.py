"""08 — Supporting Information (Tables S1–S15, Figures S1–S2) as one .docx file (requires python-docx).
Run from the repository root: python3 code/python/08_ek_dosya_S1_S7.py
Comments in the code body are in Turkish."""
import csv, json, re
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor

R = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
O = "results/tables/"
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
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
doc.add_paragraph("Adopting the WHO 2026 world standard population reorders international cancer mortality, but not incidence, "
                  "rankings: a preregistered analysis of GLOBOCAN 2022 and 2024")
for line in [
    "Table S1. Age distribution of the four standard populations",
    "Table S2. Rank agreement between Segi–Doll and WHO 2026 for all 33 cancer sites, GLOBOCAN 2024",
    "Table S3. Countries whose highest-ASR cancer site differs between Segi–Doll and WHO 2026",
    "Table S4. Rank agreement for all six pairs of standards, and tests of H3 and H4, GLOBOCAN 2024",
    "Table S5. Determinants of the ASR ratio (H2): Huber robust regression adjusted for HDI group",
    "Table S6. Sensitivity analyses: exclusion of C44, exclusion of countries with <1 million inhabitants, and stratification by sex",
    "Table S7. Replication in GLOBOCAN 2022",
    "Table S8. Benchmarks: rank change between GLOBOCAN releases and between standards (post hoc)",
    "Table S9. Rank change by GLOBOCAN mortality data source (post hoc)",
    "Table S10. Cumulative risk 0–74 and age-truncated ASRs (post hoc)",
    "Table S11. Change in the male:female ASR ratio (registered index 8)",
    "Table S12. Scandinavian and European 2013 standards (registered exploratory analysis)",
    "Table S13. Rank agreement within GLOBOCAN world regions (registered exploratory analysis)",
    "Table S14. Rank agreement by upper age limit of standardisation (post hoc)",
    "Table S15. Reporting recommendation by main site (registered exploratory analysis)",
    "Table S16. H3 within sex: rank agreement for incidence versus mortality in men and in women (registered)",
    "Figure S1. ASR ratio WHO 2026 / Segi–Doll by country, all cancers, GLOBOCAN 2024",
    "Figure S2. ASR ratio WHO 2026 / Segi–Doll against the share of the population aged ≥60",
]:
    doc.add_paragraph(line, style="List Bullet")
note("General notes. ASR, age-standardised rate per 100,000; ρ, Spearman rank correlation; τb, Kendall tau-b; CI, confidence "
     "interval (percentile, 2,000 country bootstrap resamples, seed 20261010); RBO, rank-biased overlap (p = 0.9); Top-10, number of "
     "the ten highest-ranked countries shared by both standards. Countries are ranked from the highest ASR (rank 1). "
     "Correlation statistics are reported to four decimals exactly as produced by the analysis code, which is available in the "
     "public repository (see Data Availability Statement). Sex-specific sites are "
     "analysed in the relevant sex. Unless stated otherwise, the comparison is Segi–Doll versus WHO 2026.")

# ---------------- S1
doc.add_page_break(); heading("Table S1. Age distribution of the four standard populations")
from decimal import Decimal, ROUND_HALF_UP
W = R("data/weights/agirliklar_ham_yuzde.csv"); keys = ["segi_doll", "who2001", "gbd2021", "who2026"]
q = lambda d, n: str(Decimal(d).quantize(Decimal(n), rounding=ROUND_HALF_UP))
rows = [[w["age_group"]] + [q(w[k], "0.01") for k in keys] for w in W]
tot = [sum(Decimal(w[k]) for w in W) for k in keys]
u30 = [100 * sum(Decimal(w[k]) for w in W[:6]) / t for k, t in zip(keys, tot)]; o60 = [100 * sum(Decimal(w[k]) for w in W[12:]) / t for k, t in zip(keys, tot)]  # after rescaling
rows += [["Total"] + [q(v, "0.01") for v in tot], ["<30 years"] + [q(v, "0.1") for v in u30], ["≥60 years"] + [q(v, "0.1") for v in o60]]
table(["Age group (years)"] + [STD[k] for k in keys], rows, widths=[3.2, 3, 3, 3, 3], size=8)
note("Age-group values are the published percentages of each standard population (GBD 2021 aggregated from its 25 published groups); the <30 and ≥60 rows are shares after rescaling to 100,000. "
     "For all analyses each standard was rescaled to sum to 100,000; after rescaling, the share "
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
     "The 2022 values are in Table S7D.")

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
note("Country names as labelled by GLOBOCAN. "
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
note("ASR ratio (WHO 2026 / Segi–Doll) is given for the Segi–Doll vs WHO 2026 pair only.")
heading("S4B. H3 — rank agreement for incidence versus mortality (Segi–Doll vs WHO 2026)", 2)
H3 = R(O + "T_H3_ins_vs_mort.csv")
def h3_rows(yr):
    return [[site_lab(r["kanser"], r["cinsiyet"]), r["n"], f4(r["rho_ins"]), f4(r["rho_mort"]), ci(f4(r["fark"]), f4(r["fark_lo"]), f4(r["fark_hi"]))] for r in H3 if r["yil"] == yr]
table(["Site", "n", "ρ incidence", "ρ mortality", "Difference (95% CI)"], h3_rows("2024"), widths=[5, 1.5, 3, 3, 5], size=7)
note("Difference = ρ incidence − ρ mortality; paired country bootstrap. Sign test across the 13 sites (all cancers excluded): 12 of 13 "
     "positive, p = 0.003 (Holm-adjusted 0.007); the bootstrap CI excludes zero in 9 of 13 sites (lung, cervix uteri, pancreas and oesophagus do not). "
     "n, countries with both cases and deaths, so n can be smaller than in Table S2 (e.g., thyroid: 183 for incidence ranking, 170 here).")
heading("S4C. H4 — agreement Segi–Doll vs WHO 2026 compared with the lowest agreement among the three existing standards", 2)
H4 = R(O + "T_H4_yeni_vs_mevcut.csv")
def h4_rows(yr):
    return [[MEAS[r["olcut"]], SHORT_SITE.get(r["kanser"], r["kanser"]), f4(r["rho_segi_who26"]), f4(r["min_rho_mevcut"]), ci(f4(r["fark"]), f4(r["fark_lo"]), f4(r["fark_hi"]))] for r in H4 if r["yil"] == yr]
table(["Measure", "Site", "ρ Segi–Doll vs WHO 2026", "Lowest ρ among existing standards", "Difference (95% CI)"], h4_rows("2024"), widths=[2.5, 4, 4, 5, 5.5], size=7, first_left=2)
note("Existing standards: Segi–Doll, WHO 2000–2025 and GBD 2021 (three pairs). Difference = ρ(Segi–Doll, WHO 2026) − lowest ρ among the "
     "three existing pairs; country bootstrap. Sign test across the 28 strata: 28 of 28 negative, p = 7.5 × 10⁻⁹ (Holm-adjusted 3.0 × 10⁻⁸). "
     "H4 is close to guaranteed by construction because WHO 2026 is the most distant standard; it is reported as registered.")

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
     "HDI group. Countries without an HDI value were excluded (10 in 2024, 9 in 2022). The registered model is the interaction model on the ratio scale, and the registered "
     "confirmatory test is its slope for the share aged ≥60 (reference: Very high HDI): 2024 incidence p = 0.643, 2024 mortality p = 0.001; "
     "2022 p = 0.704 and 0.732. Main-effects and log-ratio models are shown for comparison.")

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
     "countries with at least one million inhabitants. The threshold is applied to the country's total (both-sexes) population, so the same countries are used in all "
     "sex strata. Analyses by sex were registered as secondary/exploratory.")

# ---------------- S7
landscape(True); heading("Table S7. Replication in GLOBOCAN 2022 (185 countries common to both releases)")
heading("S7A. Segi–Doll vs WHO 2026, 14 main strata", 2)
table(T2HDR, t2_rows("2022", {("segi_doll", "who2026")}), widths=T2W, size=6.5, first_left=3)
heading("S7B. H3 — incidence versus mortality", 2)
table(["Site", "n", "ρ incidence", "ρ mortality", "Difference (95% CI)"], h3_rows("2022"), widths=[5, 1.5, 3, 3, 5], size=7)
note("Sign test: 12 of 13 sites positive, p = 0.003 (Holm-adjusted 0.010); the bootstrap CI excludes zero in 8 of 13 sites.")
heading("S7C. H4 — Segi–Doll vs WHO 2026 compared with the lowest agreement among existing standards", 2)
table(["Measure", "Site", "ρ Segi–Doll vs WHO 2026", "Lowest ρ among existing standards", "Difference (95% CI)"], h4_rows("2022"), widths=[2.5, 4, 4, 5, 5.5], size=7, first_left=2)
note("Sign test: 28 of 28 strata negative, p = 7.5 × 10⁻⁹ (Holm-adjusted 3.0 × 10⁻⁸).")
heading("S7D. All 33 cancer sites", 2)
p = doc.add_paragraph(); p.add_run("Columns 2–7: incidence; columns 8–13: mortality.").font.size = Pt(7.5)
table(H2HDR, s2_rows("2022"), widths=[3.6] + [1.6] * 12, size=7)
note("Results for the six pairs of standards in 2022 are in the public repository; H2 in 2022 is in Table S5. "
     "China changed GLOBOCAN country code between releases (160 in 2022, 156 in 2024) and was matched manually.")


# ================= Additional tables (S8–S16) =================
def f3(x): return f"{float(x):.3f}"
MEN = {"incidence": "Incidence", "mortality": "Mortality"}
def sitel(x): return SHORT_SITE.get(x, x)
landscape(False); heading("Table S8. Benchmarks: rank change between GLOBOCAN releases and between standards (post hoc)")
S8 = R(O + "T_S8_benchmark.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["comparison"].replace("release: ", "Release update: "), r["n"],
         ci(f3(r["rho"]), f3(r["rho_lo"]), f3(r["rho_hi"])) if r["rho_lo"] else f3(r["rho"]), f"{r['top10']}/10", r["moved_ge10"], r["moved_ge20"]] for r in S8]
table(["Measure", "Site", "Comparison", "n", "ρ (95% CI)", "Top-10", "≥10 places", "≥20 places"], rows, widths=[1.8, 2.6, 5.2, 0.9, 3.0, 1.2, 1.3, 1.3], size=6.5, first_left=3)
note("Release update: Segi–Doll ASRs in GLOBOCAN 2022 versus GLOBOCAN 2024 for the 185 countries present in both releases with cases in both, "
     "i.e. the change in country ranks produced by a release update while the standard is held fixed. Standard comparisons: GLOBOCAN 2024. "
     "95% CIs (2,000 country bootstrap resamples) are shown for all cancers only. Not preregistered.")
heading("Table S9. Rank change by GLOBOCAN mortality data source, Segi–Doll vs WHO 2026, GLOBOCAN 2024 (post hoc)")
S9 = R(O + "T_S9_veri_kalitesi.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["tier"], r["n"], ci(f3(r["rho_within_tier"]), f3(r["rho_lo"]), f3(r["rho_hi"])) if r["rho_lo"] else f3(r["rho_within_tier"]),
         r["moved_ge20_within_tier"], f"{r['moved_ge20_in_full_ranking']} ({pct(r['share_moved_ge20_full'])}%)"] for r in S9]
table(["Measure", "Site", "GLOBOCAN mortality method", "n", "ρ within group (95% CI)", "≥20 places within group", "≥20 places in full ranking (%)"], rows,
      widths=[1.8, 2.6, 5.0, 0.9, 3.0, 1.9, 2.4], size=6.5, first_left=3)
note("Countries grouped by the GLOBOCAN 2024 mortality estimation method: methods 1, 2a and 2b use national or subnational death records; "
     "methods 3a–3c and 4 derive mortality from incidence with modelled incidence-to-mortality ratios or from neighbouring countries (GLOBOCAN "
     "sources and methods). For all-cancer mortality, the proportion of countries moving ≥20 places in the full ranking did not differ between the "
     "groups (41.6% vs 43.3%; Fisher exact p = 0.88). Not preregistered.")
heading("Table S10. Cumulative risk 0–74 and age-truncated ASRs, GLOBOCAN 2024 (post hoc)")
S10 = R(O + "T_S10_standarttan_bagimsiz.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["comparison"], r["n"], f3(r["rho"]), f"{r['top10']}/10", r["moved_ge20"]] for r in S10]
table(["Measure", "Site", "Comparison", "n", "ρ", "Top-10", "≥20 places"], rows, widths=[1.8, 2.6, 6.6, 0.9, 1.4, 1.3, 1.6], size=6.5, first_left=3)
note("Cumulative risk 0–74 (%) = 100 × [1 − exp(−5 Σ r_a / 100,000)] over the 15 age groups 0–4 to 70–74; it does not depend on a standard "
     "population. Truncated ASRs use the weights of the included age groups, rescaled to sum to 100,000. Not preregistered.")
heading("Table S11. Change in the male:female ASR ratio, WHO 2026 vs Segi–Doll, GLOBOCAN 2024 (registered index 8)")
S11 = R(O + "T_S11_erkek_kadin_orani.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["n"], f3(r["median_change"]), f"{f3(r['q1'])}–{f3(r['q3'])}", f"{f3(r['min'])}–{f3(r['max'])}", pct(r["share_change_gt5pct"])] for r in S11]
table(["Measure", "Site", "n", "Median change", "IQR", "Range", "Countries with >5% change (%)"], rows, widths=[1.8, 3.0, 0.9, 2.0, 2.6, 2.6, 2.6], size=6.5, first_left=2)
note("Change = (male:female ASR ratio under WHO 2026) / (male:female ASR ratio under Segi–Doll), per country, for non-sex-specific main sites; "
     "values above 1 mean that WHO 2026 widens the male excess. Countries with cases in both sexes.")
heading("Table S12. Scandinavian and European 2013 standards, GLOBOCAN 2024 (registered exploratory analysis)")
S12 = R(O + "T_S12_iskandinav_avrupa2013.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["comparison"], r["n"], f3(r["rho"]), f"{r['top10']}/10", r["moved_ge20"]] for r in S12]
table(["Measure", "Site", "Comparison", "n", "ρ", "Top-10", "≥20 places"], rows, widths=[1.8, 2.6, 5.0, 0.9, 1.4, 1.3, 1.6], size=6.5, first_left=3)
note("Weights from Table 1 of WHO Technical Paper WHO/HSA/DDA/GHE/2026.4, rescaled to 100,000. Share aged ≥60: Scandinavian 16.0%, "
     "European 2013 25.5%.")
heading("Table S13. Rank agreement within GLOBOCAN world regions, all cancers, both sexes, GLOBOCAN 2024 (registered exploratory analysis)")
S13 = R(O + "T_S13_bolge.csv")
rows = [[MEN[r["measure"]], r["region"], r["n"], f3(r["rho_within_region"]), r["max_rank_change_within_region"]] for r in S13]
table(["Measure", "Region", "n", "ρ within region", "Largest rank change within region"], rows, widths=[2.2, 5.5, 1.2, 2.5, 4.0], size=7, first_left=2)
note("Countries ranked within each GLOBOCAN grouping; Northern America (2 countries) not shown.")
heading("Table S14. Rank agreement, Segi–Doll vs WHO 2026, by upper age limit of standardisation, GLOBOCAN 2024 (post hoc)")
S14 = R(O + "T_S14_yas_kesme.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["ages"], r["n"], f3(r["rho"]), f"{r['top10']}/10", r["moved_ge20"]] for r in S14]
table(["Measure", "Site", "Ages included", "n", "ρ", "Top-10", "≥20 places"], rows, widths=[1.8, 2.8, 2.0, 0.9, 1.4, 1.3, 1.6], size=6.5, first_left=3)
note("Truncated ASRs use the weights of the included age groups, rescaled to sum to 100,000. Not preregistered.")
heading("Table S15. Reporting recommendation by main site, GLOBOCAN 2024 (registered exploratory analysis)")
S15 = R(O + "T_S15_raporlama_onerisi.csv")
rows = [[MEN[r["measure"]], sitel(r["site"]), r["rho_full"], r["moved_ge20"], r["rho_truncated_0_74"], r["recommendation"]] for r in S15]
table(["Measure", "Site", "ρ, all ages", "≥20 places", "ρ, ages 0–74", "Recommendation for country comparisons"], rows, widths=[1.8, 2.6, 1.5, 1.4, 1.6, 7.0], size=6.5, first_left=2)
note("Rules, defined after analysis and applied mechanically: ρ ≥ 0.95 and ≤15 countries moving ≥20 places, rankings comparable across standards; "
     "otherwise, if ρ for ASRs truncated at 74 years is ≥0.98, state the standard and report rankings of truncated rates alongside; otherwise, "
     "report rankings under both standards. Truncated rates exclude deaths at ages ≥75 and complement, rather than replace, all-age ASRs.")

heading("Table S16. H3 within sex: rank agreement for incidence versus mortality, Segi–Doll vs WHO 2026, GLOBOCAN 2024 (registered)")
S16 = R(O + "T_S16_H3_cinsiyet.csv")
rows = [[r["sex"].capitalize(), sitel(r["site"]), r["n"], f4(r["rho_incidence"]), f4(r["rho_mortality"]), ci(f4(r["difference"]), f4(r["lo"]), f4(r["hi"]))] for r in S16]
table(["Sex", "Site", "n", "ρ incidence", "ρ mortality", "Difference (95% CI)"], rows, widths=[1.6, 3.4, 1.0, 2.2, 2.2, 4.6], size=7, first_left=2)
note("Difference = ρ incidence − ρ mortality; paired country bootstrap (2,000 resamples). Sign test: men, 11 of 11 sites positive (p = 0.001; CI excludes "
     "zero in 9); women, 11 of 12 positive (p = 0.006; CI excludes zero in 8). Sex-specific sites in the relevant sex only.")
# ---------------- Figure S1
landscape(False); heading("Figure S1. ASR ratio WHO 2026 / Segi–Doll by country, all cancers, both sexes, GLOBOCAN 2024")
doc.add_picture("results/figures/EkSekil_S1_harita_ASR_orani.png", width=Cm(16.5))
note("(A) Incidence; (B) mortality. Classes are identical in both panels. Grey, no GLOBOCAN estimate. Equal Earth projection. Boundaries: "
     "Natural Earth 1:50m admin-0 countries (public domain); Somaliland is shown with Somalia and Northern Cyprus with Cyprus, consistent "
     "with the population coverage of the GLOBOCAN estimates; French Guiana, Guadeloupe, Martinique and La Réunion are shown separately "
     "from metropolitan France, as in GLOBOCAN. Boundaries do not imply any judgement on the legal status of any territory.")

heading("Figure S2. ASR ratio WHO 2026 / Segi–Doll against the share of the population aged ≥60, all cancers, both sexes, GLOBOCAN 2024")
doc.add_picture("results/figures/FigureS2_ratio_age60.png", width=Cm(16.5))
note("(A) Incidence; (B) mortality. Each point is one country (n = 186); circled and labelled: highest and lowest ratio and largest share aged ≥60. "
     "Spearman ρ 0.33 (95% CI 0.21–0.44) for incidence and 0.63 (0.55–0.70) for mortality. Regression models are given in Table S5.")
doc.core_properties.author = "Mehmet Zafer Sabuncuoğlu; İsmail Zihni"
doc.core_properties.title = "Supporting Information"
doc.save("results/submission/Supporting_Information.docx")
print("ok")
