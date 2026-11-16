# -*- coding: utf-8 -*-
# figs_illd.py — ILLD International Journal of Legal Medicine 그림(2026-11-16 다시 그림). 컬러, 패널 문자 = fig.text 상수 PANEL_LABEL_PT(모든 패널 같은 크기·굵기, IJLM 규정상 소문자 a·b·c),
#  방위표 3배(동해 중간), 그림 안 설명문 없음, 결합은 시군구 코드로만. TIFF: 지도 600 dpi, 선화 1200 dpi.
#  Fig 1 (A) 성별 불명확 비율 (B) 연령군별 비율 (C) 전국 연령표준화율 ILLD·순환계 · Fig 2 지도 (A) ILLD SMR (B) 순환계 SMR (C) 결합 SMR (D) 산점도 · Fig 3 강건 5변수 모형별 RR
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch, Polygon, Rectangle
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_illd import load, ROB, SHP, SEX, SUB, PAN, EM, LTC, BLS, TE, MPA
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 174 * MM; DPI = 600; LW = 0.3
PANEL_LABEL_PT = 54   # 15 런북 11/10·37호: 48–64 pt, fig.text 상수 하나
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "legend.fontsize": 8, "legend.title_fontsize": 8.5, "axes.linewidth": 0.6, "pdf.fonttype": 42})
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["region"] = G.region.map(NFC); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")
assert G.region.is_unique and len(G) == 229
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
def label(fig, ax, ch, dx=-0.02, dy=0.01):   # 축 왼쪽 위 바깥, 그림 좌표
    bb = ax.get_position(); fig.text(bb.x0 + dx, bb.y1 + dy, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="bottom", ha="left")
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#303030", linewidth=0.5); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    bx, by, bh = x0 + 0.55 * W_, y0 + 0.03 * H_, 0.012 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + k, by + bh + 0.01 * H_, t, ha="center", va="bottom", fontsize=6.5)
    ax.text(bx + 100000 + 0.015 * W_, by + bh / 2, "km", ha="left", va="center", fontsize=6.5)
    nx, ny, nw, nh = x0 + 0.93 * W_, y0 + 0.40 * H_, 0.06 * W_, 0.20 * H_
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=22, fontweight="bold")
def save(fig, k, dpi=DPI):
    p = os.path.join(FIG, f"IJLM_Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi)); im.save(os.path.join(OUTF, f"Fig{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw"); return im.size

# Fig 1
AG = N["agesex"]; yrs = list(range(2011, 2025))
fig = plt.figure(figsize=(W, 4.2)); axs = [fig.add_axes([0.08 + i * 0.325, 0.25, 0.25, 0.47]) for i in range(3)]
a = axs[0]
for s, lab, c, mk in (("계", "Both sexes", "#000000", "o"), ("남자", "Men", "#2166AC", "s"), ("여자", "Women", "#B2182B", "^")):
    a.plot(yrs, [AG[(y, s, "all")] for y in yrs], color=c, marker=mk, ms=2.8, lw=1.0, label=lab)
a.set_ylim(0, 16); a.set_ylabel("Ill-defined share of deaths (%)"); a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=7.5)
a = axs[1]; AGC = (("<45", "< 45 years", "#FDB863"), ("45-64", "45–64", "#E08214"), ("65-74", "65–74", "#B35806"), ("75-84", "75–84", "#8073AC"), ("85+", "≥ 85", "#2D004B"))
for ag, lab, c in AGC: a.plot(yrs, [AG[(y, "계", ag)] for y in yrs], color=c, marker="o", ms=2.4, lw=1.0, label=lab)
assert max(AG[(y, "계", "85+")] for y in yrs) < 25
a.set_ylim(0, 25); a.set_ylabel("Ill-defined share of deaths (%)"); a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=7.5)
a = axs[2]; Y4 = sorted(N["asr"])
A = pd.read_csv(os.path.join(SUB, "SUB_national_asr.csv"))
a.plot(A.year, A.ILLD, color="#B2182B", marker="o", ms=3, lw=1.0, label="Ill-defined"); a.plot(A.year, A.CIRC, color="#2166AC", marker="s", ms=3, lw=1.0, label="Circulatory")
a.set_ylim(0, 150); a.set_ylabel("Age-standardised rate per 100 000"); a.set_xticks([2011, 2015, 2019, 2024]); a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=7.5)
assert A.CIRC.max() < 150
for a in axs[:2]: a.set_xticks([2011, 2015, 2019, 2024])
for a in axs: a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=8)
for a, ch in zip(axs, "abc"): label(fig, a, ch, dx=-0.075, dy=0.02)
s1 = save(fig, 1, dpi=1200)

# Fig 2 지도
SM = N["sub_smr"].copy(); SM["fbd_region"] = SM.fbd_region.map(NFC)
R2C = dict(zip(G.region, G.cd)); SM["cd"] = SM.fbd_region.map(R2C); assert SM.cd.notna().all() and SM.cd.nunique() == 229   # 이름→코드는 경계 파일 코드표로 한 번만, 결합은 코드
d = SM.set_index("cd")
BR = [0, 0.67, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 99]; LB = ["< 0.67", "0.67–0.79", "0.80–0.89", "0.90–0.99", "1.00–1.09", "1.10–1.24", "1.25–1.49", "≥ 1.50"]
PAL = ["#053061", "#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
for c in ("SMR_ILLD", "SMR_CIRC", "SMR_combined_ILLD_CIRC"): assert d[c].min() >= BR[0] and d[c].max() < BR[-1]
fig = plt.figure(figsize=(W, 6.6))
pos = [[0.00, 0.47, 0.33, 0.45], [0.335, 0.47, 0.33, 0.45], [0.67, 0.47, 0.33, 0.45]]
for (col, ch), p in zip((("SMR_ILLD", "a"), ("SMR_CIRC", "b"), ("SMR_combined_ILLD_CIRC", "c")), pos):
    ax = fig.add_axes(p); gg = G.copy(); gg["v"] = gg.cd.map(d[col]); assert gg.v.notna().all()
    gg.plot(ax=ax, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#b5b5b5", linewidth=0.2); mapax(ax); label(fig, ax, ch, dx=0.0, dy=-0.005)
fig.legend(handles=[Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)], title="Standardised mortality ratio", loc="upper center", bbox_to_anchor=(0.5, 0.475), ncol=8, frameon=False, columnspacing=0.9, handlelength=1.2, fontsize=7.5)
ax = fig.add_axes([0.36, 0.07, 0.30, 0.23])
ax.scatter(d.SMR_ILLD, d.SMR_CIRC, s=7, color="#4D4D4D", edgecolor="none", alpha=0.8); ax.set_xscale("log"); ax.set_yscale("log")
xt = [0.4, 0.6, 1.0, 1.4, 2.0]; yt = [0.6, 0.8, 1.0, 1.25, 1.5]
assert d.SMR_ILLD.min() > xt[0] and d.SMR_ILLD.max() < xt[-1] and d.SMR_CIRC.min() > yt[0] and d.SMR_CIRC.max() < yt[-1], (d.SMR_ILLD.agg(["min", "max"]).tolist(), d.SMR_CIRC.agg(["min", "max"]).tolist())
ax.set_xlim(xt[0], xt[-1]); ax.set_ylim(yt[0], yt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:g}" for x in xt]); ax.set_yticks(yt); ax.set_yticklabels([f"{x:g}" for x in yt]); ax.minorticks_off()
ax.axhline(1, color="#a0a0a0", lw=0.5); ax.axvline(1, color="#a0a0a0", lw=0.5); ax.set_xlabel("SMR, ill-defined deaths"); ax.set_ylabel("SMR, circulatory deaths"); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=8)
label(fig, ax, "d", dx=-0.10, dy=0.0)
s2 = save(fig, 2)

# Fig 3 포레스트
LAB = {LTC: "Long-term care\nhospitals", TE: "Tertiary-educated\nadults", BLS: "Basic livelihood\nrecipients", MPA: "Moderate physical\nactivity", EM: "Emergency medicine\nspecialists"}
ORD = [LTC, TE, BLS, MPA, EM]; assert set(ORD) == set(ROB)
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "o", "#000000"),
       ("Knorr-Held type II", lambda v: N["s43"][("KH_typeII", v)][:3], "D", "#F4A582"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)][:3], "D", "#B2182B"),
       ("Between districts", lambda v: N["bw"][f"{v}__between"][:3], "s", "#8073AC"),
       ("Within districts", lambda v: N["bw"][f"{v}__within"][:3], "s", "#2D004B"),
       ("Circulatory deaths as outcome", lambda v: N["nco"][("CIRC", v)][:3], "^", "#2166AC")]
VALS = [f(v) for v in ORD for _, f, _, _ in MOD]; lo_all = min(t[1] for t in VALS); hi_all = max(t[2] for t in VALS)
fig, ax = plt.subplots(figsize=(W, 4.4)); fig.subplots_adjust(left=0.21, right=0.98, top=0.97, bottom=0.27)
off = np.linspace(-0.36, 0.36, len(MOD))
for i, v in enumerate(ORD):
    for (lab, f, mk, fc), o in zip(MOD, off):
        e, lo, hi = f(v); ax.plot([lo, hi], [i + o] * 2, color=fc, lw=0.9); ax.plot(e, i + o, marker=mk, mfc=fc, mec=fc, ms=3.8, ls="none")
ax.axvline(1, color="#808080", lw=0.6); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis()
ax.set_xscale("log"); xt = [0.65, 0.75, 0.85, 1.0, 1.15]; assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 standard deviation (95% credible interval, log scale)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=fc, marker=m, mfc=fc, mec=fc, lw=0.9, ms=3.8, label=l) for l, _, m, fc in MOD], loc="upper center", bbox_to_anchor=(0.42, -0.15), ncol=3, frameon=False)
s3 = save(fig, 3, dpi=1200)
for k, s, dp in zip((1, 2, 3), (s1, s2, s3), (1200, DPI, 1200)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/dp*25.4:.0f} x {s[1]/dp*25.4:.0f} mm")
