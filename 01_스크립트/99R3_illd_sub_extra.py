#!/usr/bin/env python3
# 99R3 — ILLD 대체 분석 보강(2026-11-12, 교훈): (1) 코로나 전 창 쌍 W1(2011-15)→W2(2016-19) ΔlogSMR 상관 (2) 전국 직접 연령표준화율(2015 인구, 18구간) ILLD·순환계·합 2011/2019/2024.
#  입력·결합은 99R_illd_substitution.py 앞부분을 그대로 실행(공유 무수정). 산출: results_sub/SUB_A2b_precovid.csv, SUB_national_asr.csv
import os, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, "04_분석", "ILLD", "results_sub")
src = open(os.path.join(HERE, "99R_illd_substitution.py"), encoding="utf-8").read().split("CAUS = list(EF)")[0]
g = {"__file__": os.path.join(HERE, "99R_illd_substitution.py"), "__name__": "sub"}; exec(compile(src, "sub", "exec"), g); M = g["M"]
def win(a, b):
    q = M[M.year.between(a, b)].groupby("fbd_region").sum(numeric_only=True); return q
rows = []
for (a1, b1), (a2, b2), lab in (((2011, 2015), (2016, 2019), "W1_W2_precovid"), ((2011, 2015), (2020, 2024), "W1_W3")):
    A, B = win(a1, b1), win(a2, b2)
    for k in ("CIRC", "IHD", "STRK", "CANM"):
        di = np.log(B.ILLD / B.ILLD_E) - np.log(A.ILLD / A.ILLD_E); dc = np.log(B[k] / B[k + "_E"]) - np.log(A[k] / A[k + "_E"])
        r = spearmanr(di, dc); rows.append(dict(pair=lab, cause=k, rho=round(r.statistic, 3), p=r.pvalue))
D = pd.DataFrame(rows); D.to_csv(os.path.join(OUT, "SUB_A2b_precovid.csv"), index=False, encoding="utf-8-sig"); print(D.to_string())
# 전국 직접 표준화율
NN = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
NN = NN[(NN.item == "사망자수") & (NN.sex == "계") & NN.year.between(2011, 2024)]
def band(a):
    a = a.replace(" ", "")
    if a in ("0세", "1-4세"): return "0-4"
    if a in ("85-89세", "90세이상"): return "85+"
    if a.endswith("세") and "-" in a:
        lo, hi = a[:-1].split("-")
        if int(hi) - int(lo) == 4 and int(lo) <= 80: return f"{lo}-{hi}"
NN["band"] = NN.age.map(band); NN = NN[NN.band.notna()]
src2 = open(os.path.join(HERE, "99R_next5b_build_E.py"), encoding="utf-8").read().split("out = {}")[0]
g2 = {"__file__": os.path.join(HERE, "99R_next5b_build_E.py"), "__name__": "pop"}; exec(compile(src2, "pop", "exec"), g2)
POP = g2["POP"].groupby("year")[g2["BANDS18"]].sum(); w = POP.loc[2015] / POP.loc[2015].sum()
CAU = {"ILLD": ["달리 분류되지 않은 증상 징후 (R00-R99)"], "CIRC": ["순환계통 질환 (I00-I99)"]}
out = []
for y in (2011, 2015, 2019, 2024):
    r = {"year": y}
    for k, cl in CAU.items():
        d = NN[NN.cause.isin(cl) & (NN.year == y)].groupby("band").value.sum()[g2["BANDS18"]]; r[k] = float((1e5 * d / POP.loc[y] * w).sum())
    r["SUM"] = r["ILLD"] + r["CIRC"]; out.append(r)
A = pd.DataFrame(out).round(2); A.to_csv(os.path.join(OUT, "SUB_national_asr.csv"), index=False, encoding="utf-8-sig"); print(A.to_string())
