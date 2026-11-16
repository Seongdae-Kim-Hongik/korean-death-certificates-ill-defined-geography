#!/usr/bin/env python3
# 99c — 불명확 사인 사망(ILLD, R00-R99, 노쇠 R54 포함) 가설 풀·분자(2026-11-12). 새 수집 없음: 검증된 EXT 파일을 코드 결합(year, fbd_region)으로 모은다. 공유 원본 무수정.
#  ① EXT_canonical_pool_ALLD_261112(수급률 양쪽 규칙 33칸 정정판·고등교육·종합병원·응급의학·내과 전문의·미충족 의료·요양병원) 재사용 + 정정판 재확인 assert
#  ② 관외 외래 비율(EXT_canonical_pool_261106, 민감도 전용)
#  ③ 분자: 02_패널/next5b_mort_counts_261112.csv cI(원표 DT_1B34E13 코드 I = R00-R99, 계 = 기준 SQLite 전체 사망 3,206칸 일치) = CIRC_mort_extra 불명확_deaths 와 3,206칸 일치 assert
#     + 대체 분석용 순환계 I00-I99·전체 사망(CIRC_mort_extra_261112)
#  산출: 02_패널/EXT_canonical_pool_ILLD_261112.csv
import os, unicodedata, numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); PAN = os.path.join(os.path.dirname(HERE), "02_패널")
def rd(f, cols):
    d = pd.read_csv(os.path.join(PAN, f), encoding="utf-8-sig"); d["fbd_region"] = d.fbd_region.map(NFC); return d[["year", "fbd_region"] + cols]
out = rd("EXT_canonical_pool_ALLD_261112.csv", ["basic_livelihood_rate", "tertiary_educated_share", "genhosp_per100k", "em_specialists_per100k", "im_specialists_per100k", "unmet_need_rate", "ltc_hospitals_per100k_65"])
r = out.fbd_region.map(out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean())
assert not (out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * r) | (out.basic_livelihood_rate > 5 * r))).any(), "수급률 정정판 아님"
out = out.merge(rd("EXT_canonical_pool_261106.csv", ["outside_care_share"]), on=["year", "fbd_region"], how="left", validate="one_to_one")
N = rd("next5b_mort_counts_261112.csv", ["cI", "total_chk"]).rename(columns={"cI": "illd_deaths"})
C = rd("CIRC_mort_extra_261112.csv", ["불명확_deaths", "CIRC_deaths", "전체_deaths"])
NC = N.merge(C, on=["year", "fbd_region"], how="inner", validate="one_to_one"); assert len(NC) == 3206
assert (NC.illd_deaths == NC["불명확_deaths"]).all(), "R00-R99 두 추출 불일치"; assert (NC.total_chk == NC["전체_deaths"]).all()
out = out.merge(NC[["year", "fbd_region", "illd_deaths", "CIRC_deaths", "전체_deaths"]].rename(columns={"CIRC_deaths": "circ_deaths", "전체_deaths": "all_deaths"}), on=["year", "fbd_region"], how="left", validate="one_to_one")
out["illd_share"] = out.illd_deaths / out.all_deaths * 100; out["circ_share"] = out.circ_deaths / out.all_deaths * 100
assert len(out) == 3206 and out.fbd_region.nunique() == 229 and out.notna().all().all(), out.isna().sum()
print("[99c-illd] R00-R99 연도 합", out.groupby("year").illd_deaths.sum().astype(int).to_dict())
print("[99c-illd] 전국 불명확 비중(%)", (out.groupby("year").illd_deaths.sum() / out.groupby("year").all_deaths.sum() * 100).round(2).to_dict())
out.sort_values(["fbd_region", "year"]).to_csv(os.path.join(PAN, "EXT_canonical_pool_ILLD_261112.csv"), index=False, encoding="utf-8-sig")
print("[99c-illd] 저장", out.shape)
