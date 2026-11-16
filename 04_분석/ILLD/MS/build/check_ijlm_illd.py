# check_ijlm_illd.py — ILLD International Journal of Legal Medicine 원고 검사기(2026-11-16). 가이드라인(IJLM 11/16 원문) > 플레이북(3선 표·네모·지문·인용 순서) > 문체·수치. FAIL 0이면 PASS.
#  sanitize_docx.py 뒤에 돌린다.
import os, re, subprocess, zipfile, sys
from docx import Document
from docx.oxml.ns import qn
from PIL import Image
import content_illd as C
from build_ijlm_illd import read_draft, TITLE, ORCID, KEYS, AI_STATEMENT, AFFIL, REPO, DECL, MSF
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out")
N = C.N; R = []
def ok(c, m): R.append(("ok  " if c else "FAIL") + " " + m)
W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount_ijlm.txt")).read().split())
D = read_draft(); AB = D["Abstract"]; ab = " ".join(AB)
SUPF, CLF = "ESM_1.docx", "Cover_Letter_IJLM.docx"
for f in (MSF, SUPF, CLF, "ESM_1.pdf", "Figures/Fig1.tif", "Figures/Fig2.tif", "Figures/Fig3.tif"): ok(os.path.exists(os.path.join(OUT, f)), f"파일 {f}")
# 1. IJLM 규정
aw = int(W["abstract_words"]); ok(150 <= aw <= 250, f"초록 {aw}단어, 150–250")
ok([p.split(":")[0] for p in AB] == ["Purpose", "Methods", "Results", "Conclusions"], "초록 Purpose/Methods/Results/Conclusions")
nk = len(C.KEYWORDS.split("; ")); ok(4 <= nk <= 6, f"키워드 {nk}개, 4–6")
ok(":" not in TITLE and "229" not in TITLE and "2011" not in TITLE and "tandardi" not in TITLE and "which specific causes are recorded less often there" not in TITLE.lower(), f"제목 {len(TITLE.split())}단어, 쌍점·시리즈 틀·이전 제목 없음")
ok(not re.search(r"\[@", ab) and not re.search(r"\[\d", ab), "초록 인용 없음")
old_ab = "Of 4,201,399 deaths, 427,264 (10.2%) were ill-defined; the share rose from 9.7% in 2011 to 11.7% in 2024 Spearman's ρ −0.53 P = 0.001 RR: 0.960; 95% credible interval, CrI: 0.942–0.979 229 districts, 2011–2024 13 district characteristics ICD-10 R00–R99"
nums = set(re.findall(r"\d[\d,.]*\d|\d", ab)); bad = sorted(n for n in nums if n not in old_ab)
ok(not bad, f"초록 수치 = 이전 원고 수치 {bad}")
d = Document(os.path.join(OUT, MSF)); _ps = [p.text.strip() for p in d.paragraphs]; _dx = "\n".join(_ps)
for t in ("Seongdae Kim", "kimsd@hongik.ac.kr", ORCID, "Hongik University", "Seoul", "Republic of Korea", "Corresponding author"): ok(t in "\n".join(_ps[:6]), f"제목면 '{t}'")
ok(sum(p == AFFIL for p in _ps[:6]) == 1 and not any(("Korea University" in p) for p in _ps[:8]), "소속 1개(Hongik University)")
ok(_ps.index("Acknowledgements") < _ps.index("Abstract") and AI_STATEMENT in _dx, "감사(AI 고지 정본 문장)는 제목면")
for h, _ in DECL: ok(h in _ps and _ps.index("Statements and Declarations") < _ps.index(h) < _ps.index("References"), f"선언 '{h}'(Statements and Declarations 안, 참고문헌 앞)")
ok("Institutional Review Board" in _dx and "7002340-202511-HR-012" in _dx and "7002340-202611-HR-040" in _dx and "Helsinki" in _dx, "윤리 승인·번호·헬싱키")
_ord = ["Acknowledgements", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Statements and Declarations", "References"]; pos = [_ps.index(k) if k in _ps else -1 for k in _ord]
ok(all(p >= 0 for p in pos) and pos == sorted(pos), f"원고 순서 {pos}")
it = [next(i for i, p in enumerate(_ps) if p.startswith(f"Table {k} ")) for k in (1, 2, 3)]; ok(pos[4] < it[0] < it[1] < it[2] < pos[5], "표 1·2·3이 결과 절 안, 번호 순")
fg = [next((i for i, p in enumerate(_ps) if p.startswith(f"Fig. {k} ")), -1) for k in (1, 2, 3)]; ok(all(x > 0 for x in fg) and fg == sorted(fg) and pos[4] < fg[0] and fg[2] < pos[5], "그림 1·2·3 본문 안(결과 절), 번호 순")
ok(all(not _ps[i].endswith(".") and _ps[i].startswith(f"Fig. {k} ") for k, i in zip((1, 2, 3), fg)), "캡션 'Fig. n' 번호 뒤·끝 구두점 없음")
z = zipfile.ZipFile(os.path.join(OUT, MSF)); ok(z.read("word/document.xml").decode().count("<w:drawing") == 3, "원고에 그림 3개 삽입(IJLM: 본문 안)")
for k in (1, 2, 3):
    im = Image.open(os.path.join(OUT, "Figures", f"Fig{k}.tif")); dpi = round(im.info.get("dpi", (0, 0))[0])
    ok(im.mode == "RGB" and dpi >= 600 and getattr(im, "n_frames", 1) == 1 and abs(im.size[0] / dpi * 25.4 - 174) < 2, f"Fig{k}.tif RGB·{dpi} dpi·단일 층·174 mm·컬러")
src = open(os.path.join(HERE, "figs_illd.py"), encoding="utf-8").read()
ok("PANEL_LABEL_PT = 54" in src and src.count("fontsize=PANEL_LABEL_PT") == 1 and '"abc"' in src and '"d"' in src and not re.search(r'"ABC"|"D", dx', src), "패널 문자 fig.text 상수 54 pt 하나, 소문자(IJLM 규정)")
ok(re.search(r"\bwomen\b", _dx) and re.search(r"\bmen\b", _dx) and "85 years or older" in _dx, "SAGER 성·연령 분해 보고")
tx = "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells); ok(not re.search(r"[*†‡]", tx), "표 각주 기호 = 위첨자 소문자(별표·단검표 없음)")
# 2. 표·문서 위생
for nm, f in (("원고", MSF), ("보충", SUPF), ("커버", CLF)):
    dd = Document(os.path.join(OUT, f))
    for i, t in enumerate(dd.tables):
        tpr = t._tbl.tblPr; b = tpr.find(qn("w:tblBorders"))
        ok(b is not None and all(b.find(qn(f"w:{s}")).get(qn("w:val")) == "nil" for s in ("insideV", "insideH", "left", "right")), f"{nm} 표{i+1} 3선")
        bad = [r.text for j, row in enumerate(t.rows) if j > 0 for c in row.cells if len({id(x._tc) for x in row.cells}) == len(row.cells) for p in c.paragraphs for r in p.runs if r.bold and r.text.strip()]
        ok(not bad, f"{nm} 표{i+1} 데이터 칸 볼드 없음 {bad[:2]}")
        ok(not [c.text for r in t.rows for c in r.cells if re.fullmatch(r"[\d.()\-– ]+\*+", c.text.strip())], f"{nm} 표{i+1} 유의성 별표 없음")
    x = subprocess.run(["unzip", "-p", os.path.join(OUT, f), "word/*.xml"], capture_output=True, text=True).stdout
    ok(len(re.findall(r"<w:keepNext[ />]|<w:keepLines[ />]|<w:pageBreakBefore[ />]", x)) == 0, f"{nm} Word 검은 네모 0건")
    zz = zipfile.ZipFile(os.path.join(OUT, f)); core = zz.read("docProps/core.xml").decode(); app = zz.read("docProps/app.xml").decode()
    ok("2013-12-23" not in core and not any(n.startswith("customXml/") for n in zz.namelist()) and "<Words>0<" not in app, f"{nm} python-docx 지문 없음(sanitize 후)")
# 3. 문체·인용
body = re.sub(r"\s+", " ", _dx[_dx.find("\nIntroduction\n"):_dx.find("\nStatements and Declarations\n")])
ok(not re.search(r"\b(we|our|us|We|Our)\b", body), "1인칭 없음")
supt = "\n".join(p.text for p in Document(os.path.join(OUT, SUPF)).paragraphs) + "\n".join(c.text for t in Document(os.path.join(OUT, SUPF)).tables for r in t.rows for c in r.cells)
cov = subprocess.run(["pdftotext", os.path.join(OUT, CLF.replace(".docx", ".pdf")), "-"], capture_output=True, text=True).stdout
alltxt = _dx + supt + cov
ok("—" not in alltxt and not re.search(r"[가-힣]", alltxt), "em-dash·한글 없음")
ok(not re.search(r"\bsignifican", _dx + supt, re.I), "'significant' 없음")
ok(not re.search(r"(?i)\b(leads? to|drives?|driven by|prevents?)\b", re.sub(r"does not show that physical activity prevents", "", body)), "인과 표현 없음")
US = r"\b(\w*(standardiz|harmoniz|summariz|characteriz|categoriz|minimiz|randomiz|generaliz|normaliz|prioritiz|organiz|utiliz|penaliz)\w*|analyz(e|ed|ing)|modeled|modeling|center(s|ed)?|neighbor\w*|behavior\w*|aging|color|favor\w*|labeled|gray|program)\b"
us = sorted(set(m.group(0) for m in re.finditer(US, body + " " + supt + " " + cov))); ok(not us, f"미국식 철자 없음 {us}")
ok(not re.search(r"ρ -\d|\(-\d|r -\d", body), "마이너스 U+2212")
ok(not re.search(r"\[(@|web:)", _dx) and "{{" not in _dx, "미해결 인용 없음")
ok(not any(":" in x[0] for x in C.METHODS + C.RESULTS), "소제목 쌍점 없음")
refs = _dx[_dx.find("\nReferences\n"):]
ok(not re.search(r"github|zenodo", refs, re.I), "참고문헌에 GitHub·Zenodo 없음")
RL = [l for l in refs.split("\n") if re.match(r"^\d+\. ", l)]
import json as _js; _R = _js.load(open(os.path.join(HERE, "refs_illd.json"), encoding="utf-8")); _nodoi = [l for l in RL if "https://doi.org/" not in l and "Accessed" not in l]
ok(len(_nodoi) == sum(1 for v in _R.values() if v["type"] == "journal" and not v.get("doi")), f"DOI 있는 문헌은 전부 전체 DOI 링크, 웹 문헌은 URL·접근일(DOI 없는 문헌 {len(_nodoi)}건은 원래 DOI 없음)")
ok(all(re.search(r" \((19|20)\d\d\) ", l) for l in RL) and not any(re.search(r"\bdoi: |PMID:", l) for l in RL), "Springer basic 형식(저자 (연도) 제목. 학술지 권:쪽. DOI 링크)")
ok([int(l.split(".")[0]) for l in RL] == list(range(1, len(RL) + 1)), "참고문헌 연속 번호")
ok("Cheol Seong" not in refs, "한국인 저자명 뒤집힘 없음")
ok("R Core Team" in refs, "R 인용")
ok(re.search(r"doi\.org/10\.5281/zenodo\.\d+", _dx) is not None, "Data availability 공개 Zenodo DOI(투고 전 게이트, PENDING이면 부모 처리)")
ok(f"github.com/Seongdae-Kim-Hongik/{REPO}" in _dx and "ill-defined-death-certification-korea" not in _dx, "GitHub 새 저장소 주소")
ok(not re.search(r"(?i)private link|restricted during|token", _dx + cov), "심사 토큰·제한 공개 문구 없음(11/12 규칙)")
for k, lab in C.SUP.items():
    ok(lab in body, f"보충 {lab} 본문 인용")
    ok(lab.split(", ")[-1] in supt, f"보충 {lab.split(', ')[-1]} 보충자료에 존재")
_sord = [body.find(C.SUP[k]) for k in ("strobe", "methods", "substitution", "covariates", "datacheck", "specs")]
first_tab = [m.group(1) for m in re.finditer(r"Table (S\d)", body)]; seen = []; [seen.append(t) for t in first_tab if t not in seen]
ok(seen == sorted(seen), f"보충 표 번호 = 본문 첫 인용 순서 {seen}")
ok(not re.search(r"RR: \d\.\d{2};", body), "RR은 셋째 자리")
ok(sum(1 for l in re.findall(r"\[(\d[\d,\s\-–]*)\]", body)) > 0 and not re.search(r"\{\{|\[@", _dx), "대괄호 숫자 인용")
cc = subprocess.run([sys.executable, os.path.expandvars("$ST_DATA_ROOT") + "/G.Downloads/00_PLAYBOOK/검증기록/check_citation_order.py", os.path.join(OUT, MSF)], capture_output=True, text=True).stdout
ok("FAIL" not in cc and ("PASS" in cc or "통과" in cc), "인용 순서 검사 check_citation_order.py PASS")
open(os.path.join(OUT, "citation_order_ijlm.txt"), "w").write(cc)
open(os.path.join(OUT, "check_ijlm.txt"), "w").write("\n".join(R)); nf = sum(r.startswith("FAIL") for r in R)
print("\n".join(r for r in R if r.startswith("FAIL")) or "", f"\n{len(R)} checks, FAIL {nf}", "PASS" if nf == 0 else "")
