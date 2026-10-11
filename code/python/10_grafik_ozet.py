"""10 — Graphical abstract (PDF and 300-dpi PNG).
Run from the repository root: python3 code/python/10_grafik_ozet.py
Comments in the code body are in Turkish."""
import csv, gzip, logging
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import matplotlib; matplotlib.use("Agg"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt
from scipy import stats

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8985", "#e4e3df"
UP, DOWN, REST = "#2a78d6", "#eb6834", "#d6d5d1"
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "font.size": 9})
q = lambda x, n: str(Decimal(repr(float(x))).quantize(Decimal(n), rounding=ROUND_HALF_UP))

A = {"0": {}, "1": {}}
for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt")):
    if r["yil"] == "2024" and r["kanser_kodu"] == "39" and r["cinsiyet"] == "0" and int(r["vaka_toplam"]) > 0:
        A[r["olcut"]][r["ulke_kodu"]] = (float(r["asr_segi_doll"]), float(r["asr_who2026"]))
T2 = {(r["olcut"]): r for r in csv.DictReader(open("results/tables/T2_sira_uyumu.csv"))
      if r["yil"] == "2024" and r["kanser"] == "All cancers" and r["std_a"] == "segi_doll" and r["std_b"] == "who2026"}
res = {}
for m in ("0", "1"):
    ids = sorted(A[m]); a = np.array([A[m][c][0] for c in ids]); b = np.array([A[m][c][1] for c in ids])
    ra, rb = stats.rankdata(-a), stats.rankdata(-b)
    rho = stats.spearmanr(a, b)[0]; mv20 = int((np.abs(ra - rb) >= 20).sum())
    top = len(set(np.argsort(-a, kind="stable")[:10]) & set(np.argsort(-b, kind="stable")[:10]))
    t = T2["insidans" if m == "0" else "mortalite"]
    assert len(ids) == int(t["n"]) and mv20 == int(t["kayma20"]) and abs(rho - float(t["rho"])) < 5e-5 and top == round(float(t["top10"]) * 10)
    res[m] = dict(n=len(ids), ra=ra, rb=rb, rho=rho, mv20=mv20, top=top)
W = list(csv.DictReader(open("data/weights/agirliklar_ham_yuzde.csv")))
o60 = {k: 100 * sum(Decimal(w[k]) for w in W[12:]) / sum(Decimal(w[k]) for w in W) for k in ("segi_doll", "who2001", "gbd2021", "who2026")}  # after rescaling

fig = plt.figure(figsize=(7, 7))
fig.text(0.05, 0.955, "A new WHO standard population reorders", fontsize=15, fontweight="bold", color=INK)
fig.text(0.05, 0.918, "international cancer mortality rankings", fontsize=15, fontweight="bold", color=INK)
fig.text(0.05, 0.882, "Same GLOBOCAN 2024 data for 186 countries, all cancers, standardised two ways", fontsize=9.5, color=INK2)

# üst şerit: 60+ payı
ax0 = fig.add_axes([0.05, 0.705, 0.90, 0.13])
labs = [("segi_doll", "Segi–Doll\n(GLOBOCAN)"), ("who2001", "WHO\n2000–2025"), ("gbd2021", "GBD\n2021"), ("who2026", "WHO\n2026")]
vals = [float(o60[k]) for k, _ in labs]
ax0.barh(range(4)[::-1], vals, color=[REST, REST, REST, INK2], height=0.62)
for i, (k, l) in enumerate(labs):
    y = 3 - i
    ax0.text(-0.4, y, l.replace("\n", " "), ha="right", va="center", fontsize=8, color=INK)
    ax0.text(vals[i] + 0.3, y, f"{q(o60[k], '0.1')}%", va="center", fontsize=8.5, color=INK, fontweight="bold" if k == "who2026" else None)
ax0.set_xlim(0, 24); ax0.axis("off")
fig.text(0.05, 0.845, "Share of the standard population aged ≥60 years", fontsize=9, color=INK2)
ax0.set_position([0.26, 0.705, 0.66, 0.13])

# alt: iki eğim grafiği
for j, (m, ttl) in enumerate((("0", "Incidence"), ("1", "Mortality"))):
    ax = fig.add_axes([0.08 + j * 0.47, 0.12, 0.38, 0.47])
    r = res[m]; d = r["rb"] - r["ra"]
    order = np.argsort(np.abs(d))
    for i in order:
        col, lw, z = (UP, 1.0, 3) if d[i] <= -20 else (DOWN, 1.0, 3) if d[i] >= 20 else (REST, 0.5, 1)
        ax.plot([0, 1], [r["ra"][i], r["rb"][i]], color=col, lw=lw, zorder=z, solid_capstyle="round")
    ax.set_ylim(r["n"] + 3, -2); ax.set_xlim(-0.08, 1.08)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Segi–Doll", "WHO 2026"], fontsize=8.5, color=INK)
    ax.set_yticks([1, 50, 100, 150, 186] if m == "0" else [1, 50, 100, 150, 186]); ax.tick_params(axis="y", labelsize=7.5, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    for s in ("top", "right", "bottom", "left"): ax.spines[s].set_visible(False)
    ax.set_title(ttl, loc="left", fontsize=12, fontweight="bold", color=INK, pad=34)
    big = f"{r['mv20']} of {r['n']}"
    ax.text(0, 1.085, big, transform=ax.transAxes, fontsize=13, fontweight="bold", color=DOWN if m == "1" else INK)
    ax.text(0, 1.03, f"countries move ≥20 places · ρ = {q(r['rho'], '0.001')}", transform=ax.transAxes, fontsize=8, color=INK2)
    if j == 0: ax.set_ylabel("Country rank (1 = highest ASR)", fontsize=8, color=INK2)
fig.text(0.05, 0.055, "■", color=UP, fontsize=10); fig.text(0.075, 0.057, "rises ≥20 places", fontsize=8, color=INK2)
fig.text(0.25, 0.055, "■", color=DOWN, fontsize=10); fig.text(0.275, 0.057, "falls ≥20 places", fontsize=8, color=INK2)
fig.text(0.45, 0.055, "■", color=REST, fontsize=10); fig.text(0.475, 0.057, "moves <20 places", fontsize=8, color=INK2)
fig.text(0.05, 0.022, f"Mortality: {res['1']['top']} of the 10 highest-ranked countries remain in the top 10. Report cancer mortality "
         "rankings under more than one standard.", fontsize=7.5, color=INK2)
fig.savefig("results/submission/Graphical_Abstract.pdf"); fig.savefig("results/submission/Graphical_Abstract.png", dpi=300)
txt = [f"60+ payı: " + ", ".join(f"{k} {q(v, '0.1')}%" for k, v in o60.items())] + \
      [f"{'insidans' if m == '0' else 'mortalite'}: n={res[m]['n']} rho={res[m]['rho']:.6f} ≥20={res[m]['mv20']} top10={res[m]['top']}" for m in ("0", "1")]
open("results/tables/grafik_ozet_sayilar.txt", "w").write("\n".join(txt) + "\n"); print("\n".join(txt))
