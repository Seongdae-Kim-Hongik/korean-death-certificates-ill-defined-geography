#!/usr/bin/env python3
# 99R_illd_substitution — ILLD 사전지정 대체 분석 A1–A4(sets_ILLD_std3.json secondary_substitution, 2026-11-12). 99R_alld_decomp의 그래프·Moran 규칙 복제, 공유 원본 무수정.
#  관측: 기준 SQLite region_year mort__*_deaths(읽기 전용) + R00-R99(EXT_canonical_pool_ILLD). 기대: 연령 18구간 E(ILLD_Estd2 E_std2, CIRC_Estd E_std, <사인>_Estd2 E_std2), 연도별 ΣE=ΣO 재척도.
#  A1 14년 SMR Spearman·비중 Spearman / A2 창별 ΔlogSMR(W1→W3) 상관·지역 내 연도 편차 상관 / A3 결합 SMR 분산(무작위 짝짓기 999회 대비) / A4 비교 사인 같은 계산
#  산출: 04_분석/ILLD/results_sub/SUB_*.csv
import os, sqlite3, unicodedata, numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널"); OUT = os.path.join(AN, "ILLD", "results_sub")
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
CA = {"CIRC": "순환계통질환", "IHD": "허혈성심장질환", "STRK": "뇌혈관질환", "CANM": "악성신생물", "PNEU": "폐렴", "ALZ": "알츠하이머"}
Q = pd.read_sql("select year, fbd_region, " + ", ".join(f'"mort__{v}_deaths" as {k}' for k, v in CA.items()) + ', "mort__전체사망_deaths" as ALL_ from region_year where year between 2011 and 2024', c); c.close()
Q["fbd_region"] = Q.fbd_region.map(NFC)
X = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_ILLD_261112.csv"), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
M = Q.merge(X[["year", "fbd_region", "illd_deaths", "circ_deaths", "all_deaths"]], on=["year", "fbd_region"], validate="one_to_one"); assert len(M) == 3206
assert (M.CIRC == M.circ_deaths).all() and (M.ALL_ == M.all_deaths).all(), "SQLite 순환계·전체 ≠ 원표"
M = M.rename(columns={"illd_deaths": "ILLD"}).drop(columns=["circ_deaths", "all_deaths"])
EF = {"ILLD": ("ILLD_Estd2.csv", "E_std2"), "CIRC": ("CIRC_Estd.csv", "E_std"), **{k: (f"{k}_Estd2.csv", "E_std2") for k in ("IHD", "STRK", "CANM", "PNEU", "ALZ")}}
for k, (f, col) in EF.items():
    e = pd.read_csv(os.path.join(PAN, f), encoding="utf-8-sig")[["year", "fbd_region", col]].rename(columns={col: k + "_E"}); e["fbd_region"] = e.fbd_region.map(NFC)
    M = M.merge(e, on=["year", "fbd_region"], validate="one_to_one")
    M[k + "_E"] = M[k + "_E"] * M.groupby("year")[k].transform("sum") / M.groupby("year")[k + "_E"].transform("sum")
CAUS = list(EF)
s98 = open(os.path.join(HERE, "98_screen_std.py"), encoding="utf-8").read(); s98 = s98[:s98.index("SCR = pd.read_csv")]
g98 = {"__file__": os.path.join(HERE, "98_screen_std.py")}; exec(compile(s98, "98head", "exec"), g98)
nb = g98["read_graph"](os.path.join(AN, "ILLD", "graph_593.graph"))
ar = pd.read_csv(os.path.join(AN, "ILLD", "results_screen", "forced_std_RR.csv"))[["area", "fbd_region"]]; ar["fbd_region"] = ar.fbd_region.map(NFC)
REG = ar.sort_values("area").fbd_region.tolist(); IDX = {a: i for i, a in enumerate(ar.sort_values("area").area)}
W = np.zeros((229, 229))
for a, i in IDX.items():
    nbs = [IDX[b] for b in nb.get(a, []) if b in IDX]; W[i, nbs] = 1 / len(nbs)
assert int((W > 0).sum() / 2) == 593
def moran(y): z = y - y.mean(); return float(len(z) * (z @ W @ z) / (z @ z) / W.sum())
def agg(lo, hi): return M[M.year.between(lo, hi)].groupby("fbd_region").sum(numeric_only=True).reindex(REG)
A = agg(2011, 2024); rng = np.random.default_rng(20261112)
rows = []
for k in CAUS[1:]:
    si, sk = A.ILLD / A.ILLD_E, A[k] / A[k + "_E"]
    shi, shk = A.ILLD / A.ALL_, A[k] / A.ALL_
    comb = (A.ILLD + A[k]) / (A.ILLD_E + A[k + "_E"]); lk, lc = np.log(sk), np.log(comb)
    # 무작위 짝짓기: ILLD를 시군구 사이에서 섞었을 때 결합 log SMR 분산 분포
    sims = np.array([np.log((A.ILLD.values[p] / A.ILLD_E.values[p] * A.ILLD_E.values + A[k].values) / (A.ILLD_E.values + A[k + "_E"].values)).var() for p in (rng.permutation(229) for _ in range(999))])
    rows.append(dict(cause=k, rho_SMR=spearmanr(si, sk)[0], p_SMR=spearmanr(si, sk)[1], rho_share=spearmanr(shi, shk)[0], p_share=spearmanr(shi, shk)[1],
                     var_log_SMR_cause=lk.var(), var_log_SMR_combined=lc.var(), var_combined_random_median=float(np.median(sims)), p_combined_smaller=(1 + (sims <= lc.var()).sum()) / 1000,
                     P90P10_cause=sk.quantile(.9) / sk.quantile(.1), P90P10_combined=comb.quantile(.9) / comb.quantile(.1), moran_cause=moran(lk.values), moran_combined=moran(lc.values),
                     illd_deaths_14y=int(A.ILLD.sum()), cause_deaths_14y=int(A[k].sum())))
A1 = pd.DataFrame(rows).round(4); A1.to_csv(os.path.join(OUT, "SUB_A1_A3_A4_district.csv"), index=False, encoding="utf-8-sig"); print(A1.to_string())
# A2 창별 변화·지역 내 연도 편차
W1, W3 = agg(2011, 2015), agg(2020, 2024); r2 = []
L = M.copy()
for k in CAUS: L["l" + k] = np.log((L[k] + 0.5) / (L[k + "_E"] + 0.5))
for k in CAUS[1:]:
    d_i = np.log((W3.ILLD / W3.ILLD_E) / (W1.ILLD / W1.ILLD_E)); d_k = np.log((W3[k] / W3[k + "_E"]) / (W1[k] / W1[k + "_E"]))
    wi = L.groupby("fbd_region")[["lILLD", "l" + k]].transform(lambda s: s - s.mean()); wi = wi - wi.groupby(L.year).transform("mean")
    wt = L[k + "_E"] + L.ILLD_E
    r2.append(dict(cause=k, rho_dlogSMR_W1W3=spearmanr(d_i, d_k)[0], p_dlog=spearmanr(d_i, d_k)[1], r_within_year_dev=pearsonr(wi.lILLD, wi["l" + k])[0],
                   r_within_weighted=float(np.cov(wi.lILLD, wi["l" + k], aweights=wt)[0, 1] / np.sqrt(np.cov(wi.lILLD, wi.lILLD, aweights=wt)[0, 1] * np.cov(wi["l" + k], wi["l" + k], aweights=wt)[0, 1]))))
A2 = pd.DataFrame(r2).round(4); A2.to_csv(os.path.join(OUT, "SUB_A2_change_within.csv"), index=False, encoding="utf-8-sig"); print(A2.to_string())
# 전국: 연도별 비중
N = M.groupby("year")[CAUS + ["ALL_"]].sum(); NS = (N[CAUS].div(N.ALL_, axis=0) * 100).round(2); NS.to_csv(os.path.join(OUT, "SUB_national_share.csv"), encoding="utf-8-sig"); print(NS[["ILLD", "CIRC", "CANM", "PNEU"]].to_string())
D = pd.DataFrame({"fbd_region": REG, "SMR_ILLD": (A.ILLD / A.ILLD_E).values, "SMR_CIRC": (A.CIRC / A.CIRC_E).values, "share_ILLD": (A.ILLD / A.ALL_ * 100).values, "share_CIRC": (A.CIRC / A.ALL_ * 100).values,
                  "SMR_combined_ILLD_CIRC": ((A.ILLD + A.CIRC) / (A.ILLD_E + A.CIRC_E)).values})
D.to_csv(os.path.join(OUT, "SUB_district_SMR.csv"), index=False, encoding="utf-8-sig")
