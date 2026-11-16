# esm_illd.py — ILLD International Journal of Legal Medicine Online Resource 1 (ESM_1: Appendix A·Table S1-S4·Appendix B STROBE/RECORD) (2026-11-16). IJLM 규정: 파일마다 논문 제목·저널명·저자·소속·교신 이메일.
#  수치는 결과 CSV에서만. 영국식 철자(TX가 brit 적용), 표 제목 쌍점 금지, 사후 검토는 post hoc 표기, 보충 표 번호 = 본문 첫 인용 순서(S1 공변량 → S2 점검 → S3 대체 → S4 사양).
import os, re, json, subprocess, pandas as pd
import content_illd as C
from build_ijlm_illd import LABEL, GROUPS, TX, TITLE as DTITLE, foot_row, read_draft, AFFIL
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out"); B = os.path.dirname(MSD); RS = os.path.join(B, "results_std3")
N = C.N
st = lambda t: f"{t[0]:.3f} ({t[1]:.3f}–{t[2]:.3f})"
J = TX(cite="bracket")
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=True)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Online Resource 1</b>"); J.para(f"Article title: {DTITLE}"); J.para("Journal: International Journal of Legal Medicine"); J.para(f"Author: Seongdae Kim. {AFFIL}. Corresponding author email: kimsd@hongik.ac.kr")
J.para("Contents. Appendix A (supplementary methods and additional results); Table S1 (substitution, additional measures); Table S2 (district characteristics); Table S3 (panel checks); Table S4 (alternative specifications); Appendix B (STROBE and RECORD checklist).")
_MT = pd.read_csv(os.path.join(B, "panel_META_ILLD_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
assert int(_MT.loc["older_single_household_share", "obs_year_min"]) == 2015
gate = open(os.path.join(B, "data_gate_ILLD_std3_261112.txt"), encoding="utf-8").read(); nwarn = int(re.search(r"경고 (\d+)건", gate).group(1))
two = re.findall(r"\[연도 간 평균 2배 이상 차이\] (\S+):", gate); cnt = lambda tag: len(re.findall(r"\[" + re.escape(tag) + r"\]", gate))
assert nwarn == 3 + len(two) + cnt("비율형인데 100 초과") + cnt("전 연도 0인 지역"), (nwarn, len(two))
_vif = _MT.vif_final.dropna().sort_values(ascending=False); assert _vif.index[0] == "older_single_household_share" and _vif.iloc[1] < 10
J.page_break(); J.head("Appendix A. Supplementary methods and additional results", 2)
SM = [("Outcome.", "Annual deaths with an underlying cause in ICD-10 Chapter XVIII (R00–R99) by district of residence came from the 104-item district cause-of-death table of Statistics Korea and matched, in all 3206 district-years, an independent extraction of the same item; the sum over districts equalled the national total each year. The district table does not split the chapter into senility (R54), sudden death (R96), unattended death (R98) and unknown cause (R99). Districts were harmonised to the 229 units of 2024 (urban wards of metropolitan cities, cities and counties) and joined across sources by administrative code."),
      ("Expected deaths.", "National deaths in Chapter XVIII by sex and age (0–4 to 80–84 years and 85 years or older) came from the national cause-of-death table by cause, sex and age. District populations by sex and 5-year age group came from resident registration statistics; the 2023 age-specific populations of Changwon, which repeated the 2022 values in the source file, were replaced with the official 2023 values (total 1 009 038) before expected deaths and population-based covariates were computed. Alternative expected deaths used age only (18 groups) or ten broad age groups (sensitivity analyses). For the substitution analysis, expected deaths for each specific cause were computed in the same way from national cause-specific rates."),
      ("Covariates.", f"Walking, moderate-or-higher physical activity and high-risk drinking were age-standardised district rates from the Community Health Survey; moderate physical activity was missing for one survey year and was interpolated within districts. Public and village sports facilities came from the national public sports facility register. General hospitals, specialists, long-term care hospitals, unmet need, tertiary education and basic livelihood recipients came from a harmonised public district panel; recipient shares for 2021–2023 that were below 0.2 times or above 5 times the mean of the same district in 2020 and 2024 (collapsed values in districts of cities with general wards) were set to missing and linearly interpolated within districts. The share of older-adult single-person households was published from 2015; earlier years carried district means. A sensitivity analysis added the share of residents' medical care used outside their district."),
      ("Panel checks before modelling.", f"An automated gate run on the analytic panel before any model was fitted reported {nwarn} flags (Table S3), mostly standardised columns whose yearly means were near 0 (a ratio artefact), the post-2020 indicator (constant by design) and districts with no general hospital, emergency medicine specialist or long-term care hospital in any year. Final variance inflation factors were below 10 except for older-adult single-person households ({_vif.iloc[0]:.2f}), which was retained as a pre-specified characteristic."),
      ("Models.", f"Software: R 4.6.0 with R-INLA (one thread); Python 3.9 for data preparation, substitution analyses and figures. Fixed effects had normal priors with mean 0 and precision 4 (intercept precision 0.001). The Besag–York–Mollié 2 district effect used penalised-complexity priors (P(σ > 0.5) = 0.01; P(φ < 0.5) = 2/3) on a 593-edge district adjacency graph with Jeju Island as a separate component; the random-walk and independent year effects used penalised-complexity priors (P(σ > 0.5) = 0.01). Covariate subsets for the multiverse were drawn with a fixed seed, each characteristic entering with probability 0.5. Knorr-Held interactions used Kronecker-product structures (type I: independent; II: random walk in time by independent districts; III: independent years by intrinsic conditional autoregressive districts; IV: random walk by intrinsic conditional autoregressive districts). The Spatial+-type method regressed each standardised covariate on the lowest-frequency eigenvectors of the graph Laplacian. Between- and within-district components were the district mean and the deviation from district and year means, entered together. E-values were computed for the rate ratio and for the interval limit closer to 1."),
      ("Substitution analysis.", "District standardised mortality ratios (SMRs) were pooled over 14 years as summed observed over summed expected deaths. The combined SMR for ill-defined deaths plus a specific cause was (O_ill + O_cause)/(E_ill + E_cause). Random pairings permuted the specific-cause observed and expected counts across districts 999 times (fixed seed) and recomputed the variance of the log combined SMR. Moran's I used the same row-standardised 593-edge graph with 999 permutations. Changes in log SMR compared district SMRs in 2016–2019 or 2020–2024 with those in 2011–2015. Within-district yearly deviations were log SMRs minus district and year means; the weighted version weighted district-years by expected deaths.")]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
J.para("<b>Additional results.</b> " + f"Posterior predictive 95% intervals covered {100*N['ppc']['coverage95']:.1f}% of district-years. The spatially structured district component accounted for {100*N['vp_spatial']:.0f}% of the variance of the linear predictor, a different quantity from the mixing parameter of the district effect reported in the main text. "
       f"The post-2020 indicator was not associated with ill-defined deaths after adjustment ({st(N['covid_main'])}). The share of medical care used outside the district, added in a sensitivity analysis, was inversely associated ({st(N['outside'])}), and the five characteristics remained credible. "
       f"The ratio of the 90th to the 10th percentile of smoothed annual district SMRs was {N['gap'][2011]['ratio']:.2f} in 2011 and {N['gap'][2024]['ratio']:.2f} in 2024.")
# ── Table S3: 대체 분석 상세 ──
S = N["sub"]; W2 = N["subw"]; PRE = N["sub_pre"]
rows = []
for k, lab in (("CIRC", "Circulatory diseases"), ("IHD", "Ischaemic heart disease"), ("STRK", "Cerebrovascular disease"), ("ALZ", "Alzheimer disease"), ("PNEU", "Pneumonia"), ("CANM", "Malignant neoplasms")):
    r = S[k]; w = W2.get(k, {}); pre = PRE.get(("W1_W2_precovid", k)); post = PRE.get(("W1_W3", k))
    rows.append([lab, f"{int(r['cause_deaths_14y'])}", f"{r['rho_SMR']:.2f}", f"{r['P90P10_cause']:.2f} / {r['P90P10_combined']:.2f}", f"{r['moran_cause']:.2f} / {r['moran_combined']:.2f}",
                 f"{pre[0]:.2f}" if pre else "–", f"{post[0]:.2f}" if post else "–", f"{w['r_within_year_dev']:.2f}" if w else "–"])
NA = N["asr"]
TF("Table S1 Substitution between ill-defined and specific causes, additional measures, 229 districts, Republic of Korea, 2011–2024", ["Specific cause", "Deaths, 2011–2024", "ρ, SMR", "P90/P10, cause / combined", "Moran's I, cause / combined", "ρ, change to 2016–2019", "ρ, change to 2020–2024", "r, within district"], rows,
   f"SMR: standardised mortality ratio; P90/P10: ratio of the 90th to the 10th percentile of district SMRs; combined: ill-defined plus the specific cause. Changes are in log SMR from 2011–2015. –, not computed. "
   f"National age-standardised rates per 100 000 (2015 population): ill-defined {NA[2011]['ILLD']:.1f} (2011), {NA[2015]['ILLD']:.1f} (2015), {NA[2019]['ILLD']:.1f} (2019), {NA[2024]['ILLD']:.1f} (2024); circulatory {NA[2011]['CIRC']:.1f}, {NA[2015]['CIRC']:.1f}, {NA[2019]['CIRC']:.1f}, {NA[2024]['CIRC']:.1f}. "
   f"Sex-specific analyses: men, {N['sexsub']['남자']['illd_deaths']} ill-defined deaths, ρ SMR {N['sexsub']['남자']['rho_SMR']:.2f}; women, {N['sexsub']['여자']['illd_deaths']}, ρ {N['sexsub']['여자']['rho_SMR']:.2f}; correlation of male and female SMRs for ill-defined deaths, ρ {N['rho_mf']:.2f}.", fs=7)
# ── Table S1 ──
DIR = {C.GH: "−", C.EM: "−", C.IM: "−", C.LTC: "−", C.UN: "+", C.ALN: "+", C.BLS: "+", C.TE: "−", C.DR: "+", C.WALK: "−", C.MPA: "−", C.FAC: "−", C.VIL: "−"}
SRCN = {C.GH: "District panel", C.EM: "District panel", C.IM: "District panel", C.LTC: "District panel", C.UN: "Community Health Survey", C.ALN: "KOSIS local indicators", C.BLS: "District panel", C.TE: "Census (district panel)",
        C.DR: "Community Health Survey", C.WALK: "Community Health Survey", C.MPA: "Community Health Survey", C.FAC: "Sports facility register", C.VIL: "Sports facility register",
        "urban_population_share": "KOSIS local indicators", "physicians_per_1000": "KOSIS local indicators", "sex_ratio": "KOSIS local indicators", "fiscal_independence": "KOSIS local indicators", "pop80_share": "Resident registration"}
UNIT = {C.GH: "per 100 000", C.EM: "per 100 000", C.IM: "per 100 000", C.LTC: "per 100 000 aged ≥ 65", C.UN: "%", C.ALN: "% of households", C.BLS: "%", C.TE: "% of adults", C.DR: "%", C.WALK: "%", C.MPA: "%",
        C.FAC: "per 100 000", C.VIL: "per 100 000", "urban_population_share": "%", "physicians_per_1000": "per 1 000", "sex_ratio": "ratio", "fiscal_independence": "%", "pop80_share": "%"}
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]; rows.append([f"  {LABEL[v].split(' (')[0]}", UNIT[v], SRCN[v], f"{int(m.obs_year_min)}–{int(m.obs_year_max)}", ("Forced" if m.role == "forced" else DIR[v]), f"{_imp(v)}"])
TF("Table S2 Source, unit, observed years, expected direction and filled cells for each district characteristic, 229 districts, Republic of Korea, 2011–2024", ["Characteristic", "Unit", "Source", "Years", "Direction", "Filled cells"], rows,
   "KOSIS: Korean Statistical Information Service; ratio, men per 100 women; forced, in every model. Expected directions for ill-defined deaths were set before any covariate model was fitted. Filled cells of 3206 district-years: interpolation within districts, district means or yearly means; collapsed recipient shares replaced after the panel checks (Table S3) are not counted here.", fs=7)
# ── Table S2 ──
ext = json.load(open(os.path.join(RS, "S41_extreme_flags.json"))); impc = json.load(open(os.path.join(RS, "S41_imputed_cells.json")))
rows = [["Year with all districts zero or missing", "≥ 98% of districts", "1 (post-2020 indicator)", "None (by design)"],
        ["Constant within a year", "1 value in a year", "1 (same indicator)", "None (by design)"],
        ["Year explains most variance", "Year R² ≥ 0.80", "1 (same indicator)", "None (by design)"],
        ["Yearly means differ twofold or more", "Max/min yearly mean ≥ 2", f"{len(two)} (mostly standardised, mean near 0)", "Checked against sources; retained"],
        ["Ratio-type column above 100", "Maximum > 100", f"{cnt('비율형인데 100 초과')} (sex ratio, men per 100 women)", "Retained (definition)"],
        ["District zero in every year", "All years 0", f"{cnt('전 연도 0인 지역')} (general hospitals, emergency specialists, long-term care hospitals)", "Retained (true zeros)"],
        ["Extreme district-years", "> 5 IQR beyond quartiles", f"{sum(ext.values())} cells in {sum(1 for v in ext.values() if v)} covariates", "Refilled in one alternative specification"],
        ["Missing district-years", "No observation", f"{sum(impc.values())} cells across {len(impc)} covariates", "Filled by interpolation within districts, district means or yearly means"],
        ["Duplicated population block", "Repeats 2022", "1 district-year (Changwon, 2023)", "Replaced with official total"],
        ["Collapsed recipient shares", "Below 0.2 or above 5 times the district mean of 2020 and 2024", "City-ward districts, 2021–2023", "Set to missing and interpolated within districts"]]
TF("Table S3 Panel checks before modelling, 3206 district-years, Republic of Korea, 2011–2024", ["Check", "Threshold", "Flags in this panel", "Action"], rows, "Checks were run on the analytic panel before any model was fitted. IQR: interquartile range.")
# ── Table S4: 사양 ──
NAMES = [("principal", "Principal model"), ("KH_typeI", "Knorr-Held type I"), ("KH_typeII", "Knorr-Held type II"), ("KH_typeIII", "Knorr-Held type III"), ("KH_typeIV", "Knorr-Held type IV"),
         ("icar_besag", "ICAR district effect"), ("iid_only", "IID district effect"), ("no_spatial", "No district effect"), ("knn3", "3 nearest neighbours"), ("knn4", "4 nearest neighbours"), ("knn5", "5 nearest neighbours"),
         ("pc_phi_flat", "Flat prior on mixing"), ("pc_relaxA", "Relaxed priors A"), ("pc_relaxB", "Relaxed priors B"),
         ("B3_smooth_forced", "Smoothed sex ratio"), ("C1_poisson_lognormal", "Poisson, observation effect"), ("C2_rw2_year", "RW2 year effect"), ("C3_ar1_year", "AR1 year effect"), ("C4_sido_year_iid", "Province-by-year effect"), ("D1_spatial_plus", "Spatial+-type"),
         ("E0_nolag_from2012", "No lag, from 2012"), ("E1_lag1", "Lag 1 year"), ("E0_nolag_from2013", "No lag, from 2013"), ("E2_lag2", "Lag 2 years"), ("F3_extreme_R7", "Extreme values refilled"), ("G1_kchs_ma3", "Survey 3-year averages"), ("H4_odd_years", "Odd years only"), ("H4_even_years", "Even years only"),
         ("sa", "Age-only expected deaths"), ("s8", "Ten age groups in E"), ("s2", "Share aged 80+ omitted"), ("s577", "Queen graph, 577 edges"),
         ("H1_nco_CIRC", "Circulatory deaths (comparison)"), ("H1_nco_TRANS", "Transport-injury deaths (comparison)")]
SS = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}
for v in ("s577", "s2", "s8", "sa"): SS.update({(v, c): t for c, t in N["sens"][v].items()}); WA[v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
WA["principal"] = N["waic_main"]; SS.update({("principal", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["main"].items()})
def cell(a, v): t = SS.get((a, v)); return "–" if t is None else st(t)
ALT = set(N["alt"]); assert ALT <= {a for a, _ in NAMES}, sorted(ALT - {a for a, _ in NAMES})
HN = {C.LTC: "Long-term care hospitals", C.TE: "Tertiary-educated adults", C.BLS: "Basic livelihood recipients", C.MPA: "Moderate physical activity", C.EM: "Emergency medicine specialists"}
_F3 = f"Values are rate ratios (95% credible intervals) per 1 standard deviation; –, not computed. <sup>a</sup>One of the {len(ALT)} alternative specifications counted in the text. For the Spatial+-type model, rate ratios are per 1 standard deviation of the residualised covariate. Comparison outcomes were fitted with the same covariates and model. WAIC: widely applicable information criterion (not comparable across outcomes or numbers of years); ICAR: intrinsic conditional autoregressive; IID: independent and identically distributed; RW2: second-order random walk; AR1: first-order autoregressive; E: expected deaths."
for part, cols in (("A", [C.LTC, C.TE, C.BLS]), ("B", [C.MPA, C.EM])):
    rows = [[lab + ("<sup>a</sup>" if a in ALT else "")] + ([f"{WA[a]:.0f}" if a in WA and not a.startswith("H1_") else "–"] if part == "A" else []) + [cell(a, v) for v in cols] for a, lab in NAMES]
    TF(f"Table S4 Rate ratios per 1 standard deviation across alternative specifications and comparison outcomes, 229 districts, Republic of Korea, 2011–2024 (part {part})", ["Specification"] + (["WAIC"] if part == "A" else []) + [HN[v] for v in cols], rows, _F3, fs=7)
# ── STROBE·RECORD ──
MH = [x[0] for x in C.METHODS]; RH = [x[0] for x in C.RESULTS]
CK = [("Title and abstract", "1", "Title page; Abstract"), ("RECORD 1.1–1.3 Data type, geography, linkage", "1", f"Abstract; Methods, {MH[0]}"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"),
      ("Study design", "4", f"Methods, {MH[0]}"), ("Setting", "5", f"Methods, {MH[0]}"), ("Participants", "6", f"Methods, {MH[0]} (all registered deaths; ecological)"), ("RECORD 6.1–6.3 Population selection, codes, linkage", "6", f"Methods, {MH[0]}; {MH[1]}; Appendix A"),
      ("Variables", "7", f"Methods, {MH[1]}; {MH[3]}; Table S2"), ("RECORD 7.1 Codes and algorithms", "7", f"Methods, {MH[1]}; {MH[2]}"), ("Data sources/measurement", "8", "Methods; Appendix A; Table S3"),
      ("Bias", "9", f"Methods, {MH[4]}; Table S4"), ("Study size", "10", f"Methods, {MH[0]} (all 229 districts)"), ("Quantitative variables", "11", f"Methods, {MH[3]}"),
      ("Statistical methods", "12", f"Methods, {MH[2]}; {MH[4]}"), ("RECORD 12.1–12.2 Data access and cleaning", "12", "Appendix A; Table S3; Data availability"),
      ("Participants (flow)", "13", "Not applicable (aggregate district data; no exclusions)"), ("Descriptive data", "14", f"Results, {RH[0]}; Table 1"), ("Outcome data", "15", f"Results, {RH[0]}; Table 1; Fig. 1"),
      ("Main results", "16", f"Results, {RH[1]}; {RH[2]}; Tables 2–3; Figs 2–3"), ("Other analyses", "17", f"Results, {RH[1]}; {RH[2]}; Tables S1 and S4"),
      ("Key results", "18", "Discussion, first paragraph"), ("Limitations", "19", "Discussion, limitations paragraph"), ("Interpretation", "20", "Discussion"), ("Generalisability", "21", "Discussion, final paragraph"),
      ("RECORD 22.1 Access to code and data", "22", "Data availability"), ("Funding", "22", "Funding")]
J.page_break()
J.table_fit("Appendix B. STROBE and RECORD checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], "", fs_max=8, title_bold=True)
foot_row(J, "STROBE: Strengthening the Reporting of Observational Studies in Epidemiology; RECORD: Reporting of studies Conducted using Observational Routinely-collected health Data.", 8, 12)
ps = os.path.join(OUT, "ESM_1.docx"); J.doc_title = "Online Resource 1"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_illd_esm", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
