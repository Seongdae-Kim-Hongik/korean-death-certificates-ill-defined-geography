#!/usr/bin/env python3
# 99S_illd_sex — ILLD 성별 분해(SAGER) (2026-11-12, 공유 스크립트 무수정).
#  인구 블록 = 99R_next5b_build_E.py 앞부분을 문자열로 읽어 실행(창원 2023 정정, ST_FBDZIP). 분자 = 원표 DT_1B34E13 정리본 성별(남/여) 코드 I(R00-R99)·9(I00-I99)·0(계), 50.load_source(코드 결합).
#  E = 성별 18연령(85+) 전국 율 × 시군구 성별 인구, 연도별 ΣE=ΣO 재척도. 산출: 04_분석/ILLD/results_sex/
import os, sys, sqlite3, importlib.util, unicodedata, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널"); OUT = os.path.join(ROOT, "04_분석", "ILLD", "results_sex")
src = open(os.path.join(HERE, "99R_next5b_build_E.py"), encoding="utf-8").read().split("out = {}")[0]
g = {"__file__": os.path.join(HERE, "99R_next5b_build_E.py"), "__name__": "pop"}; exec(compile(src, "pop", "exec"), g)
POP, base, BANDS18, NFC, m50 = g["POP"], g["base"], g["BANDS18"], g["NFC"], g["m50"]
SX = {"남": "남자", "여": "여자"}; CODES = {"0": "tot", "I": "illd", "9": "circ"}
L = pd.read_parquet(os.path.join(PAN, "사망원인_시군구_연도_사인_성_long.parquet"), columns=["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note", "cause_code", "sex", "deaths"],
                    filters=[("year", ">=", 2011), ("year", "<=", 2024), ("cause_code", "in", list(CODES))])
L = L[L.sex.isin(list(SX)) & L.cause_code.isin(list(CODES))]
IDX = ["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note"]
for c in IDX[1:]: L[c] = L[c].fillna("").astype(str)
mk = pd.read_csv(os.path.join(PAN, "시군구_마스터키.csv"), dtype=str); mk = mk[mk.fbd_sido.notna()].drop_duplicates("key")
parts = []
for s, s2 in SX.items():
    W = L[L.sex == s].assign(v=lambda d: d.cause_code.map(CODES) + "_" + s2).pivot_table(index=IDX, columns="v", values="deaths", aggfunc="sum").reset_index().replace({"": np.nan}).infer_objects(); W = W[W.level.notna()]
    tmpf = f"_tmp_illd_sex_{s}.csv"; W.to_csv(os.path.join(PAN, tmpf), index=False, encoding="utf-8-sig")
    log = dict(missing_files=[], level_filter={}, unmatched=[], special=[], overlap=[], sources={})
    srcd = dict(name="illdsex", prefix="", files=[tmpf], sido="sido", sgg="sigungu", merge_counts=True, level="시군구", ratio=lambda c: False, label="사망원인통계")
    agg, _ = m50.load_source(srcd, set(mk.key), log); os.remove(os.path.join(PAN, tmpf))
    agg["key"] = agg.key.map(NFC); agg["year"] = agg.year.astype(int); parts.append(agg.set_index(["year", "key"])[[c for c in agg.columns if c.endswith(s2)]])
C = base.merge(pd.concat(parts, axis=1).reset_index(), on=["year", "key"], how="left", validate="one_to_one")
VV = [c for c in C.columns if c.split("_")[0] in CODES.values()]; C[VV] = C[VV].fillna(0)
# 검산: 남+여 = 기준 SQLite 전체 사망, 남+여 ILLD = EXT 풀 illd_deaths
con = sqlite3.connect(f"file:{g['DB']}?mode=ro", uri=True)
R = pd.read_sql('select year, fbd_region, "mort__전체사망_deaths" as total from region_year where year between 2011 and 2024', con); R["fbd_region"] = R.fbd_region.map(NFC)
X = C.merge(R, on=["year", "fbd_region"], validate="one_to_one"); d = (X.tot_남자 + X.tot_여자 - X.total).abs()
print("[99S] 남+여 전체 − SQLite 전체: 불일치 칸", int((d > 0).sum()), "최대", d.max())
EX = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_ILLD_261112.csv")); EX["fbd_region"] = EX.fbd_region.map(NFC)
Y = C.merge(EX[["year", "fbd_region", "illd_deaths", "circ_deaths"]], on=["year", "fbd_region"], validate="one_to_one")
print("[99S] 남+여 ILLD − 풀: 불일치", int(((Y.illd_남자 + Y.illd_여자) != Y.illd_deaths).sum()), "· 순환계 불일치", int(((Y.circ_남자 + Y.circ_여자) != Y.circ_deaths).sum()))
src2 = open(os.path.join(HERE, "99R_next5b_build_E.py"), encoding="utf-8").read(); src2 = "def nat_band" + src2.split("def nat_band")[1].split("NATPOP18")[0]
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig"); N = N[N.sex.isin(["남자", "여자"]) & (N.item == "사망자수") & N.year.between(2011, 2024)]
g2 = {"N": N}; exec(compile(src2, "nb", "exec"), g2); N = g2["N"]; N = N[N.band.notna()]; NATPOP = POP.groupby(["year", "sex"])[BANDS18].sum()
CAUSE = {"illd": "달리 분류되지 않은 증상 징후 (R00-R99)", "circ": "순환계통 질환 (I00-I99)", "tot": None}
for k, cl in CAUSE.items():
    for s2 in SX.values():
        if cl is None: continue
        Z = N[(N.cause == cl) & (N.sex == s2)].groupby(["year", "band"]).value.sum().unstack()[BANDS18]
        rate = Z / NATPOP.xs(s2, level="sex")
        Xp = C[["year", "key"]].merge(POP[POP.sex == s2], on=["year", "key"], how="left", validate="one_to_one"); assert Xp[BANDS18].notna().all().all()
        E = (Xp[BANDS18].values * rate.loc[Xp.year.values].values).sum(1); O = C[f"{k}_{s2}"].values
        C[f"E_{k}_{s2}"] = E * pd.Series(O).groupby(C.year.values).transform("sum").values / pd.Series(E).groupby(C.year.values).transform("sum").values
C.to_csv(os.path.join(OUT, "ILLD_sex_counts_E.csv"), index=False, encoding="utf-8-sig")
# 성별 대체 분석(A1·A3 성별판): 14년 합 SMR
rng = np.random.default_rng(20261112); rows = []
for s2 in SX.values():
    A = C.groupby("fbd_region")[[f"illd_{s2}", f"circ_{s2}", f"E_illd_{s2}", f"E_circ_{s2}", f"tot_{s2}"]].sum()
    si, sc = A[f"illd_{s2}"] / A[f"E_illd_{s2}"], A[f"circ_{s2}"] / A[f"E_circ_{s2}"]
    sh_i, sh_c = A[f"illd_{s2}"] / A[f"tot_{s2}"], A[f"circ_{s2}"] / A[f"tot_{s2}"]
    comb = (A[f"illd_{s2}"] + A[f"circ_{s2}"]) / (A[f"E_illd_{s2}"] + A[f"E_circ_{s2}"])
    v_c, v_k = np.var(np.log(sc)), np.var(np.log(comb))
    rnd = [np.var(np.log((A[f"illd_{s2}"].values + A[f"circ_{s2}"].values[p]) / (A[f"E_illd_{s2}"].values + A[f"E_circ_{s2}"].values[p]))) for p in (rng.permutation(len(A)) for _ in range(999))]
    nat = C.groupby("year")[[f"illd_{s2}", f"tot_{s2}"]].sum(); nsh = nat[f"illd_{s2}"] / nat[f"tot_{s2}"]
    rows.append(dict(sex=s2, illd_deaths=int(A[f"illd_{s2}"].sum()), illd_share_2011=round(nsh.loc[2011] * 100, 2), illd_share_2024=round(nsh.loc[2024] * 100, 2),
                     rho_SMR=round(si.corr(sc, method="spearman"), 3), rho_share=round(sh_i.corr(sh_c, method="spearman"), 3),
                     var_logSMR_circ=round(v_c, 4), var_logSMR_combined=round(v_k, 4), var_random_median=round(float(np.median(rnd)), 4), p_combined_smaller=round((1 + sum(r <= v_k for r in rnd)) / 1000, 3),
                     SMR_illd_P90_P10=round(si.quantile(.9) / si.quantile(.1), 2)))
S = pd.DataFrame(rows); S.to_csv(os.path.join(OUT, "SUB_by_sex.csv"), index=False, encoding="utf-8-sig"); print(S.T.to_string())
B = C.groupby("fbd_region")[[f"illd_{s}" for s in SX.values()] + [f"E_illd_{s}" for s in SX.values()]].sum()
print("[99S] 남·여 ILLD SMR Spearman", round((B.illd_남자 / B.E_illd_남자).corr(B.illd_여자 / B.E_illd_여자, method="spearman"), 3))
