#!/usr/bin/env python3
# 39m_illd — 불명확 사인 사망(ILLD, R00-R99) E (2026-11-12). 공유 원본 39m_build_Estd_mort.py 불변: 원문을 읽어 사인 표에 ILLD 한 줄만 더해 실행.
#  (39m만) 선별 E 대조 파일은 02_패널/ILLD_Estd3r.csv(99R_next5b_mort_E 산출, E_std 열)로 바꿔 읽는다.
#  사용: ST_FBDZIP=<창원 교정 인구> [ST_E2_PANEL_SUF=_std3] python3 39m_illd.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "39m_build_Estd_mort.py"), encoding="utf-8").read()
a = 'TAG = sys.argv[1]; assert TAG in CAUSES, TAG; NC = CAUSES[TAG]'
assert src.count(a) == 1
src = src.replace(a, 'CAUSES["ILLD"] = "달리 분류되지 않은 증상 징후 (R00-R99)"\n' + a)
b = 'f"{TAG}_Estd.csv"'
if b in src: src = src.replace(b, 'f"{TAG}_Estd3r.csv"')
sys.argv = ["39m_build_Estd_mort.py", "ILLD"]
exec(compile(src, os.path.join(HERE, "39m_build_Estd_mort.py"), "exec"), {"__file__": os.path.join(HERE, "39m_build_Estd_mort.py"), "__name__": "__main__"})
