"""RQ3 Buoc 6 - ve bieu do PNG tu results/ va input_tables/ ; xuat kem du lieu ve trong figures/data/.
Chay: python code/03_figures.py --root ."""
import argparse, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
R = ap.parse_args().root
IN, RS, FG = (os.path.join(R, d) for d in ('input_tables', 'results', 'figures'))
FD = os.path.join(FG, 'data')
os.makedirs(FD, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 100, 'savefig.dpi': 200,
                     'axes.titlesize': 11, 'axes.titleweight': 'bold'})
POS = ['2', '3', '4', '5', '>=6']
POSL = ['2', '3', '4', '5', '≥6']
C1, C2, GR = '#1f5a96', '#c0504d', '#888888'
pct = lambda q: 100 * (np.exp(q) - 1)
T = pd.read_csv(os.path.join(IN, 'T1_transitions_A0_with_sample_flags.csv'))
P = pd.read_csv(os.path.join(RS, 'R2_PT1_by_position_all_samples.csv'))
A1b = T[T.in_A1b]
nF = lambda s, g: P[(P['sample'] == s) & (P.group == g)].iloc[0]


def foot(ax_or_fig, txt, fig, y=-0.17):
    fig.text(0.0, y, txt, fontsize=7.5, color='#444', ha='left', va='top', wrap=True)


def save(fig, name):
    fig.savefig(os.path.join(FG, name), bbox_inches='tight')
    plt.close(fig)


# ---------- F1 tong quan Y, A1b
o = nF('A1b', 'ALL')
fig, ax = plt.subplots(figsize=(9, 4.6))
y = A1b.Y.values
lim = 4
ax.hist(np.clip(y, -lim, lim), bins=np.arange(-lim, lim + 0.01, 0.2), color=C1, alpha=.8, edgecolor='white')
for v, lab, c in ((0, 'Y = 0 (opening không đổi)', 'k'), (o.median_Y, f'Trung vị Y = {o.median_Y:.3f} ({o.median_pct:+.1f}%)', C2), (o.q1_Y, 'Q1', GR), (o.q3_Y, 'Q3', GR)):
    ax.axvline(v, color=c, ls='-' if c in ('k', C2) else '--', lw=1.5)
    ax.text(v, ax.get_ylim()[1] * (0.97 if lab != 'Q1' else 0.9), ' ' + lab, color=c, fontsize=8.5, va='top', ha='left' if lab != 'Q1' else 'right')
ax.set_xlabel('Y = ln(Open_N) − ln(Open_{N−1})   (giá trị |Y|>4 gộp vào mép: ' + f'{int((np.abs(y) > lim).sum())} transition)')
ax.set_ylabel('Số transition')
ax.set_title(f'Phân phối Y toàn mẫu A1b — {int(o.n_transition)} transition / {int(o.n_franchise)} franchise')
ax.text(0.99, 0.55, f'Y<0 (opening giảm): {o.n_lt0} ({o.share_lt0:.1%}, CI {o.share_lt0_ci_lo:.1%}–{o.share_lt0_ci_hi:.1%})\nY=0: {int(o.n_eq0)}\nY>0 (opening tăng): {o.n_gt0} ({o.share_gt0:.1%})\n'
        f'Q1–Q3: {o.q1_pct:+.1f}% đến {o.q3_pct:+.1f}%\nCI 95% trung vị: {o.median_pct_ci_lo:+.1f}% đến {o.median_pct_ci_hi:+.1f}%',
        transform=ax.transAxes, ha='right', va='top', fontsize=8.5, bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
foot(ax, 'Mẫu A1b. CI: bootstrap theo franchise, 10.000 lần, percentile 95%. Opening chưa xác minh thị trường/tiền tệ/cửa sổ; mô tả quan sát, không nhân quả.', fig, y=-0.12)
save(fig, 'F1_overview_Y_distribution_A1b.png')
pd.DataFrame({'Y': y, 'transition_id': A1b.transition_id}).to_csv(os.path.join(FD, 'F1_data.csv'), index=False)

# ---------- F2 PT1 trung vi + CI theo vi tri
m = P[(P['sample'] == 'A1b') & (P.group.isin(POS))].set_index('group').loc[POS]
fig, ax = plt.subplots(figsize=(8, 4.8))
x = np.arange(5)
ax.errorbar(x, m.median_pct, yerr=[m.median_pct - m.median_pct_ci_lo, m.median_pct_ci_hi - m.median_pct], fmt='o', color=C1, capsize=5, ms=7, lw=1.8, label='Trung vị + CI 95%')
ax.vlines(x + 0.18, m.q1_pct, m.q3_pct, color=GR, lw=5, alpha=.5, label='Q1–Q3 (IQR)')
ax.axhline(0, color='k', lw=1)
ax.set_xticks(x)
ax.set_xticklabels([f'{p}\nn={int(r.n_transition)}\nF={int(r.n_franchise)}' for p, (_, r) in zip(POSL, m.iterrows())])
ax.set_xlabel('Nhóm vị trí trong collection (≥6 = các vị trí 6 trở đi, gộp; không phải “phần 6”)\nn = số transition, F = số franchise')
ax.set_ylabel('% thay đổi opening tương ứng trung vị Y\n= 100·(exp(Y)−1)')
ax.set_title('PT1 — Trung vị % thay đổi opening theo vị trí (mẫu A1b)')
for xi, (_, r) in zip(x, m.iterrows()):
    ax.text(xi - 0.12, r.median_pct, f'{r.median_pct:+.1f}%', ha='right', va='center', fontsize=8.5)
ax.set_xlim(-0.6, 4.5)
ax.set_ylim(-60, 75)
ax.legend(frameon=False, loc='upper center', ncol=2)
foot(ax, 'Mẫu A1b (910/557). Các nhóm gồm tập franchise khác nhau: không đọc là xu hướng trong cùng franchise. IQR vẽ lệch phải một chút để dễ nhìn.', fig)
save(fig, 'F2_PT1_median_pct_CI_by_position_A1b.png')
m[['n_transition', 'n_franchise', 'median_Y', 'median_pct', 'median_pct_ci_lo', 'median_pct_ci_hi', 'q1_pct', 'q3_pct']].to_csv(os.path.join(FD, 'F2_data.csv'))

# ---------- F3 ty le giam + CI
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.errorbar(x, m.share_lt0 * 100, yerr=[(m.share_lt0 - m.share_lt0_ci_lo) * 100, (m.share_lt0_ci_hi - m.share_lt0) * 100], fmt='s', color=C2, capsize=5, ms=7, lw=1.8)
ax.axhline(50, color='k', lw=1, ls='--')
ax.text(4.45, 50.8, '50%', fontsize=8)
for xi, (_, r) in zip(x, m.iterrows()):
    ax.text(xi + 0.1, r.share_lt0 * 100, f'{r.share_lt0:.1%}\n({int(r.n_lt0)}/{int(r.n_transition)})', fontsize=8.5, va='center')
ax.set_xticks(x)
ax.set_xticklabels([f'{p}\nn={int(r.n_transition)}\nF={int(r.n_franchise)}' for p, (_, r) in zip(POSL, m.iterrows())])
ax.set_ylim(25, 95)
ax.set_xlim(-0.5, 4.8)
ax.set_xlabel('Nhóm vị trí (≥6 gộp nhiều vị trí). n = transition, F = franchise')
ax.set_ylabel('Tỷ lệ transition có Y<0 (opening giảm), %')
ax.set_title('PT1 — Tỷ lệ opening giảm theo vị trí + CI bootstrap theo franchise (A1b)')
foot(ax, 'Mẫu A1b; không có Y=0 trong A1b. CI percentile 95%, 10.000 lần lặp, seed 20260101. Không suy ra xu hướng trong cùng franchise từ khác biệt giữa nhóm.', fig)
save(fig, 'F3_PT1_share_decrease_CI_by_position_A1b.png')
m[['n_transition', 'n_franchise', 'n_lt0', 'share_lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi']].to_csv(os.path.join(FD, 'F3_data.csv'))

# ---------- F4 phan phoi Y theo vi tri
fig, ax = plt.subplots(figsize=(9, 5))
rng = np.random.default_rng(1)
data = [A1b[A1b.pos_bin == p].Y.values for p in POS]
ax.boxplot([np.clip(d, -4, 4) for d in data], positions=x, widths=.5, showfliers=False, medianprops=dict(color=C2, lw=2), boxprops=dict(color=C1), whiskerprops=dict(color=C1), capprops=dict(color=C1))
for xi, d in zip(x, data):
    ax.scatter(xi + rng.uniform(-.22, .22, len(d)), np.clip(d, -4, 4), s=7, alpha=.35, color=C1, zorder=1)
ax.axhline(0, color='k', lw=1)
ax.set_xticks(x)
ax.set_xticklabels([f'{p}\nn={len(d)}, F={A1b[A1b.pos_bin == p].franchise_id.nunique()}' for p, d in zip(POSL, data)])
ax.set_xlabel('Nhóm vị trí (≥6 gộp)')
ax.set_ylabel('Y (|Y|>4 hiển thị tại ±4)')
ax.set_title('PT1 — Phân phối Y theo vị trí (A1b): hộp = Q1–Q3, vạch đỏ = trung vị')
foot(ax, 'Mẫu A1b. Mỗi chấm là một transition. Dữ liệu vẽ: figures/data/F4_data.csv', fig, y=-0.14)
save(fig, 'F4_PT1_Y_distribution_by_position_A1b.png')
A1b[['transition_id', 'franchise_id', 'pos_bin', 'Y']].to_csv(os.path.join(FD, 'F4_data.csv'), index=False)

# ---------- F5 PT3
D = pd.read_csv(os.path.join(RS, 'R3c_D_values_per_franchise.csv'))
d = D[D.in_A1b]
p3 = pd.read_csv(os.path.join(RS, 'R3_PT3_D_all_samples.csv')).set_index('sample').loc['A1b']
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
ax = axs[0]
lim = 4
ax.hist(np.clip(d.D, -lim, lim), bins=np.arange(-lim, lim + .01, .25), color=C1, alpha=.8, edgecolor='white')
ax.axvline(0, color='k', lw=1.3)
ax.axvline(p3.median_D, color=C2, lw=2)
ax.set_ylim(0, 40)
ax.set_xlabel('D = Y(2→3) − Y(1→2)  (|D|>4 gộp vào mép)')
ax.set_ylabel('Số franchise')
ax.set_title(f'PT3 — Phân phối D (A1b, {len(d)} franchise)')
ax.text(0.98, 0.97, f'Trung vị D = {p3.median_D:.3f}\nCI 95%: [{p3.median_D_ci_lo:.3f}; {p3.median_D_ci_hi:.3f}]\nQ1–Q3: [{p3.q1_D:.3f}; {p3.q3_D:.3f}]\nD<0: {int(p3.n_D_lt0)} ({p3.share_D_lt0:.1%}) · D=0: {int(p3.n_D_eq0)} · D>0: {int(p3.n_D_gt0)} ({p3.share_D_gt0:.1%})',
        transform=ax.transAxes, ha='right', va='top', fontsize=8.5, bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
ax = axs[1]
lim = 4
ax.scatter(np.clip(d.Y12, -lim, lim), np.clip(d.Y23, -lim, lim), s=14, alpha=.55, color=C1)
ax.plot([-lim, lim], [-lim, lim], color=C2, lw=1.3, label='y = x (D = 0)')
ax.axhline(0, color='k', lw=.6)
ax.axvline(0, color='k', lw=.6)
ax.set_xlabel('Y(1→2)')
ax.set_ylabel('Y(2→3)')
ax.set_title('Y(2→3) so với Y(1→2), mỗi chấm một franchise')
ax.legend(frameon=False, loc='upper right')
ax.text(0.02, 0.03, f'Dưới đường y=x: D<0 ({int(p3.n_D_lt0)}); trên: D>0 ({int(p3.n_D_gt0)}).\nTrung vị Y(1→2)={p3.median_Y12:+.3f} ({pct(p3.median_Y12):+.0f}%), trung vị Y(2→3)={p3.median_Y23:+.3f} ({pct(p3.median_Y23):+.0f}%)',
        transform=ax.transAxes, fontsize=8, va='bottom', bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
fig.text(0.01, -0.02, 'Mẫu A1b, franchise có Y ở cả vị trí 2 và 3. D<0 không có nghĩa opening phim 3 thấp hơn phim 2. Hai Y chia sẻ opening phim 2 (hệ số −2 trong D); mẫu D gồm franchise đã có phim thứ 3 có opening (chọn lọc). |Y|>4 hiển thị tại ±4.',
         fontsize=7.5, color='#444')
save(fig, 'F5_PT3_D_distribution_and_scatter_A1b.png')
d[['franchise_id', 'Y12', 'Y23', 'D', 'O1', 'O2_from_12', 'O3']].to_csv(os.path.join(FD, 'F5_data.csv'), index=False)

# ---------- F6 PT4
ch = T[T.in_CH_A1b].sort_values(['franchise_id', 'franchise_position_n'])
ctr = pd.read_csv(os.path.join(RS, 'R4c_PT4_position_contribution_and_median.csv'))
ctr = ctr[ctr.chain_sample == 'CH_A1b']
pat = pd.read_csv(os.path.join(RS, 'R4b_PT4_sign_patterns.csv'))
pat = pat[(pat.chain_sample == 'CH_A1b') & (pat.sign_pattern != '__SUMMARY__')]
fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={'width_ratios': [1.5, 1]})
ax = axs[0]
for f, g in ch.groupby('franchise_id'):
    ax.plot(g.franchise_position_n, np.clip(g.Y, -4, 4), color=C1, alpha=.22, lw=1, marker='o', ms=2.5)
ax.plot(ctr.position, np.clip(ctr.median_Y, -4, 4), color=C2, lw=2.2, marker='D', ms=6, label='Trung vị Y tại vị trí (tập franchise thay đổi theo vị trí)')
for _, r in ctr.iterrows():
    ax.text(r.position, -4.35, f'F={int(r.n_franchise_contributing)}', ha='center', fontsize=7.5, color=C2)
ax.axhline(0, color='k', lw=1)
ax.set_ylim(-4.6, 4.2)
ax.set_xticks(ctr.position)
ax.set_xlabel('Vị trí N của transition (N−1→N); F = số franchise đóng góp tại vị trí')
ax.set_ylabel('Y (|Y|>4 hiển thị tại ±4)')
ax.set_title(f'PT4 — Chuỗi Y của {ch.franchise_id.nunique()} franchise / {len(ch)} transition (mẫu CH)')
ax.legend(frameon=False, loc='upper right', fontsize=8)
ax = axs[1]
top = pat.head(12).iloc[::-1]
ax.barh(top.sign_pattern, top.n_franchise, color=C1)
for yv, v in zip(top.sign_pattern, top.n_franchise):
    ax.text(v + .1, yv, str(int(v)), va='center', fontsize=8)
ax.set_xlabel('Số franchise')
ax.set_title('Mẫu hình dấu thường gặp (12 mẫu đầu)\n“+” tăng, “−” giảm; thứ tự từ vị trí 2')
fig.text(0.01, -0.02, f'Mẫu chuỗi Y liên tục từ vị trí 2 theo master (≥3 transition; 58/234), chưa khẳng định đủ toàn collection. {len(pat)} mẫu dấu khác nhau tổng cộng; đường trung vị không phải quỹ đạo của một franchise điển hình.',
         fontsize=7.5, color='#444')
save(fig, 'F6_PT4_chain_Y_and_sign_patterns.png')
ch[['transition_id', 'franchise_id', 'franchise_position_n', 'Y']].to_csv(os.path.join(FD, 'F6_data_chain.csv'), index=False)
ctr.to_csv(os.path.join(FD, 'F6_data_position_contribution.csv'), index=False)

# ---------- F7 do nhay: chenh lech theo cap
S = pd.read_csv(os.path.join(RS, 'R5_sensitivity_paired_differences.csv'))
S = S[S.contrast != 'weights']
cons = ['A0->A1b', 'A1b->A1', 'A1->A2']
labs = ['A0→A1b\n(−8 cặp nghi vấn)', 'A1b→A1\n(−3 cặp chỉ cờ global)', 'A1→A2\n(−126 cặp opening nhỏ)']
fig, axs = plt.subplots(1, 2, figsize=(13, 5))
for ax, (stat, ylab, scale) in zip(axs, (('median', 'Δ trung vị, điểm phần trăm của %thay đổi\n(sau − trước)', 'delta_pct_points'), ('share_lt0', 'Δ tỷ lệ Y<0, điểm phần trăm\n(sau − trước)', 'delta'))):
    s = S[S.statistic == stat]
    for ci_, (c, col) in enumerate(zip(cons, ('#1f5a96', '#7f7f7f', '#c0504d'))):
        for gi, g in enumerate(POS + ['ALL']):
            r = s[(s.contrast == c) & (s.group == g)].iloc[0]
            f = 1 if stat == 'median' else 100
            lo = r['delta_pct_points_ci_lo'] if stat == 'median' else r.delta_ci_lo * f
            hi = r['delta_pct_points_ci_hi'] if stat == 'median' else r.delta_ci_hi * f
            v = r[scale] * (1 if stat == 'median' else 100)
            xx = gi + (ci_ - 1) * 0.25
            ax.errorbar(xx, v, yerr=[[v - lo], [hi - v]], fmt='o', color=col, capsize=3, ms=5, label=labs[ci_].replace('\n', ' ') if gi == 0 else None)
    ax.axhline(0, color='k', lw=1)
    ax.set_xticks(range(6))
    ax.set_xticklabels(POSL + ['Toàn mẫu'])
    ax.set_ylabel(ylab)
    ax.set_xlabel('Nhóm vị trí')
axs[0].set_title('Độ nhạy: thay đổi trung vị khi đổi mẫu (mỗi lần một thay đổi)')
axs[1].set_title('Độ nhạy: thay đổi tỷ lệ opening giảm')
axs[0].legend(frameon=False, fontsize=8, loc='upper left')
fig.text(0.01, -0.03, 'CI 95% của CHÊNH LỆCH: bootstrap ghép cặp, cùng cụm franchise rút chung trên universe A0 (562 franchise), 10.000 lần. Nhiều lần lặp cho chênh lệch đúng bằng 0 (các cặp bị loại không có mặt) nên CI có thể chạm 0 hoặc rất hẹp; không dùng làm kiểm định.',
         fontsize=7.5, color='#444')
save(fig, 'F7_sensitivity_paired_differences.png')
S.to_csv(os.path.join(FD, 'F7_data.csv'), index=False)

# ---------- F8 trong so >=6
W = pd.read_csv(os.path.join(RS, 'R6_weighting_ge6_transition_vs_franchise.csv'))
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
smp = ['A0', 'A1b', 'A1', 'A2']
for ax, (lab, v, lo, hi, tf) in zip(axs, (('Trung vị % thay đổi', 'median_pct', 'median_pct_ci_lo', 'median_pct_ci_hi', 1), ('Tỷ lệ Y<0 (%)', 'share_lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi', 100))):
    for i, sc in enumerate(('transition_equal', 'franchise_equal_1_over_kf')):
        w = W[W.scheme == sc].set_index('sample').loc[smp]
        xx = np.arange(4) + (i - .5) * .25
        ax.errorbar(xx, w[v] * tf, yerr=[(w[v] - w[lo]) * tf, (w[hi] - w[v]) * tf], fmt='o', capsize=4, color=(C1, C2)[i], label=('Mỗi transition ngang nhau', 'Mỗi franchise ngang nhau (w=1/k_f)')[i])
    ax.axhline(0 if tf == 1 else 50, color='k', lw=1, ls='-' if tf == 1 else '--')
    ax.set_xticks(range(4))
    ax.set_xticklabels([f'{s}\nn={int(W[W['sample'] == s].n_transition.iloc[0])}, F={int(W[W['sample'] == s].n_franchise.iloc[0])}' for s in smp])
    ax.set_ylabel(lab)
    ax.set_title(lab + ' — nhóm vị trí ≥6')
axs[0].legend(frameon=False, fontsize=8, loc='lower right')
fig.text(0.01, -0.03, 'Cùng quy tắc phân vị (nghịch đảo CDF) cho cả hai trọng số. CI từ bootstrap theo franchise của từng mẫu (trọng số tính theo từng bản sao cụm). Không phải CI của chênh lệch (xem R5).', fontsize=7.5, color='#444')
save(fig, 'F8_weighting_ge6_transition_vs_franchise.png')
W.to_csv(os.path.join(FD, 'F8_data.csv'), index=False)

# ---------- F9 do phu vi tri x thap nien
cov = pd.read_csv(os.path.join(IN, 'T4_coverage_position_by_decade_A1b.csv'), index_col=0)
fig, ax = plt.subplots(figsize=(9, 3.8))
im = ax.imshow(cov.values, cmap='Blues', aspect='auto')
ax.set_xticks(range(cov.shape[1]))
ax.set_xticklabels(cov.columns)
ax.set_yticks(range(len(cov)))
ax.set_yticklabels(['≥6' if i == '>=6' else i for i in cov.index])
for i in range(cov.shape[0]):
    for j in range(cov.shape[1]):
        ax.text(j, i, int(cov.values[i, j]), ha='center', va='center', fontsize=9, color='white' if cov.values[i, j] > cov.values.max() * .55 else 'black')
ax.set_xlabel('Thập niên năm phát hành phim N')
ax.set_ylabel('Nhóm vị trí')
ax.set_title(f'Độ phủ: số transition theo vị trí × thập niên (A1b, n={int(cov.values.sum())})')
fig.text(0.01, -0.04, 'Bảng kiểm tra mẫu (mô tả độ phủ), không phải phân tích theo thời kỳ.', fontsize=7.5, color='#444')
save(fig, 'F9_coverage_position_by_decade_A1b.png')
cov.to_csv(os.path.join(FD, 'F9_data.csv'))
print('figures OK:', sorted(f for f in os.listdir(FG) if f.endswith('.png')))
