"""04 — Figures 1 and 3 (and earlier versions of Figures 2 and 4). Writes results/figures/.
Run from the repository root: python3 code/python/04_sekiller.py
Comments in the code body are in Turkish."""
import csv, gzip, json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("results/tables/sekiller", exist_ok=True)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans"], "pdf.fonttype": 42, "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})

# Şekil 1 — dört standardın yaş dağılımı
W = list(csv.DictReader(open("data/weights/agirliklar_100bin_ANALIZ.csv")))
ages = [r["age_group"] for r in W]
fig, ax = plt.subplots(figsize=(7, 3.6))
for key, lab, col in [("segi_doll", "Segi–Doll 1966", S1), ("who2001", "WHO 2000–2025", S2),
                      ("gbd2021", "GBD 2021", S3), ("who2026", "WHO 2026", S4)]:
    y = [float(r[key]) / 1000 for r in W]
    ax.plot(range(18), y, color=col, lw=2.6 if key == "who2026" else 2, label=lab, marker="o", ms=4)
ax.set_xticks(range(18)); ax.set_xticklabels(ages, rotation=45, ha="right")
ax.set_ylabel("Share of standard population (%)"); ax.grid(axis="y", color=GRID, lw=0.6)
ax.axvspan(11.5, 17.5, color=GRID, alpha=0.35, lw=0); ax.text(14.5, 11.6, "≥60 years", ha="center", color=INK2)
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))
fig.tight_layout(); fig.savefig("results/figures/Sekil1_standart_yas_dagilimi.png", dpi=300); fig.savefig("results/figures/Sekil1_standart_yas_dagilimi.pdf"); plt.close(fig)

# veri
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
SHORT = {"Korea, Democratic People's Republic of": "DPR Korea", "Korea, Republic of": "Rep. of Korea", "Iran, Islamic Republic of": "Iran", "Lao People's Democratic Republic": "Lao PDR"}
CN = {str(x["country"]): SHORT.get(x["label"], x["label"]) for x in meta["meta2024"]["p"]}
A = [r for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt"))
     if r["yil"] == "2024" and r["kanser_kodu"] == "39" and r["cinsiyet"] == "0"]
P60 = {}
raw = gzip.open("data/raw/globocan_yasaozgu_2022_2024.csv.gz", "rt")
acc = {}
for r in csv.DictReader(raw):
    if r["yil"] == "2024" and r["olcut"] == "0" and r["cinsiyet"] == "0" and r["kanser_kodu"] == "39":
        acc.setdefault(r["ulke_kodu"], {})[int(r["age_code"])] = int(r["nufus"])
# 60+ = 12,13,14 doğrudan + 75+ (117 − 14)
for c, v in acc.items():
    P60[c] = (v[12] + v[13] + v[14] + (v[117] - v[14])) / v[99]

# Şekil 2 — ASR oranı × 60+ payı (insidans, mortalite)
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
for ax, m, ttl in zip(axes, ("0", "1"), ("Incidence", "Mortality")):
    R = [r for r in A if r["olcut"] == m]
    x = np.array([100 * P60[r["ulke_kodu"]] for r in R]); y = np.array([float(r["asr_who2026"]) / float(r["asr_segi_doll"]) for r in R])
    ax.scatter(x, y, s=22, color=S1, edgecolor="white", lw=0.6, zorder=3)
    for r, xi, yi in zip(R, x, y):
        if yi == y.max() or yi == y.min() or xi == x.max(): ax.annotate(CN[r["ulke_kodu"]], (xi, yi), fontsize=7, color=INK2, xytext=(4, 2), textcoords="offset points")
    ax.set_title(("(A) " if m == "0" else "(B) ") + ttl, color=INK, loc="left", fontsize=10); ax.set_xlabel("Population aged ≥60 years (%)")
    ax.grid(color=GRID, lw=0.6)
axes[0].set_ylabel("ASR ratio, WHO 2026 / Segi–Doll")
fig.suptitle("All cancers, both sexes, GLOBOCAN 2024 (186 countries)", x=0.01, ha="left", fontsize=9, color=INK2)
fig.tight_layout(); fig.savefig("results/figures/Sekil2_oran_60plus.png", dpi=300); fig.savefig("results/figures/Sekil2_oran_60plus.pdf"); plt.close(fig)

# Şekil 3 — eğim grafiği: mortalite, Segi ilk 20 ∪ WHO2026 ilk 20 sıraları
R = [r for r in A if r["olcut"] == "1"]
rk = lambda key: {r["ulke_kodu"]: i + 1 for i, r in enumerate(sorted(R, key=lambda r: -float(r[key])))}
a, b = rk("asr_segi_doll"), rk("asr_who2026")
sel = [c for c in a if a[c] <= 20 or b[c] <= 20]
fig, ax = plt.subplots(figsize=(6, 7))
for c in sel:
    up = b[c] < a[c]; col = S1 if b[c] <= 20 and a[c] > 20 else (S2 if a[c] <= 20 and b[c] > 20 else "#a9a8a2")
    ax.plot([0, 1], [a[c], b[c]], color=col, lw=2 if col != "#a9a8a2" else 1.2)
    ax.text(-0.03, a[c], f"{CN[c]} ({a[c]})", ha="right", va="center", fontsize=7, color=INK if a[c] <= 20 else INK2)
    ax.text(1.03, b[c], f"({b[c]}) {CN[c]}", ha="left", va="center", fontsize=7, color=INK if b[c] <= 20 else INK2)
ax.set_ylim(max(max(a[c] for c in sel), max(b[c] for c in sel)) + 2, 0); ax.set_xlim(-0.75, 1.75)
ax.set_xticks([0, 1]); ax.set_xticklabels(["Segi–Doll rank", "WHO 2026 rank"]); ax.set_yticks([])
ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
ax.set_title("Cancer mortality, all cancers, both sexes, GLOBOCAN 2024\nBlue: enters top 20 under WHO 2026 · Orange: leaves top 20", fontsize=9, color=INK2, loc="left")
fig.tight_layout(); fig.savefig("results/figures/Sekil3_egim_mortalite_ilk20.png", dpi=300); fig.savefig("results/figures/Sekil3_egim_mortalite_ilk20.pdf"); plt.close(fig)

# Şekil 4 — 13 bölge: ρ(Segi, WHO 2026), insidans vs mortalite
T = [r for r in csv.DictReader(open("results/tables/T2_sira_uyumu.csv")) if r["std_a"] == "segi_doll" and r["std_b"] == "who2026" and r["yil"] == "2024"]
sites = list(dict.fromkeys(r["kanser"] for r in T))
fig, ax = plt.subplots(figsize=(6.5, 5))
for i, s in enumerate(sites):
    for m, col, off in (("insidans", S1, -0.15), ("mortalite", S2, 0.15)):
        r = next(r for r in T if r["kanser"] == s and r["olcut"] == m)
        ax.errorbar(float(r["rho"]), i + off, xerr=[[float(r["rho"]) - float(r["rho_lo"])], [float(r["rho_hi"]) - float(r["rho"])]],
                    fmt="o", color=col, ms=5, lw=1.4, capsize=0, label=("Incidence" if m == "insidans" else "Mortality") if i == 0 else None)
ax.set_yticks(range(len(sites))); ax.set_yticklabels(sites); ax.invert_yaxis()
ax.axvline(0.95, color=INK2, lw=0.8, ls="--"); ax.axvline(0.90, color=INK2, lw=0.8, ls=":")
ax.set_xlabel("Spearman ρ of country ranks, Segi–Doll vs WHO 2026\n(95% bootstrap CI; GLOBOCAN 2024)"); ax.grid(axis="x", color=GRID, lw=0.6)
ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.4, 1.0))
fig.tight_layout(); fig.savefig("results/figures/Sekil4_rho_bolgeler.png", dpi=300); fig.savefig("results/figures/Sekil4_rho_bolgeler.pdf"); plt.close(fig)
print("ok")
