#!/usr/bin/env python3
# 99S2 — ILLD 전국 성×연령 불명확 사인(R00-R99) 비율, 2011·2017·2024 (SAGER, 2026-11-12). 원자료 DT_1B34E01(전국 사인×성×연령).
import os, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "04_분석", "ILLD", "results_sex")
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
N = N[(N.item == "사망자수") & N.year.between(2011, 2024) & N.sex.isin(["남자", "여자", "계"])]
AG = {"0세": "<45", "1 - 4세": "<45", "5 - 9세": "<45", "10 - 14세": "<45", "15 - 19세": "<45", "20 - 24세": "<45", "25 - 29세": "<45", "30 - 34세": "<45", "35 - 39세": "<45", "40 - 44세": "<45",
      "45 - 49세": "45-64", "50 - 54세": "45-64", "55 - 59세": "45-64", "60 - 64세": "45-64", "65 - 69세": "65-74", "70 - 74세": "65-74", "75 - 79세": "75-84", "80 - 84세": "75-84", "85 - 89세": "85+", "90세이상": "85+"}
N["ag"] = N.age.map(AG); I = "달리 분류되지 않은 증상 징후 (R00-R99)"
A = N[N.ag.notna() & N.cause.isin(["계", I])].groupby(["year", "sex", "ag", "cause"]).value.sum().unstack()
A["share"] = 100 * A[I] / A["계"]; A = A.reset_index().rename(columns={I: "illd", "계": "all"})
T = N[(N.age == "계") & N.cause.isin(["계", I])].groupby(["year", "sex", "cause"]).value.sum().unstack(); T["share"] = 100 * T[I] / T["계"]
T = T.reset_index().rename(columns={I: "illd", "계": "all"}).assign(ag="all")
R = pd.concat([A, T]); R.to_csv(os.path.join(OUT, "national_share_by_sex_age.csv"), index=False, encoding="utf-8-sig")
print(R[R.year.isin([2011, 2024])].pivot_table(index=["sex", "ag"], columns="year", values="share").round(2).to_string())
