# Ill-defined causes in Korean death certification: district geography and substitution of circulatory deaths, 2011-2024

Analysis code for the manuscript

> Kim S. *Ill-defined causes in Korean death certification vary inversely with circulatory deaths and with long-term care hospital supply.* Submitted to the *International Journal of Legal Medicine*.

Release v1.0.0 of this repository is archived on Zenodo.

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected deaths, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/ILLD/sets_ILLD_std3.json`, `sets_ILLD_s577.json`, `sets_ILLD_s2.json`, `sets_ILLD_s8.json`, `sets_ILLD_sa.json`, `config_ILLD_std3.json`, `run_std3_chain.sh` | Covariates with expected directions, forced controls, negative controls, the pre-specified substitution analyses and model settings (principal model `std3`; sensitivity versions with the queen contiguity graph, without the share aged 80 or older, with ten-group expected deaths and with age-only expected deaths) |
| `04_분석/ILLD/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supplementary material, including `content_illd.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Deaths by underlying cause (ill-defined causes, ICD-10 R00-R99; circulatory diseases I00-I99 and other specific causes; all causes) by sex and district of residence: Statistics Korea, cause-of-death statistics (KOSIS DT_1B34E13), 2011-2024.
- National deaths by cause, sex and 5-year age group (to 85 years or older): Statistics Korea (KOSIS DT_1B34E01), fetched by `34_fetch_national_cause_age_deaths.py` (requires a personal KOSIS API key in `~/.kosis_key`; the key is not included).
- Population by sex and 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected.
- District covariates: a harmonised public district panel (general hospitals, emergency medicine and internal medicine specialists, long-term care hospitals, unmet need, tertiary education, basic livelihood security recipients with corrected cells), the Community Health Survey (walking, moderate-or-higher physical activity, high-risk drinking), the national public sports facility register and Korean Statistical Information Service local indicators (older-adult single-person households, forced and negative controls).

## Pipeline

Run from the repository root (set `ST_DATA_ROOT`, `ST_FBDZIP_CORRECTED` and `ST_GPT_DATASET` to the local copies of the public source files and the read-only district database).

| Step | Script | Output |
|---|---|---|
| 0 | `34_fetch_national_cause_age_deaths.py`, `99R_next5b_mort_counts.py`, `99m_screen_mortality_prep.py`, `98_fit_forced.R`, `99m_screen_mortality.py` | National cause-by-age deaths, district cause counts and spatial screening of causes of death |
| 1 | `99b_extra_canonical_pool.py`, `99c_extra_canonical_pool_alld.py`, `99c_extra_canonical_pool_illd.py` | Outcome counts and district characteristics joined by district code |
| 2 | `39m_illd.py`, `39ms_illd.py` (wrapping `39m_build_Estd_mort.py`, `39ms_build_Esex_mort.py`) | Expected deaths by indirect standardisation (sex by eighteen age groups; age-only and ten-group versions for sensitivity) |
| 3 | `99R_illd_substitution.py`, `99R3_illd_sub_extra.py`, `99S_illd_sex.py`, `99S2_illd_agesex_national.py` | Pre-specified substitution analyses, sex-specific analyses and national rates by sex and age |
| 4 | `80_build_disease_panel_v.py ILLD` (`ST_VER=std3`) | Analytic panel |
| 5 | `81_fit_inla.R ILLD` (`ST_VER=std3`, `ST_GRAPH=04_분석/ILLD/graph_593.graph`, `ST_THREADS=1`; see `04_분석/ILLD/run_std3_chain.sh`, which wraps R jobs in `rslot.sh`) | Principal model, set comparison, 200-subset multiverse, window models |
| 6 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Maps, yearly smoothed ratios and emerging hot spot analysis |
| 7 | `88g_sens_prep.py ILLD std3 CIRC,TRANS`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R` (nb, struct, kh, review) with `kh_constraints.R`, `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models |
| 8 | `04_분석/ILLD/MS/build/` (`build_refs_illd.py`, `figs_illd.py`, `build_ijlm_illd.py`, `esm_illd.py`, `check_ijlm_illd.py`; `run_all_illd.sh`) | Manuscript, Online Resource 1, figures and checks |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.

## Licence

MIT (see `LICENSE`).
