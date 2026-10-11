# WHO 2026 standard population and the global cancer map

Code and data for:

Sabuncuoğlu MZ, Zihni İ. *A new world standard, a new cancer map? Impact of the WHO 2026 standard population on age-standardised cancer incidence, mortality and country rankings.* (submitted to the International Journal of Cancer)

Preregistration: OSF Registries, https://osf.io/stb6m (registered 10 October 2026).

## Contents

| Folder | Content |
|---|---|
| `data/raw/` | Age-specific GLOBOCAN 2022 and 2024 cases, deaths and populations (18 age groups) retrieved from the Global Cancer Observatory (Cancer Today) on 10 October 2026; metadata; HDI 2023 (UNDP Human Development Report 2025); `SHA256.txt` checksums |
| `data/weights/` | Segi–Doll, WHO 2000–2025, GBD 2021 and WHO 2026 standard population weights (`agirliklar_100bin_ANALIZ.csv`, rescaled to 100,000) |
| `code/python/` | `01` validation and ASRs · `02` main analysis · `03` sensitivity · `04` figures · `05` H2 regression · `06` all sites · `07` sex-specific denominator correction · `08` supplementary tables · `09` map · `10` graphical abstract · `11` numerical audit |
| `code/R/` | `R_bagimsiz_tekrar.R` independent replication in R (data.table) of the age-standardised rates and principal rank statistics |
| `results/tables/` | All derived tables; `asr_dort_standart.csv.gz` = ASRs under the four standards for every cell (full precision) |

## Notes

- The raw file contains 42,294 exact duplicate rows (all-cancers site retrieved twice); scripts remove them (1,437,996 unique records).
- Python 3 with NumPy and SciPy; random seed 20261010. R 4.6.0 with data.table.
- Script comments are in Turkish.


## Licence

Code: MIT. Derived data: CC BY 4.0. GLOBOCAN source data remain subject to IARC terms of use.
