"""18 — Figure 2 (benchmarks and age truncation), Figure 4 and Supplementary Figure S2.
Run from the repository root: python3 code/python/18_sekiller_v08.py
Comments in the code body are in Turkish."""
import csv, gzip, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
S1, S2 = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans"], "pdf.fonttype": 42, "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})
O = "results/figures/"

# ---------- Figure 1 (four main standards + ESP 2013 dashed) ----------
Wr = list(csv.DictReader(open("data/weights/agirliklar_ham_yuzde.csv")))
ages1 = [r["age_group"] for r in Wr]
fig, ax = plt.subplots(figsize=(7, 3.6))
for key, lab, col, ls, lw in [("segi_doll", "Segi–Doll 1966", "#2a78d6", "-", 2), ("who2001", "WHO 2000–2025", "#eb6834", "-", 2),
                              ("gbd2021", "GBD 2021", "#1baf7a", "-", 2), ("who2026", "WHO 2026", "#eda100", "-", 2.6),
                              ("european2013", "European 2013", "#52514e", "--", 1.4)]:
    v = np.array([float(r[key]) for r in Wr]); v = 100 * v / v.sum()
    ax.plot(range(18), v, color=col, lw=lw, ls=ls, label=lab, marker="o" if ls == "-" else None, ms=4)
ax.set_xticks(range(18)); ax.set_xticklabels(ages1, rotation=45, ha="right")
ax.set_ylabel("Share of standard population (%)"); ax.grid(axis="y", color=GRID, lw=0.6)
ax.axvspan(11.5, 17.5, color=GRID, alpha=0.35, lw=0); ax.text(14.5, 11.6, "≥60 years", ha="center", color=INK2)
ax.legend(frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.13), fontsize=8)
fig.tight_layout(); fig.savefig(O + "Figure1_standards.png", dpi=300); fig.savefig(O + "Figure1_standards.pdf"); plt.close(fig)

# ---------- Figure 2 ----------
S8 = [r for r in csv.DictReader(open("results/tables/T_S8_benchmark.csv")) if r["site"] == "All cancers"]
S14 = list(csv.DictReader(open("results/tables/T_S14_yas_kesme.csv")))
COMP = [("Segi–Doll vs WHO 2000–2025", "Segi–Doll vs WHO 2000–2025"), ("Segi–Doll vs GBD 2021", "Segi–Doll vs GBD 2021"),
        ("WHO 2000–2025 vs GBD 2021", "WHO 2000–2025 vs GBD 2021"), ("GBD 2021 vs WHO 2026", "GBD 2021 vs WHO 2026"),
        ("WHO 2000–2025 vs WHO 2026", "WHO 2000–2025 vs WHO 2026"), ("Segi–Doll vs WHO 2026", "Segi–Doll vs WHO 2026"),
        ("release: Segi–Doll 2022 vs 2024", "GLOBOCAN 2022 vs 2024\n(Segi–Doll, same countries)")]
fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.9), gridspec_kw=dict(width_ratios=[1.35, 1]))
for i, (key, lab) in enumerate(COMP):
    for meas, col, off in (("incidence", S1, -0.14), ("mortality", S2, 0.14)):
        r = next(r for r in S8 if r["comparison"] == key and r["measure"] == meas)
        a.errorbar(float(r["rho"]), i + off, xerr=[[float(r["rho"]) - float(r["rho_lo"])], [float(r["rho_hi"]) - float(r["rho"])]],
                   fmt="o", color=col, ms=4.5, lw=1.2, label=("Incidence" if meas == "incidence" else "Mortality") if i == 0 else None)
        if meas == "mortality":
            a.text(1.004, i + off, r["moved_ge20"], va="center", ha="left", fontsize=7.5, color=S2)
a.text(1.004, -0.95, "≥20\nplaces", ha="left", va="bottom", fontsize=7, color=INK2)
a.set_yticks(range(len(COMP))); a.set_yticklabels([c[1] for c in COMP], fontsize=8); a.invert_yaxis()
for y0, y1, t in ((-0.5, 2.5, "Existing standards"), (2.5, 5.5, "Change to WHO 2026"), (5.5, 6.5, "Release update")):
    a.axhspan(y0, y1, color=GRID, alpha=0.35 if t != "Change to WHO 2026" else 0.0, lw=0)
a.axhline(2.5, color=GRID, lw=0.8); a.axhline(5.5, color=GRID, lw=0.8)
a.set_xlim(0.58, 1.0); a.set_xlabel("Spearman ρ of country ranks (95% CI)")
a.grid(axis="x", color=GRID, lw=0.6); a.set_title("(A) Rank agreement, all cancers", loc="left", fontsize=10, color=INK)
a.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=2, fontsize=8)
ages = ["0–64", "0–74", "0–79", "0–84", "all ages"]; xt = ["64", "74", "79", "84", "All ages"]
ends = []
for site in ("Leukaemia", "Breast", "Thyroid", "Non-Hodgkin lymphoma"):
    y = [float(next(r for r in S14 if r["site"] == site and r["measure"] == "mortality" and r["ages"] == g)["rho"]) for g in ages]
    b.plot(range(5), y, color=INK2, lw=0.9, alpha=0.5, ls="--"); ends.append([y[-1], {"Non-Hodgkin lymphoma": "NHL"}.get(site, site)])
ends.sort(key=lambda t: -t[0])
for i in range(1, len(ends)):
    ends[i][0] = min(ends[i][0], ends[i - 1][0] - 0.0065)
for yv, t in ends: b.text(4.1, yv, t, fontsize=6.5, va="center", color=INK2)
for meas, col in (("incidence", S1), ("mortality", S2)):
    y = [float(next(r for r in S14 if r["site"] == "All cancers" and r["measure"] == meas and r["ages"] == g)["rho"]) for g in ages]
    b.plot(range(5), y, color=col, lw=2.2, marker="o", ms=4, label=f"All cancers, {meas}")
b.set_xticks(range(5)); b.set_xticklabels(xt); b.set_xlabel("Upper age limit of standardisation (years)")
b.set_ylabel("Spearman ρ, Segi–Doll vs WHO 2026"); b.set_ylim(0.84, 1.003); b.set_xlim(-0.2, 4.7)
b.grid(color=GRID, lw=0.6); b.set_title("(B) Effect of the oldest age groups", loc="left", fontsize=10, color=INK)
b.legend(frameon=False, loc="lower left", fontsize=7.5)
b.text(0.02, 0.24, "Dashed: mortality for leukaemia,\nbreast, thyroid, NHL", transform=b.transAxes, fontsize=6.5, color=INK2)
fig.tight_layout(); fig.savefig(O + "Figure2_benchmark_age.png", dpi=300); fig.savefig(O + "Figure2_benchmark_age.pdf"); plt.close(fig)

# ---------- Figure 4 (labels as in Table 1) ----------
LAB = {"All cancers": "All cancers", "Trachea, bronchus and lung": "Lung", "Breast": "Breast (women)", "Colorectum": "Colorectum",
       "Prostate": "Prostate (men)", "Stomach": "Stomach", "Thyroid": "Thyroid", "Liver and intrahepatic bile ducts": "Liver",
       "Bladder": "Bladder", "Cervix uteri": "Cervix uteri (women)", "Non-Hodgkin lymphoma": "NHL", "Pancreas": "Pancreas",
       "Oesophagus": "Oesophagus", "Leukaemia": "Leukaemia"}
T = [r for r in csv.DictReader(open("results/tables/T2_sira_uyumu.csv")) if r["std_a"] == "segi_doll" and r["std_b"] == "who2026" and r["yil"] == "2024"]
sites = list(dict.fromkeys(r["kanser"] for r in T))
fig, ax = plt.subplots(figsize=(6.5, 5))
for i, s in enumerate(sites):
    for m, col, off in (("insidans", S1, -0.15), ("mortalite", S2, 0.15)):
        r = next(r for r in T if r["kanser"] == s and r["olcut"] == m)
        ax.errorbar(float(r["rho"]), i + off, xerr=[[float(r["rho"]) - float(r["rho_lo"])], [float(r["rho_hi"]) - float(r["rho"])]],
                    fmt="o", color=col, ms=5, lw=1.4, capsize=0, label=("Incidence" if m == "insidans" else "Mortality") if i == 0 else None)
ax.set_yticks(range(len(sites))); ax.set_yticklabels([LAB[s] for s in sites]); ax.invert_yaxis()
ax.axvline(0.95, color=INK2, lw=0.8, ls="--"); ax.axvline(0.90, color=INK2, lw=0.8, ls=":")
ax.set_xlim(0.80, 1.0)
ax.set_xlabel("Spearman ρ of country ranks, Segi–Doll vs WHO 2026\n(95% bootstrap CI; GLOBOCAN 2024)"); ax.grid(axis="x", color=GRID, lw=0.6)
ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.4, 1.0))
fig.tight_layout(); fig.savefig(O + "Figure4_rho_sites.png", dpi=300); fig.savefig(O + "Figure4_rho_sites.pdf"); plt.close(fig)

# ---------- Supplementary Figure S2 (former Figure 2) ----------
meta = json.load(open("data/raw/globocan_meta_2022_2024.json"))
SHORT = {"Korea, Democratic People's Republic of": "DPR Korea", "Korea, Republic of": "Rep. of Korea", "Iran, Islamic Republic of": "Iran", "Lao People's Democratic Republic": "Lao PDR"}
CN = {str(x["country"]): SHORT.get(x["label"], x["label"]) for x in meta["meta2024"]["p"]}
A = [r for r in csv.DictReader(gzip.open("results/tables/asr_dort_standart.csv.gz", "rt")) if r["yil"] == "2024" and r["kanser_kodu"] == "39" and r["cinsiyet"] == "0"]
acc = {}
for r in csv.DictReader(gzip.open("data/raw/globocan_yasaozgu_2022_2024.csv.gz", "rt")):
    if r["yil"] == "2024" and r["olcut"] == "0" and r["cinsiyet"] == "0" and r["kanser_kodu"] == "39":
        acc.setdefault(r["ulke_kodu"], {})[int(r["age_code"])] = int(r["nufus"])
P60 = {c: (v[12] + v[13] + v[14] + (v[117] - v[14])) / v[99] for c, v in acc.items()}
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
for ax, m, ttl in zip(axes, ("0", "1"), ("(A) Incidence", "(B) Mortality")):
    R = [r for r in A if r["olcut"] == m]
    x = np.array([100 * P60[r["ulke_kodu"]] for r in R]); y = np.array([float(r["asr_who2026"]) / float(r["asr_segi_doll"]) for r in R])
    ax.scatter(x, y, s=22, color=S1, edgecolor="white", lw=0.6, zorder=3)
    for k in (int(np.argmax(y)), int(np.argmin(y)), int(np.argmax(x))):
        ax.scatter(x[k], y[k], s=30, facecolor="none", edgecolor=INK, lw=0.9, zorder=4)
        ax.annotate(CN[R[k]["ulke_kodu"]], (x[k], y[k]), fontsize=7, color=INK2, xytext=(5, -3 if k == int(np.argmin(y)) else 3), textcoords="offset points")
    ax.set_title(ttl, color=INK, loc="left", fontsize=10); ax.set_xlabel("Population aged ≥60 years (%)"); ax.grid(color=GRID, lw=0.6)
axes[0].set_ylabel("ASR ratio, WHO 2026 / Segi–Doll")
fig.tight_layout(); fig.savefig(O + "FigureS2_ratio_age60.png", dpi=300); fig.savefig(O + "FigureS2_ratio_age60.pdf"); plt.close(fig)
print("ok")
