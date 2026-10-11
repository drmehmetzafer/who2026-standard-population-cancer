"""09_harita_ek_sekil_S1.py — Supplementary Figure S1: world map of the ASR ratio WHO 2026 / Segi–Doll
(all cancers, both sexes, GLOBOCAN 2024), incidence and mortality. Proje kökünden çalıştırın.
Girdi : 05_ciktilar/asr_dort_standart.csv.gz (01 betiğinin çıktısı), 03_veri_ham/globocan_meta_2022_2024.json,
        01_kaynak_belgeler/harita/ne_50m_admin_0_countries.geojson (Natural Earth 1:50m, kamu malı;
        SHA-256 3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb)
Çıktı : 05_ciktilar/sekiller/EkSekil_S1_harita_ASR_orani.{pdf,png}, 05_ciktilar/EkSekil_S1_eslesme_raporu.txt
Projeksiyon: Equal Earth (Šavrič, Patterson & Jenny 2018), kendi uygulaması (ek coğrafi paket gerekmez).
Ülke eşleme: GLOBOCAN ISO3 ↔ Natural Earth ADM0_A3. Natural Earth'te farklı kodlu birimler:
  SDS→SSD (Güney Sudan), PSX→PSE (Filistin), SOL→SOM (Somaliland; GLOBOCAN Somali nüfusu tüm ülkeyi kapsar),
  CYN→CYP (Kuzey Kıbrıs; GLOBOCAN Kıbrıs nüfusu adanın tamamıdır, BM WPP tanımı).
  Fransa (FRA) çoklu poligonu konuma göre ayrılır: Fransız Guyanası (GUF), Réunion (REU), Martinik (MTQ),
  Guadeloupe (GLP) GLOBOCAN'da ayrı ülkedir. Kosova, Batı Sahra, Tayvan, Hong Kong, Makao, Grönland vb. tahmin yoktur → gri.
"""
import csv, gzip, json, os
import numpy as np
import logging, matplotlib; matplotlib.use("Agg"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch

os.makedirs("05_ciktilar/sekiller", exist_ok=True)
INK, INK2, NODATA, EDGE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
# sıralı tek renk (mavi) rampası; 7 sınıf, iki panelde ortak
EDGES = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
COLS = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
LABS = ["<1.5", "1.5–1.6", "1.6–1.7", "1.7–1.8", "1.8–1.9", "1.9–2.0", "≥2.0"]
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "font.size": 8})

# ---- veri
meta = json.load(open("03_veri_ham/globocan_meta_2022_2024.json"))["meta2024"]["p"]
ISO = {str(p["country"]): p["country_iso3"] for p in meta if "country_iso3" in p}
ratio = {"0": {}, "1": {}}
for r in csv.DictReader(gzip.open("05_ciktilar/asr_dort_standart.csv.gz", "rt")):
    if r["yil"] == "2024" and r["kanser_kodu"] == "39" and r["cinsiyet"] == "0":
        ratio[r["olcut"]][ISO[r["ulke_kodu"]]] = float(r["asr_who2026"]) / float(r["asr_segi_doll"])
assert len(ratio["0"]) == len(ratio["1"]) == 186

# ---- Equal Earth
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = np.sqrt(3) / 2
def ee(lon, lat):
    lon, lat = np.radians(lon), np.radians(lat)
    th = np.arcsin(M * np.sin(lat)); t2 = th * th; t6 = t2 ** 3
    x = lon * np.cos(th) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y

RECODE = {"SDS": "SSD", "PSX": "PSE", "SOL": "SOM", "CYN": "CYP"}
def fr_part(ring):
    lon, lat = np.mean([p[0] for p in ring]), np.mean([p[1] for p in ring])
    if -55 < lon < -51 and 1 < lat < 7: return "GUF"
    if 55 < lon < 56.5 and -22 < lat < -20.5: return "REU"
    if -61.3 < lon < -60.7 and 14.3 < lat < 15: return "MTQ"
    if -62 < lon < -60.9 and 15.8 < lat < 16.6: return "GLP"
    if -6 < lon < 10 and 41 < lat < 52: return "FRA"
    return None  # Mayotte vb. — GLOBOCAN'da ayrı tahmin yok

geo = json.load(open("01_kaynak_belgeler/harita/ne_50m_admin_0_countries.geojson"))["features"]
polys = []  # (iso3 or None, ring xy)
for f in geo:
    code = f["properties"]["ADM0_A3"]
    if code == "ATA": continue
    g = f["geometry"]
    parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for part in parts:
        outer = part[0]
        c = fr_part(outer) if code == "FRA" else RECODE.get(code, code)
        x, y = ee(np.array([p[0] for p in outer]), np.array([p[1] for p in outer]))
        polys.append((c, np.column_stack([x, y])))

matched = {c for c, _ in polys}
miss = sorted(set(ratio["0"]) - matched)
rep = [f"GLOBOCAN ülkeleri: {len(ratio['0'])}", f"Haritada eşleşmeyen GLOBOCAN ülkesi: {len(miss)} {miss}"]

def klass(v): return int(np.searchsorted(EDGES, v, side="right"))

# küre sınırı (yalnız x ekseni sınırları için)
lat = np.linspace(-90, 90, 181)
bx1, by1 = ee(np.full_like(lat, -180), lat); bx2, by2 = ee(np.full_like(lat, 180), lat[::-1])
border = np.column_stack([np.r_[bx1, bx2], np.r_[by1, by2]])

fig, axes = plt.subplots(2, 1, figsize=(7.2, 7.6))
for ax, m, ttl in zip(axes, ("0", "1"), ("A  Incidence", "B  Mortality")):
    verts, fc = [], []
    for c, xy in polys:
        verts.append(xy); v = ratio[m].get(c)
        fc.append(COLS[klass(v)] if v is not None else NODATA)
    ax.add_collection(PolyCollection(verts, facecolors=fc, edgecolors=EDGE, linewidths=0.15, zorder=1))
    ax.set_xlim(border[:, 0].min() * 1.01, border[:, 0].max() * 1.01); ax.set_ylim(ee(0, -57)[1], ee(0, 84)[1])
    ax.set_aspect("equal"); ax.axis("off")
    vals = np.array(list(ratio[m].values()))
    ax.set_title(ttl, loc="left", fontsize=10, color=INK, fontweight="bold", pad=14)
    ax.text(0.0, 1.0, f"Median {np.median(vals):.2f} (IQR {np.percentile(vals,25):.2f}–{np.percentile(vals,75):.2f}); "
            f"range {vals.min():.2f}–{vals.max():.2f}; 186 countries", transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
    counts = np.bincount([klass(v) for v in vals], minlength=7)
    rep.append(f"{ttl}: sınıf sayıları {dict(zip(LABS, counts.tolist()))}; ortanca {np.median(vals):.4f}")
handles = [Patch(fc=c, ec="none", label=l) for c, l in zip(COLS, LABS)] + [Patch(fc=NODATA, ec="none", label="No estimate")]
fig.legend(handles=handles, loc="lower center", ncol=8, frameon=False, fontsize=7.5, handlelength=1.4,
           columnspacing=1.0, title="ASR ratio, WHO 2026 / Segi–Doll", title_fontsize=8, bbox_to_anchor=(0.5, 0.0))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig("05_ciktilar/sekiller/EkSekil_S1_harita_ASR_orani.pdf")
fig.savefig("05_ciktilar/sekiller/EkSekil_S1_harita_ASR_orani.png", dpi=300)
open("05_ciktilar/EkSekil_S1_eslesme_raporu.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
