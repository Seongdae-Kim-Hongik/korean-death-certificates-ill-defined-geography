# numbers_illd.py — ILLD(R00-R99 불명확 사인 사망) IJLM 원고의 모든 수치를 결과 CSV에서 읽는다(2026-11-12, numbers_nihd.py 구조 이식). 손입력 금지, assert로 정합 확인.
import os, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3"); SUB = os.path.join(B, "results_sub"); SEX = os.path.join(B, "results_sex")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널")
SHP = os.environ.get("ST_SHP", os.path.expandvars("$ST_DATA_ROOT") + "/기타/R_Studio/FBD_DATA_ZIP/final.shp")
WIN = [("W1_2011-15", 2011, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-24", 2020, 2024)]
rd = lambda f, d=RS, **k: pd.read_csv(os.path.join(d, f), encoding="utf-8-sig", **k)
EM, LTC, BLS, TE, MPA = "em_specialists_per_100k", "ltc_hospitals_per_100k_65", "basic_livelihood_rate", "tertiary_educated_share", "moderate_pa_rate"
ROB = [LTC, BLS, TE, MPA, EM]
GH, IM, UN, ALN, DR, WALK, FAC, VIL = "ext__genhosp_per100k", "im_specialists_per_100k", "ext__unmet_need_rate", "older_single_household_share", "high_risk_drinking_rate", "walking_practice_rate", "public_sports_facilities_per_100k", "village_sports_facilities_per_100k"
HYP = [GH, EM, IM, LTC, UN, ALN, BLS, TE, DR, WALK, MPA, FAC, VIL]
FORCED = ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"]
KH = ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV")

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_ILLD_std3.csv")); N["n_rows"], N["n_districts"] = len(P), P.fbd_region.nunique(); assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    N["cases_total"] = int(P.cases.sum()); assert N["cases_total"] == 427264
    X = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_ILLD_261112.csv")); xs = X.groupby("year")[["illd_deaths", "circ_deaths", "all_deaths"]].sum()
    assert int(xs.illd_deaths.sum()) == N["cases_total"]
    N["all_total"] = int(xs.all_deaths.sum()); N["circ_total"] = int(xs.circ_deaths.sum())
    N["share"] = (100 * xs.illd_deaths / xs.all_deaths).to_dict(); N["n_y"] = xs.illd_deaths.astype(int).to_dict()
    N["share_min_year"] = min(N["share"], key=N["share"].get)
    T1 = {}
    for wn, a, b in WIN + [("ALL", 2011, 2024)]:
        q = P[P.year.between(a, b)]; x = xs.loc[a:b]; smr = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), all=int(x.all_deaths.sum()), share=100 * x.illd_deaths.sum() / x.all_deaths.sum(), circ=100 * x.circ_deaths.sum() / x.all_deaths.sum(),
                      p10=smr.quantile(.1), med=smr.median(), p90=smr.quantile(.9), cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in HYP + FORCED})
    N["T1"] = T1
    # 성·연령(SAGER)
    A = rd("national_share_by_sex_age.csv", SEX); N["agesex"] = {(r.year, r.sex, r.ag): r.share for r in A.itertuples()}
    S = rd("SUB_by_sex.csv", SEX).set_index("sex"); N["sexsub"] = S.to_dict("index"); assert (S.p_combined_smaller <= 0.001).all() and (S.rho_SMR < 0).all()
    C = rd("ILLD_sex_counts_E.csv", SEX); N["n_m"], N["n_f"] = int(C.illd_남자.sum()), int(C.illd_여자.sum()); assert N["n_m"] + N["n_f"] == N["cases_total"]
    b = C.groupby("fbd_region")[["illd_남자", "illd_여자", "E_illd_남자", "E_illd_여자"]].sum(); N["rho_mf"] = float((b.illd_남자 / b.E_illd_남자).corr(b.illd_여자 / b.E_illd_여자, method="spearman"))
    # 대체 분석
    D = rd("SUB_A1_A3_A4_district.csv", SUB).set_index("cause"); N["sub"] = D.to_dict("index")
    W2 = rd("SUB_A2_change_within.csv", SUB).set_index("cause"); N["subw"] = W2.to_dict("index")
    Pc = rd("SUB_A2b_precovid.csv", SUB); N["sub_pre"] = {(r.pair, r.cause): (r.rho, r.p) for r in Pc.itertuples()}
    NA = rd("SUB_national_asr.csv", SUB).set_index("year"); N["asr"] = NA.to_dict("index")
    sm = rd("SUB_district_SMR.csv", SUB); N["sub_smr"] = sm
    assert N["sub"]["CIRC"]["p_combined_smaller"] <= 0.001 and N["sub"]["CIRC"]["var_log_SMR_combined"] < N["sub"]["CIRC"]["var_combined_random_median"]
    assert N["sub"]["CANM"]["var_log_SMR_combined"] > N["sub"]["CANM"]["var_log_SMR_cause"]
    # 공간
    s6m = rd("S6_moran_year.csv"); N["moran_year"] = (s6m.moran_I.min(), s6m.moran_I.max())
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"], N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "moran_I"], r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); N["s6"] = s6; N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    o = pd.read_csv(os.path.join(os.path.dirname(B), "NIHD", "results_std3", "S6_spatial_RR.csv")); m = s6.merge(o[["fbd_region", "RR", "class"]], on="fbd_region", suffixes=("", "_o")); assert len(m) == 229
    N["nihd_rho"] = float(m.RR.corr(m.RR_o, method="spearman")); N["nihd_hot_in_cold"] = int(((m["class"] == "coldspot") & (m.class_o == "hotspot")).sum()); N["nihd_hot"] = int((m.class_o == "hotspot").sum())
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict(); vp = rd("S42_variance_partition.csv").set_index("component"); N["vp_spatial"] = vp.loc["spatial_structured", "share_of_linear_predictor_var"]
    # 주모형·다중우주
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role"]].to_dict("index")
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); assert N["n_hyp"] == 13 and set(m3.index[m3.role == "hypothesis"]) == set(HYP)
    N["cred_hyp"] = sorted(v for v in HYP if N["main"][v]["cred"]); assert set(N["cred_hyp"]) == set(ROB)
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index"); assert set(s7.index[s7.robust]) == set(ROB)
    hb = open(os.path.join(B, "HM_best_ILLD_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0]); N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    lk = rd("S1_likelihood.csv"); lk = lk[lk.set == "REF_forced_only"].set_index("family").WAIC; N["waic_pois"], N["waic_nb"] = lk["poisson"], lk["nbinomial"]; assert N["waic_nb"] < N["waic_pois"]
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = {v: (r.IRR, r.lo, r.hi, bool(r.cred)) for v, r in nc.iterrows()}
    wi = rd("S4_window_IRR.csv"); N["win"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in wi.itertuples()}
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    ret = rd("S41_retention_by_cov.csv") if os.path.exists(os.path.join(RS, "S41_retention_by_cov.csv")) else None
    ALT = sorted({a for a in S41.analysis.unique() if not a.startswith(("F1_", "F2_", "G2_", "H1_", "bw_"))}); N["alt"] = ALT
    N["ret"] = {}
    for v in ROB:
        sg = N["main"][v]["IRR"] > 1; rr = [N["s41"][(a, v)] for a in ALT if (a, v) in N["s41"]]; N["ret"][v] = (sum(1 for t in rr if t[3] and (t[0] > 1) == sg), len(rr))
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis.str.startswith("H1_nco_")].itertuples()}
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r.set, r.cov): (r.n, r.n_cred_same_sign) for r in lo.itertuples() if not str(r.cov).startswith("__")}
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index")
    N["sens"] = {}
    for v in ("s577", "s2", "s8", "sa"):
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    ac = rd("S50_access_sensitivity.csv").set_index("cov"); N["outside"] = tuple(ac.loc["outside_care_share", ["IRR", "lo", "hi", "cred"]])
    cv = rd("S5_covid.csv"); N["covid_main"] = tuple(cv[cv.term == "post_main"][["IRR", "lo", "hi", "cred"]].iloc[0])
    eb = rd("S12c_yearly_EB_SIR.csv"); g = eb.groupby("year").ebSIR; gap = pd.DataFrame({"p10": g.quantile(.1), "p90": g.quantile(.9)}); gap["ratio"] = gap.p90 / gap.p10; N["gap"] = gap.to_dict("index")
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame, tuple))})
    for k in ("phi", "moran_year", "covid_main", "outside"): print(k, N[k])
    print("share", {k: round(v, 2) for k, v in N["share"].items()}); print("hot", N["hot_by_sido"]); print("cold", N["cold_by_sido"]); print("ret", N["ret"], len(N["alt"]))
    print("KH", {k: v for k, v in N["s43_waic"].items() if k.startswith("KH")}, N["waic_main"]); print("gap", {y: round(N["gap"][y]["ratio"], 2) for y in (2011, 2024)})
    print("nihd", N["nihd_rho"], N["nihd_hot_in_cold"], N["nihd_hot"]); print("asr", N["asr"]); print("evalue", N["evalue"])
