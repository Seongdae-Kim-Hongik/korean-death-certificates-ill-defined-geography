#!/usr/bin/env python3
# 99R_next5b — 다음 타깃 5개(38호~) 2차 선별용 E (2026-11-12; 99Q_build_E_next5.py 복제·대상만 교체, 원본 수정 없음).
#  대상(장부 미사용 행만): 검진 1차 판정 OTHS 질환의심_기타질환·SUSP 질환의심_실인원·DXT 유질환자_실인원·TBT 유질환자_폐결핵(N104/N106 전국 성×16연령 율, 분모 N098),
#        대사 위험요인 WAIST 복부비만·HBP 높은혈압·HGLU 높은혈당·HTG 고중성지방·LHDL 낮은HDL·MSPRE 주의군(1~2개)(N139/N136 전국 성×16연령 율, 분모 N138/N135 수검자수), 2013-2024.
#  분자 = 기준 SQLite region_year(읽기 전용), 빈칸만 원표 시군구 행(50 매핑 규칙, 코드 결합)으로 채우고 겹치는 칸은 대조. 세종 제외(99U2 규칙). 인구 = ST_FBDZIP(창원 2023 정정본).
#  산출: 02_패널/<TAG>_Estd3r.csv (year, fbd_region, offset, cases, E_std, E_crude), 04_분석/00_다음타깃b_분자채움_261112.csv
import os, sys, sqlite3, importlib.util, unicodedata
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널")
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py"); m50 = _load("m50", "50_build_master_panel.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
assert os.environ.get("ST_FBDZIP"), "ST_FBDZIP(창원 2023 교정 인구 폴더)를 지정"
YEARS = list(range(2011, 2025)); SEXES = ["남자", "여자"]
SCR = {"OTHS": ("chk__질환의심_기타질환", "N104", "기타질환", YEARS), "SUSP": ("chk__질환의심_실인원", "N104", "실인원", YEARS),
       "DXT": ("chk__유질환자_실인원", "N106", "실인원", YEARS), "TBT": ("chk__유질환자_폐결핵", "N106", "폐결핵", YEARS)}
MY = list(range(2013, 2025))
META = {"WAIST": ("chk__대사_복부비만_인원", "N139", "복부비만", "DT_35007_N138", "복부비만"), "HBP": ("chk__대사_높은혈압_인원", "N139", "높은혈압", "DT_35007_N138", "높은혈압"),
        "HGLU": ("chk__대사_높은혈당_인원", "N139", "높은혈당", "DT_35007_N138", "높은혈당"), "HTG": ("chk__대사_고중성지방_인원", "N139", "고중성지방혈증", "DT_35007_N138", "고중성지방혈증"),
        "LHDL": ("chk__대사_낮은HDL_인원", "N139", "낮은 HDL 콜레스테롤 혈증", "DT_35007_N138", "낮은HDL콜레스테롤혈증"), "MSPRE": ("chk__대사_주의군_인원", "N136", "주의군(1~2개)", "DT_35007_N135", "주의군(1~2개)")}
HI, CB, HT, IH = "허혈성 심장 질환 (I20-I25)", "뇌혈관 질환 (I60-I69)", "고혈압성 질환 (I10-I13)", "기타 심장 질환 (I26-I51)"
MORT = {}
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cols = sorted({v[0] for v in SCR.values()} | {v[0] for v in META.values()})
RY = pd.read_sql("select year, fbd_region, " + ", ".join(f'"{c}"' for c in cols) + " from region_year where year between 2011 and 2024", con); RY["fbd_region"] = RY.fbd_region.map(NFC)
base = pd.read_sql("select year, key, fbd_region from disease_panel where tag='PERIO'", con); base["fbd_region"] = base.fbd_region.map(NFC); base["key"] = base.key.map(NFC)
PKEYS = set(base.key); assert len(base) == 3206
# ── 시군구 성×연령 인구(99U2 규칙) ──
BANDS16 = ["0-19"] + [f"{lo}-{lo+4}" for lo in range(20, 85, 5)] + ["85+"]; BANDS18 = [f"{lo}-{lo+4}" for lo in range(0, 85, 5)] + ["85+"]
SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 85, 5)]; OLD85 = ["85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}; rows = []
for y in YEARS:
    d = pd.read_csv(os.path.join(m38.FBDZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip()
    for s in SEXES: d[s] = pd.to_numeric(d[s].str.replace(",", ""), errors="coerce")
    sido = None; city = None; blocks = (d["행정구역별"] != d["행정구역별"].shift()).cumsum()
    for _, g in d.groupby(blocks, sort=False):
        nm = g["행정구역별"].iat[0]
        if nm == "전국": continue
        if nm in SIDO_HDR:
            sido = nm; city = None
            if nm != "세종특별자치시": continue
            g = g.drop_duplicates("연령별")
        sg = nm.split("-")[-1]
        if sg.endswith("시"): city = sg
        elif sg.endswith("구") and city is not None and cw.sido_std(sido) not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): continue
        else: city = None
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        for s in SEXES:
            a = g.set_index("연령별")[s]
            if pd.isna(a.get("계", np.nan)): continue
            f = a.reindex(FIVE); o = a.reindex(OLD85).fillna(0); assert f.notna().all(), (y, nm, s)
            r = {"year": y, "sex": s, "key": NFC(key), **{b: f[b + "세"] for b in BANDS18[:-1]}, "85+": o.sum()}
            r["0-19"] = f["0-4세"] + f["5-9세"] + f["10-14세"] + f["15-19세"]; r["s0-19_adult"] = f["15-19세"]; rows.append(r)
POP = pd.DataFrame(rows).groupby(["year", "key", "sex"], as_index=False).sum(numeric_only=True)
cwn = POP[(POP.key == NFC(base[base.fbd_region == NFC("경상남도창원시")].key.iat[0])) & (POP.year == 2023)][BANDS18].sum().sum()
print(f"[99R5b] 창원 2023 인구 {cwn:,.0f} (정답 1,009,038)")
out = {}
# ── 사망 ──
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
N = N[N.sex.isin(SEXES) & (N.item == "사망자수") & N.year.between(2011, 2024)]
def nat_band(a):
    a = a.replace(" ", "")
    if a in ("0세", "1-4세"): return "0-4"
    if a in ("85-89세", "90세이상"): return "85+"
    if a.endswith("세") and "-" in a:
        lo, hi = a[:-1].split("-")
        if int(hi) - int(lo) == 4 and int(lo) <= 80: return f"{lo}-{hi}"
    return None
N["band"] = N.age.map(nat_band)
NATPOP18 = POP.groupby(["year", "sex"])[BANDS18].sum()
for T, (cl, plus, minus) in MORT.items():
    Z = N[N.band.notna()].groupby(["cause", "year", "sex", "band"]).value.sum()
    x = sum(Z.loc[c].unstack()[BANDS18] for c in plus) - (sum(Z.loc[c].unstack()[BANDS18] for c in minus) if minus else 0)
    rate = x / NATPOP18
    RY["_c"] = sum((-1 if c.startswith("-") else 1) * RY[c.lstrip("-")] for c in cl)
    P = base.merge(RY[["year", "fbd_region", "_c"]], on=["year", "fbd_region"], how="left", validate="one_to_one").rename(columns={"_c": "cases"}); assert P.cases.notna().all() and (P.cases >= 0).all(), T
    E = np.zeros(len(P)); off = np.zeros(len(P))
    for s in SEXES:
        X = P[["year", "key"]].merge(POP[POP.sex == s], on=["year", "key"], how="left", validate="one_to_one"); assert X[BANDS18].notna().all().all()
        E += (X[BANDS18].values * rate.xs(s, level="sex").loc[X.year.values].values).sum(1); off += X[BANDS18].values.sum(1)
    P["offset"] = off; P["E_std"] = E * P.year.map(P.groupby("year").cases.sum()) / pd.Series(E).groupby(P.year.values).transform("sum").values
    P["E_crude"] = P.offset * P.year.map(P.groupby("year").cases.sum() / P.groupby("year").offset.sum())
    NT = N[N.age == "계"].groupby(["cause", "year"]).value.sum()
    nat = sum(NT.loc[c] for c in plus) - (sum(NT.loc[c] for c in minus) if minus else 0)
    print(f"[99R5b] {T}: 시군구 합/전국 사망 {(P.groupby('year').cases.sum()/nat).round(3).min()}~{(P.groupby('year').cases.sum()/nat).round(3).max()}, 합 {int(P.cases.sum()):,}, 0칸 {(P.cases==0).sum()}")
    out[T] = P
# ── 검진 ──
A = pd.read_csv(os.path.join(SRC, "DT_35007_N099_national_long.csv"), encoding="utf-8-sig"); A = A[(A.grp == "계") & A.year.isin(YEARS)]
def nb_band(a):
    a = str(a).replace(" ", "")
    if a == "19세이하": return "0-19"
    if a == "85세이상": return "85+"
    if a.endswith("세") and "~" in a: lo, hi = a[:-1].split("~"); return f"{lo}-{hi}"
    return None
A["band"] = A.age.map(nb_band); EX = A[A.band.notna() & A.sex.isin(SEXES)].set_index(["year", "sex", "band"]).value.unstack()[BANDS16]
NATPOP16 = POP.groupby(["year", "sex"])[BANDS16].sum(); UPT = EX / NATPOP16
L = pd.read_csv(os.path.join(PAN, "NHIS검진_시군구_연도_long.csv"), usecols=["year", "sido", "sigungu", "level", "sex", "category", "value", "tbl_id"], engine="pyarrow")
L = L[(L.tbl_id == "DT_35007_N098") & (L.level == "시군구") & L.year.isin(YEARS) & L.sex.isin(SEXES) & (L.category == "계")].copy()
pairs = L[["sido", "sigungu"]].drop_duplicates(); mp = {(a, b): m50.map_region(a, b, PKEYS) for a, b in zip(pairs.sido, pairs.sigungu)}
L["key"] = [mp[(a, b)]["key"] for a, b in zip(L.sido, L.sigungu)]; L["role"] = [mp[(a, b)]["role"] for a, b in zip(L.sido, L.sigungu)]
L = L[L.key.notna()]; L["key"] = L.key.map(NFC); hasprim = L[L.role == "primary"].groupby(["key", "year"]).size().index
L = L[~((L.role == "sub") & L.set_index(["key", "year"]).index.isin(hasprim))]
SX = L.pivot_table(index=["year", "key"], columns="sex", values="value", aggfunc="sum")
# SQLite 분자 빈칸(일반구 시 일부 연도) → 원표 N103/N105 시군구 행을 같은 50 매핑 규칙으로 합산해 채우고, 겹치는 칸은 SQLite와 대조
SRCCAT = {"OTHS": ("DT_35007_N103", "일반_기타질환"), "SUSP": ("DT_35007_N103", "일반_실인원"), "DXT": ("DT_35007_N105", "실인원"), "TBT": ("DT_35007_N105", "폐결핵"), "HTNT": ("DT_35007_N105", "고혈압"), "DMT": ("DT_35007_N105", "당뇨"), "_KIDS": ("DT_35007_N103", "일반_신장질환"), "ANEM": ("DT_35007_N103", "일반_빈혈증"), "LIVS": ("DT_35007_N103", "일반_간장질환"), "TBS": ("DT_35007_N103", "일반_폐결핵"),
          "LIPSA": ("DT_35007_N103", "일반_이상지질혈증"), "LIPSB": ("DT_35007_N103", "일반_이상지질혈증"), "CHES": ("DT_35007_N103", "일반_기타흉부질환"), "LIPT": ("DT_35007_N105", "이상지질혈증")}
L2 = pd.read_csv(os.path.join(PAN, "NHIS검진_시군구_연도_long.csv"), usecols=["year", "sido", "sigungu", "level", "sex", "category", "value", "tbl_id"], engine="pyarrow")
L2 = L2[L2.tbl_id.isin(["DT_35007_N103", "DT_35007_N105"]) & (L2.level == "시군구") & L2.year.isin(YEARS) & L2.sex.isin(SEXES)].copy()
pr2 = L2[["sido", "sigungu"]].drop_duplicates(); mp2 = {(a, b): m50.map_region(a, b, PKEYS) for a, b in zip(pr2.sido, pr2.sigungu)}
L2["key"] = [mp2[(a, b)]["key"] for a, b in zip(L2.sido, L2.sigungu)]; L2["role"] = [mp2[(a, b)]["role"] for a, b in zip(L2.sido, L2.sigungu)]
L2 = L2[L2.key.notna()]; L2["key"] = L2.key.map(NFC); hp2 = L2[L2.role == "primary"].groupby(["key", "year", "tbl_id", "category"]).size().index
L2 = L2[~((L2.role == "sub") & L2.set_index(["key", "year", "tbl_id", "category"]).index.isin(hp2))]
SRCV = L2.groupby(["tbl_id", "category", "year", "key"]).value.sum(min_count=1)
FILLLOG = []
for T, (col, tb, grp, yrs) in SCR.items():
    B = pd.read_csv(os.path.join(SRC, f"DT_35007_{tb}_national_long.csv"), encoding="utf-8-sig", dtype={"grp_code": str}); B = B[(B.grp == grp) & B.year.isin(yrs) & ~B.grp_code.eq("00401")]  # N104 실인원 = 일반 질환의심(00301), 고혈압·당뇨 질환의심 실인원(00401) 제외
    B["band"] = B.age.map(nb_band); NUM = B[B.band.notna() & B.sex.isin(SEXES)].set_index(["year", "sex", "band"]).value.unstack()[BANDS16].fillna(0)
    RATE = NUM / EX.loc[NUM.index]
    P = base[base.year.isin(yrs)].reset_index(drop=True)
    P = P.merge(RY[["year", "fbd_region", col]], on=["year", "fbd_region"], how="left", validate="one_to_one").rename(columns={col: "cases"})
    sv = SRCV.loc[SRCCAT[T]].reindex(pd.MultiIndex.from_arrays([P.year, P.key])).values if True else None
    both = P.cases.notna().values & ~np.isnan(sv); dif = np.abs(P.cases.values[both] - sv[both])
    fill = P.cases.isna().values & ~np.isnan(sv)
    FILLLOG.append(dict(TAG=T, 겹침칸=int(both.sum()), 일치칸=int((dif <= 2).sum()), 최대차=float(dif.max()) if both.any() else 0, 채운칸=int(fill.sum()),
                        채운곳="; ".join(f"{a}{b}" for a, b in P.loc[fill, ["fbd_region", "year"]].values.tolist())))
    P.loc[fill, "cases"] = sv[fill]
    S = SX.reindex(P.set_index(["year", "key"]).index)
    ok = P.cases.notna().values & S.notna().all(1).values & (S.min(1) > 0).values & ~P.fbd_region.eq(NFC("세종시세종시")).values
    drop = P[~ok][["year", "fbd_region"]].values.tolist(); P = P[ok].reset_index(drop=True); S = S[ok]
    P["offset"] = S.sum(1).values; E = np.zeros(len(P))
    for s in SEXES:
        X = P[["year", "key"]].merge(POP[POP.sex == s], on=["year", "key"], how="left", validate="one_to_one")
        raw = X[BANDS16].values * UPT.xs(s, level="sex").loc[X.year.values].values; exam = raw * (S[s].values / raw.sum(1))[:, None]
        E += (exam * RATE.xs(s, level="sex").loc[X.year.values].values).sum(1)
    P["E_std"] = E * P.year.map(P.groupby("year").cases.sum()) / pd.Series(E).groupby(P.year.values).transform("sum").values
    P["E_crude"] = P.offset * P.year.map(P.groupby("year").cases.sum() / P.groupby("year").offset.sum())
    natc = NUM.groupby(level="year").sum().sum(1)
    print(f"[99R5b] {T}: 행 {len(P)}, 시군구 {P.fbd_region.nunique()}, {min(yrs)}-{max(yrs)}, 제외 {len(drop)}칸 {sorted({d[1] for d in drop})[:5]}, 합 {int(P.cases.sum()):,}, 시군구 합/전국 {(P.groupby('year').cases.sum()/natc).round(3).min()}~{(P.groupby('year').cases.sum()/natc).round(3).max()}, 0칸 {(P.cases==0).sum()}")
    out[T] = P
# ── 대사 위험요인(N135/N138 시군구 성별, N136/N139 전국 성×16연령) ──
L3 = pd.read_csv(os.path.join(PAN, "NHIS검진_시군구_연도_long.csv"), usecols=["year", "sido", "sigungu", "level", "sex", "category", "measure", "value", "tbl_id"], engine="pyarrow")
L3 = L3[L3.tbl_id.isin(["DT_35007_N135", "DT_35007_N138"]) & (L3.level == "시군구") & L3.year.isin(MY) & L3.sex.isin(SEXES) & (L3.measure == "인원")].copy()
pr3 = L3[["sido", "sigungu"]].drop_duplicates(); mp3 = {(a, b): m50.map_region(a, b, PKEYS) for a, b in zip(pr3.sido, pr3.sigungu)}
L3["key"] = [mp3[(a, b)]["key"] for a, b in zip(L3.sido, L3.sigungu)]; L3["role"] = [mp3[(a, b)]["role"] for a, b in zip(L3.sido, L3.sigungu)]
L3 = L3[L3.key.notna()]; L3["key"] = L3.key.map(NFC); hp3 = L3[L3.role == "primary"].groupby(["key", "year", "tbl_id", "category"]).size().index
L3 = L3[~((L3.role == "sub") & L3.set_index(["key", "year", "tbl_id", "category"]).index.isin(hp3))]
SRC3 = L3.groupby(["tbl_id", "category", "year", "key"]).value.sum(min_count=1)
SX3 = L3[L3.category == "수검자수"].pivot_table(index=["tbl_id", "year", "key"], columns="sex", values="value", aggfunc="sum")
NB_ = {}
for tb in ["N136", "N139"]:
    B = pd.read_csv(os.path.join(SRC, f"DT_35007_{tb}_national_long.csv"), encoding="utf-8-sig", dtype={"grp_code": str}); B = B[(B.item == "인원") & B.year.isin(MY) & B.sex.isin(SEXES)].copy()
    B["band"] = B.age.map(nb_band); NB_[tb] = B[B.band.notna()]
for T, (col, tb, grp, stb, scat) in META.items():
    B = NB_[tb]; EXm = B[B.grp == "수검자수"].set_index(["year", "sex", "band"]).value.unstack()[BANDS16]
    NUM = B[B.grp == grp].set_index(["year", "sex", "band"]).value.unstack()[BANDS16].fillna(0); RATE = NUM / EXm.loc[NUM.index]; UPm = EXm / NATPOP16.loc[EXm.index]
    P = base[base.year.isin(MY)].reset_index(drop=True)
    P = P.merge(RY[["year", "fbd_region", col]], on=["year", "fbd_region"], how="left", validate="one_to_one").rename(columns={col: "cases"})
    sv = SRC3.loc[(stb, scat)].reindex(pd.MultiIndex.from_arrays([P.year, P.key])).values
    both = P.cases.notna().values & ~np.isnan(sv); dif = np.abs(P.cases.values[both] - sv[both]); fill = P.cases.isna().values & ~np.isnan(sv)
    FILLLOG.append(dict(TAG=T, 겹침칸=int(both.sum()), 일치칸=int((dif <= 2).sum()), 최대차=float(dif.max()) if both.any() else 0, 채운칸=int(fill.sum()),
                        채운곳="; ".join(f"{a}{b}" for a, b in P.loc[fill, ["fbd_region", "year"]].values.tolist())))
    P.loc[fill, "cases"] = sv[fill]
    S = SX3.loc[stb].reindex(pd.MultiIndex.from_arrays([P.year, P.key]))
    ok = P.cases.notna().values & S.notna().all(1).values & (S.min(1) > 0).values & ~P.fbd_region.eq(NFC("세종시세종시")).values
    drop = P[~ok][["year", "fbd_region"]].values.tolist(); P = P[ok].reset_index(drop=True); S = S[ok]
    P["offset"] = S.sum(1).values; E = np.zeros(len(P))
    for s_ in SEXES:
        X = P[["year", "key"]].merge(POP[POP.sex == s_], on=["year", "key"], how="left", validate="one_to_one")
        raw = X[BANDS16].values * UPm.xs(s_, level="sex").loc[X.year.values].values; exam = raw * (S[s_].values / raw.sum(1))[:, None]
        E += (exam * RATE.xs(s_, level="sex").loc[X.year.values].values).sum(1)
    P["E_std"] = E * P.year.map(P.groupby("year").cases.sum()) / pd.Series(E).groupby(P.year.values).transform("sum").values
    P["E_crude"] = P.offset * P.year.map(P.groupby("year").cases.sum() / P.groupby("year").offset.sum())
    natc = NUM.groupby(level="year").sum().sum(1)
    print(f"[99R5b] {T}: 행 {len(P)}, 시군구 {P.fbd_region.nunique()}, 제외 {len(drop)}칸, 합 {int(P.cases.sum()):,}, 시군구 합/전국 {(P.groupby('year').cases.sum()/natc).round(3).min()}~{(P.groupby('year').cases.sum()/natc).round(3).max()}, 0칸 {(P.cases==0).sum()}, E/O 상관 {np.corrcoef(P.E_std, P.cases)[0,1]:.3f}")
    out[T] = P
FL = pd.DataFrame(FILLLOG); print(FL.drop(columns="채운곳").to_string()); FL.to_csv(os.path.join(AN, "00_다음타깃b_분자채움_261112.csv"), index=False, encoding="utf-8-sig")
for T, P in out.items():
    P[["year", "fbd_region", "offset", "cases", "E_std", "E_crude"]].to_csv(os.path.join(PAN, f"{T}_Estd3r.csv"), index=False, encoding="utf-8-sig")
