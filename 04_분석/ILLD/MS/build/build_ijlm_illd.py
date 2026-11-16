# build_ijlm_illd.py — ILLD International Journal of Legal Medicine Original article 원고 조립(2026-11-16).
#  IJLM 규정(link.springer.com/journal/414/submission-guidelines 11/16 확인): 초록 150–250, 키워드 4–6, 대괄호 숫자 인용·Springer basic 참고문헌(전체 DOI 링크),
#   제목면(이름·소속·교신 이메일·ORCID, 감사는 제목면), 'Statements and Declarations'(참고문헌 앞), 표 각주 위첨자 소문자, 그림은 본문 안 + TIFF 별도, 캡션 'Fig. 1'(번호·끝 구두점 없음),
#   패널 문자 소문자(a, b, c), 보충은 'Online Resource 1'(ESM_1.pdf). 분량 한도 명시 없음. 단일 익명(제목면 요구).
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from jkms_engine import JKMS
from british import brit
import content_illd as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_illd.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript.md")
PAPER = os.environ.get("ILLD_PAPER_DIR", os.path.expandvars("$ST_DATA_ROOT") + "/G.Downloads/논문_마스터자료/85_불명확사인진단지리_IJLM")
_zf = os.path.join(PAPER, "06_GitHub_Zenodo", "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "10.5281/zenodo.PENDING"
REPO = "korean-death-certificates-ill-defined-geography"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication."
DECL = [
 ("Funding", "No funding was received for conducting this study."),
 ("Competing interests", "The author has no relevant financial or non-financial interests to disclose."),
 ("Ethics approval", "Only published aggregate statistics were used, and no individual could be identified. The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 (7002340-202611-HR-040). The study was performed in accordance with the ethical standards of the 1964 Declaration of Helsinki and its later amendments."),
 ("Consent to participate", "Not applicable. The Institutional Review Board waived informed consent because only published aggregate statistics were used."),
 ("Consent to publish", "Not applicable."),
 ("Data availability", None),
 ("Code availability", None),
 ("Author contributions", "Seongdae Kim conceived and designed the study, obtained and analysed the data, interpreted the results, wrote the manuscript and approved the final version."),
]
def data_statement(): return ("All source data are publicly available aggregate statistics from Statistics Korea, the Ministry of the Interior and Safety, the Community Health Survey and the other national sources cited in the Methods; the processed district-year data are available from the author on reasonable request. "
                             f"Analysis code is openly available at Zenodo (https://doi.org/{ZENODO}) and GitHub (https://github.com/Seongdae-Kim-Hongik/{REPO}).")
def code_statement(): return f"The code that generates every number, table and figure is openly available at Zenodo (https://doi.org/{ZENODO}) and GitHub (https://github.com/Seongdae-Kim-Hongik/{REPO}) under the MIT licence."

def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: " {{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)   # 대괄호 숫자, 앞에 공백
def all_keys():
    src = open(os.path.join(HERE, "content_illd.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

def ref(k):   # Springer basic: 'Kircher T, Nelson J, Burdo H (1985) Title. N Engl J Med 313:1263–1269. https://doi.org/x'
    r = REFS[k]
    if r["type"] == "web":
        t = r["title"].rstrip("."); return f"{r['authors']} ({r['year']}) {t}. {r['url']}. Accessed {r['accessed']}"
    au = r["authors"]; a = ", ".join(au) if len(au) <= 10 else ", ".join(au[:3]) + " et al"
    t = r["title"].rstrip("."); t = t + ("" if t.endswith(("?", "!")) else ".")
    s = f"{a} ({r['year']}) {t} {r['journal']}"
    if r.get("vol"):
        s += f" {r['vol']}" + (f":{r['pages'].replace('-', '–')}" if r.get("pages") else "")
    s += "."
    if r.get("doi"): s += f" https://doi.org/{r['doi']}"
    return s

class TX(JKMS):
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = brit(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)

EN_SEX = {"남자": "Men", "여자": "Women"}
TAB1_COV = [("pop80_share", "Population aged ≥ 80 years, %"), ("urban_population_share", "Urban population share, %"), ("ltc_hospitals_per_100k_65", "Long-term care hospitals per 100 000 aged ≥ 65 years"),
            ("em_specialists_per_100k", "Emergency medicine specialists per 100 000"), ("basic_livelihood_rate", "Basic livelihood recipients, %"), ("tertiary_educated_share", "Tertiary-educated adults, %"),
            ("moderate_pa_rate", "Moderate-or-higher physical activity, %"), ("older_single_household_share", "Older-adult single-person households, %")]
WC = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "ALL"]; WH = ["2011–2015", "2016–2019", "2020–2024", "2011–2024"]
def table1():
    T = N["T1"]; AG = N["agesex"]
    def wshare(sex, ag, a, b):
        return sum(AG[(y, sex, ag)] for y in range(a, b + 1)) / (b - a + 1)
    rows = [["__H__", "Deaths"], ["  District-years, no."] + [f"{T[c]['n']:,}".replace(",", " ") for c in WC], ["  All deaths, no."] + [f"{T[c]['all']:,}".replace(",", " ") for c in WC],
            ["  Ill-defined deaths (R00–R99), no."] + [f"{T[c]['cases']:,}".replace(",", " ") for c in WC], ["  Ill-defined share of all deaths, %"] + [f"{T[c]['share']:.1f}" for c in WC]]
    for s in ("남자", "여자"):
        rows.append([f"    {EN_SEX[s]}, %<sup>a</sup>"] + [f"{wshare(s, 'all', a, b):.1f}" for a, b in ((2011, 2015), (2016, 2019), (2020, 2024), (2011, 2024))])
    for ag, lab in (("<45", "< 45 years"), ("45-64", "45–64 years"), ("65-74", "65–74 years"), ("75-84", "75–84 years"), ("85+", "≥ 85 years")):
        rows.append([f"    {lab}, %<sup>a</sup>"] + [f"{wshare('계', ag, a, b):.1f}" for a, b in ((2011, 2015), (2016, 2019), (2020, 2024), (2011, 2024))])
    rows += [["  Circulatory share of all deaths, %"] + [f"{T[c]['circ']:.1f}" for c in WC],
             ["  District SMR, median (P10–P90)<sup>b</sup>"] + [f"{T[c]['med']:.2f} ({T[c]['p10']:.2f}–{T[c]['p90']:.2f})" for c in WC], ["__H__", "District characteristics, mean (SD)"]]
    for v, lab in TAB1_COV:
        mx = max(abs(T[c]['cov'][v][0]) for c in WC); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
        rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:.{dp}f} ({T[c]['cov'][v][1]:.{dp}f})" for c in WC])
    foot = ("P10–P90: 10th–90th percentile; SD: standard deviation; SMR: standardised mortality ratio. <sup>a</sup>Mean of annual national shares. <sup>b</sup>Observed over sex- and age-standardised expected deaths summed over the period. "
            "Survey and register characteristics are district-year means; sources and units of all characteristics are in Online Resource 1, Table S2.")
    return (f"Table 1 Ill-defined deaths and district characteristics, {N['n_districts']} districts, Republic of Korea, 2011–2024", ["Characteristic"] + WH, rows, foot)

SUBC = [("CIRC", "Circulatory diseases (I00–I99)"), ("IHD", "Ischaemic heart disease (I20–I25)"), ("STRK", "Cerebrovascular disease (I60–I69)"), ("ALZ", "Alzheimer disease (G30)"), ("PNEU", "Pneumonia (J12–J18)"), ("CANM", "Malignant neoplasms (C00–C97)")]
def table3():
    S = N["sub"]; rows = []
    for k, lab in SUBC:
        r = S[k]; rows.append([lab, f"{r['rho_SMR']:.2f}", f"{r['rho_share']:.2f}", f"{r['var_log_SMR_cause']:.4f}", f"{r['var_log_SMR_combined']:.4f}", f"{r['var_combined_random_median']:.4f}", f"{r['p_combined_smaller']:.3f}"])
    for s in ("남자", "여자"):
        r = N["sexsub"][s]; rows.append([f"Circulatory diseases, {EN_SEX[s].lower()}", f"{r['rho_SMR']:.2f}", f"{r['rho_share']:.2f}", f"{r['var_logSMR_circ']:.4f}", f"{r['var_logSMR_combined']:.4f}", f"{r['var_random_median']:.4f}", f"{r['p_combined_smaller']:.3f}"])
    foot = ("SMR: standardised mortality ratio. ρ, Spearman correlation across 229 districts of 14-year SMRs (age-standardised; sex rows, sex-specific) or of shares of all deaths. Combined: ill-defined plus the specific cause. "
            "<sup>a</sup>Median of 999 random pairings of districts (fixed random seed); P, (1 + number of random pairings with a variance at or below the observed combined variance)/(999 + 1); random pairings ignore spatial autocorrelation, so P is descriptive.")
    return ("Table 2 Substitution between ill-defined and specific causes of death, 229 districts, Republic of Korea, 2011–2024",
            ["Specific cause", "ρ, SMR", "ρ, share", "Variance of log SMR, cause alone", "Variance, combined", "Variance, random pairs<sup>a</sup>", "P"], rows, foot)

GROUPS = [("Access to diagnosis and certification", [C.GH, C.EM, C.IM, C.LTC, C.UN]), ("Social conditions", [C.ALN, C.BLS, C.TE, C.DR]), ("Physical activity", [C.WALK, C.MPA, C.FAC, C.VIL]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {C.GH: "General hospitals (−)", C.EM: "Emergency medicine specialists (−)", C.IM: "Internal medicine specialists (−)", C.LTC: "Long-term care hospitals (−)", C.UN: "Unmet health-care need (+)",
         C.ALN: "Older-adult single-person households (+)", C.BLS: "Basic livelihood recipients (+)", C.TE: "Tertiary-educated adults (−)", C.DR: "High-risk drinking (+)",
         C.WALK: "Walking (−)", C.MPA: "Moderate-or-higher physical activity (−)", C.FAC: "Public sports facilities (−)", C.VIL: "Village sports facilities (−)",
         "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians per 1 000", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Population aged ≥ 80 years"}
BEST_KH = "KH_typeIV"; assert min(N["s43_waic"][a] for a in C.KH) == N["s43_waic"][BEST_KH]
def f3(t): return f"{t[0]:.3f} ({t[1]:.3f}–{t[2]:.3f})"
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k = N["s43"][(BEST_KH, v)]
            bt = N["bw"].get(f"{v}__between"); wi = N["bw"].get(f"{v}__within")
            rows.append([f"  {LABEL[v]}", f3((m["IRR"], m["lo"], m["hi"])), f"{100*mv['cred_frac']:.0f}" if mv else "Forced", f3(k), f3(bt) if bt else "–", f3(wi) if wi else "–"])
    foot = (f"CrI: credible interval; RR: rate ratio per 1 standard deviation; expected direction in parentheses. Principal model, negative binomial with a Besag–York–Mollié 2 district effect and random-walk and independent year effects, all characteristics and five forced controls (n = {N['n_rows']} district-years). "
            "<sup>a</sup>Share of the 200 covariate-subset models containing the characteristic in which the CrI excluded 1. <sup>b</sup>Knorr-Held type IV space-time interaction added, the best-fitting interaction model. "
            "<sup>c</sup>District mean and within-district deviation entered together for the five characteristics credible in the principal model; –, not estimated. Means and SDs over 2011–2024 of the characteristics shown in Table 1 are given there; between and within components are per 1 SD of the original characteristic.")
    return (f"Table 3 District characteristics and ill-defined deaths, 229 districts, Republic of Korea, 2011–2024",
            ["Characteristic", "Principal RR (95% CrI)", "Subsets credible, %<sup>a</sup>", "Type IV RR (95% CrI)<sup>b</sup>", "Between districts<sup>c</sup>", "Within districts<sup>c</sup>"], rows, foot)

FIGCAP = {
 1: "Ill-defined deaths in the Republic of Korea, 2011–2024. (a) Share of all deaths with an ill-defined underlying cause (R00–R99) by sex. (b) Share by age group, both sexes. (c) National age-standardised death rates (2015 population) for ill-defined and circulatory deaths.",
 2: "District standardised mortality ratios (SMRs), 229 districts, Republic of Korea, 2011–2024. (a) Ill-defined deaths. (b) Circulatory deaths. (c) Ill-defined and circulatory deaths combined. (d) SMR for circulatory against ill-defined deaths, one point per district, log scales. SMRs are age-standardised and summed over 14 years; thick lines are province boundaries.",
 3: "Rate ratios per 1 standard deviation with 95% credible intervals for the five characteristics credible in the principal model, 229 districts, Republic of Korea, 2011–2024, from the principal model, Knorr-Held type II and type IV space-time models, between-district and within-district components, and circulatory deaths as the outcome of the same model. The horizontal axis is on a log scale.",
}
def foot_row(J, text, sz=9, ls=13):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=True); foot_row(J, t[3], 8); J.counting = c

FIGW = {1: 15.9, 2: 15.9, 3: 15.9}
def put_fig(J, k):
    from PIL import Image
    src = os.path.join(HERE, "figs", f"IJLM_Fig{k}.png"); lo = os.path.join(HERE, "figs", f"IJLM_Fig{k}_embed.png")
    im = Image.open(src); w = int(FIGW[k] / 2.54 * 300); im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS).save(lo, dpi=(300, 300))
    p = J.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if getattr(J, "_pb", False): p.paragraph_format.page_break_before = True; J._pb = False
    p.add_run().add_picture(lo, width=Cm(FIGW[k]))
    c = J.counting; J.counting = False; J.para(f"<b>Fig. {k}</b> {FIGCAP[k].rstrip('.')}", sz=11, after=6); J.counting = c

def build(bw=0, aw=0):
    D = read_draft(); J = TX(cite="bracket")
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim", before=6); J.para(AFFIL)
    J.para(f"<b>Corresponding author:</b> Seongdae Kim, {ADDRESS}. Email: kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.head("Acknowledgements", 1); J.para(AI_STATEMENT)
    J.page_break(); J.head("Abstract", 1)
    for p in D["Abstract"]:
        m = re.match(r"^(Purpose|Methods|Results|Conclusions):\s*(.*)$", p, re.S); J.para(f"<b>{m.group(1)}</b> {m.group(2)}")
    J.para(f"<b>Keywords</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for x in C.METHODS:
        J.head(x[0], 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for x in C.RESULTS:
        h = x[0]; J.head(h, 2)
        for i, p in enumerate(x[1:]):
            J.para(pandoc_cites(p), indent=True)
            if h == "Ill-defined deaths by year, sex and age" and i == 0: put_fig(J, 1); J.page_break(); put_table(J, table1())
            if h == "Geography and substitution" and i == 0: put_fig(J, 2)
            if h == "Geography and substitution" and i == 1: put_table(J, table3())
            if h == "District characteristics" and i == 0: J.new_page("landscape"); put_table(J, table2(), fs=7.5); J.new_page("portrait")
            if h == "District characteristics" and i == 1: put_fig(J, 3)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.head("Statements and Declarations", 1)
    for h, t in DECL:
        J.head(h, 2); J.para(data_statement() if h == "Data availability" else code_statement() if h == "Code availability" else t)
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s = f"{i}. " + ref(k); rl.append(s); J.para(s)
    J.raw = False
    return J, rl, D

STOP = "\nStatements and Declarations\n"
def docx_bw(path):   # 본문 단어 수: Introduction ~ Discussion 끝(Statements 직전), 표·그림 캡션 제외
    from docx import Document
    ps = [x.text for x in Document(path).paragraphs]; t = "\n".join(p for p in ps if not re.match(r"^(Fig\. \d|Table \d )", p))
    return len(t[t.find("\nIntroduction\n"):t.find(STOP)].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    fixed = set()
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_illd_ijlm", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads:
                k = len(ls) - 1
                while k > 0 and ls[k - 1] in heads: k -= 1
                orphan = ls[k]; break
        if orphan is None: return
        if orphan in fixed: print("orphan persists, stop:", orphan); return
        fixed.add(orphan); d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:
                np_ = OxmlElement("w:p"); r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); np_.append(r); p._p.addprevious(np_); break
        d.save(path); print("orphan fixed:", orphan)

MSF = "Manuscript_IJLM.docx"
if __name__ == "__main__":
    p = os.path.join(OUT, MSF); D = read_draft()
    AB = [re.sub(r"^(Purpose|Methods|Results|Conclusions):\s*", "", x) for x in D["Abstract"]]; aw = sum(len(x.split()) for x in AB)
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    heads = {"Abstract", "Introduction", "Methods", "Results", "Discussion", "References", "Acknowledgements", "Statements and Declarations"} | {h for h, _ in DECL} | {x[0] for x in C.METHODS + C.RESULTS}
    fix_orphans(p, heads)
    open(os.path.join(OUT, "wordcount_ijlm.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=3\nfigures=3\ntitle_words={len(TITLE.split())}\nkeywords={len(C.KEYWORDS.split('; '))}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | title words {len(TITLE.split())}")
    assert 150 <= aw <= 250 and 4 <= len(C.KEYWORDS.split("; ")) <= 6
