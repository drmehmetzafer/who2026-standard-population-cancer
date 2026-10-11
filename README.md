# WHO 2026 standard population and international cancer rankings

Code and data for:

Sabuncuoğlu MZ, Zihni İ. *The WHO 2026 world standard population reorders country rankings for cancer mortality, but not incidence, through the oldest ages: a preregistered analysis of GLOBOCAN 2022 and 2024.* (submitted to the International Journal of Cancer)

Preregistration: OSF Registries, https://osf.io/stb6m (doi:10.17605/OSF.IO/STB6M; registered 10 October 2026).

## Contents

| Folder | Content |
|---|---|
| `data/raw/` | Age-specific GLOBOCAN 2022 and 2024 cases, deaths and populations (18 age groups) retrieved from the Global Cancer Observatory (Cancer Today) on 10 October 2026; metadata (including each country's estimation method); HDI 2023 (UNDP Human Development Report 2025); `SHA256.txt` checksums |
| `data/weights/` | Standard population weights: Segi–Doll, WHO 2000–2025, GBD 2021 and WHO 2026 rescaled to 100,000 (`agirliklar_100bin_ANALIZ.csv`); all six standards as published percentages, including Scandinavian and European 2013 (`agirliklar_ham_yuzde.csv`) |
| `data/map/` | Natural Earth 1:50m admin-0 country boundaries (public domain), used for Supplementary Figure S1 |
| `code/python/` | `01` validation and ASRs · `02` main preregistered analysis · `03` registered sensitivity analyses · `04` Figure 3 · `05` H2 regression · `06` all 33 sites · `07` sex-specific denominator correction · `08` Supporting Information · `09` map · `10` graphical abstract · `17` registered H3 within sex, registered exploratory analyses, and post hoc analyses (benchmarks, data source, age truncation, cumulative risk) · `18` Figures 1, 2, 4 and S2 |
| `code/R/` | `R_bagimsiz_tekrar.R`: independent replication in R (data.table) of the age-standardised rates and principal rank statistics |
| `results/tables/` | All derived tables; `asr_dort_standart.csv.gz` = ASRs under the four main standards for every cell (full precision) |
| `results/figures/` | Figures as PDF (vector, Arial) and 300-dpi PNG |

## How to reproduce

From the repository root, with Python 3 (NumPy, SciPy, Matplotlib; python-docx for script 08):

```
python3 code/python/01_dogrulama_ve_asr.py
python3 code/python/02_ana_analiz.py
python3 code/python/03_duyarlilik.py
python3 code/python/05_h2_hdi.py
python3 code/python/06_ek_tablo_tum_bolgeler.py
python3 code/python/07_h5_cinsiyete_ozgu_duzeltme.py
python3 code/python/17_ek_analizler_hakem.py
python3 code/python/04_sekiller.py
python3 code/python/18_sekiller_v08.py
python3 code/python/09_harita_ek_sekil_S1.py
python3 code/python/10_grafik_ozet.py
python3 code/python/08_ek_dosya_S1_S7.py
```

Running the scripts in this order from a clean copy reproduces every table in `results/tables/` exactly. R replication (from the repository root): `Rscript code/R/R_bagimsiz_tekrar.R`.

## Notes

- The raw file contains 42,294 exact duplicate rows (all-cancers site retrieved twice); they are identical and do not affect any result (1,437,996 unique records).
- "All cancers" (GLOBOCAN code 39) includes non-melanoma skin cancer; code 40 excludes it.
- Random seed 20261010; 2,000 country bootstrap resamples.
- File names and comments in the code body are in Turkish; script headers are in English.

## Licence

Code: MIT. Derived data: CC BY 4.0. GLOBOCAN source data remain subject to IARC terms of use.
