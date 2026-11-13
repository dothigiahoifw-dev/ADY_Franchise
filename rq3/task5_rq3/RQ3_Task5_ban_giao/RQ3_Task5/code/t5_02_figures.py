"""Task 5 / RQ3 - 5 bieu do chinh ve lai tu du lieu ke thua (khong tinh lai thong ke moi) + sao chep bieu do phu luc.
Moi bieu do: ghi mau, so transition/franchise, dai luong, CI, thong diep chinh (trong hinh + chu thich trong bao cao). Du lieu ve: figures/data/.
Chay: python code/t5_02_figures.py --root ."""
import argparse, os, shutil, textwrap
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); R = ap.parse_args().root
T4 = os.path.join(R, 'inherited_task4_v2'); S56 = os.path.join(T4, 'inherited_step5_6'); RS4 = os.path.join(T4, 'results'); RS56 = os.path.join(S56, 'results'); IN = os.path.join(S56, 'input_tables')
FM, FA, FD = (os.path.join(R, 'figures', d) for d in ('main', 'appendix', 'data'))
for d in (FM, FA, FD): os.makedirs(d, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 200, 'axes.titlesize': 10.5, 'axes.titleweight': 'bold'})
C1, C2, GR = '#1f5a96', '#c0504d', '#888888'
pct = lambda q: 100 * (np.exp(q) - 1)
POS = ['2', '3', '4', '5', '>=6']; POSL = ['2', '3', '4', '5', '≥6']
T = pd.read_csv(os.path.join(IN, 'T1_transitions_A0_with_sample_flags.csv')); a1b = T[T.in_A1b]
P = pd.read_csv(os.path.join(RS56, 'R2_PT1_by_position_all_samples.csv')); A = P[(P['sample'] == 'A1b')].set_index('group')
def foot(fig, txt, y):
    fig.text(0.0, y, textwrap.fill(txt, 190), fontsize=7.5, color='#333', ha='left', va='top')
def save(fig, name):
    fig.savefig(os.path.join(FM, name), bbox_inches='tight'); plt.close(fig)

# ---- Hinh 1: phan phoi toan mau + mau hinh theo vi tri (A1b)
o = A.loc['ALL']; m = A.loc[POS]; x = np.arange(5)
fig, axs = plt.subplots(1, 3, figsize=(15.5, 4.8), gridspec_kw={'width_ratios': [1.25, 1, 1]})
ax = axs[0]; y = a1b.Y.values; lim = 4
ax.hist(np.clip(y, -lim, lim), bins=np.arange(-lim, lim + .01, .2), color=C1, alpha=.8, edgecolor='white')
for v, lab, c, ls in ((0, 'Y = 0 (không đổi)', 'k', '-'), (o.median_Y, f'Trung vị {o.median_pct:+.1f}%', C2, '-'), (o.q1_Y, 'Q1', GR, '--'), (o.q3_Y, 'Q3', GR, '--')):
    ax.axvline(v, color=c, ls=ls, lw=1.5)
ax.text(0.98, 0.97, f'Trung vị Y = {o.median_Y:.3f} → {o.median_pct:+.1f}%\n(CI 95% {o.median_pct_ci_lo:+.1f}% đến {o.median_pct_ci_hi:+.1f}%)\nQ1–Q3: {o.q1_pct:+.1f}% đến {o.q3_pct:+.1f}%\nopening giảm: {o.share_lt0:.1%} ({int(o.n_lt0)}/{int(o.n_transition)})', transform=ax.transAxes, ha='right', va='top', fontsize=8.5, bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
ax.set_xlabel(f'Y = ln(Open_N) − ln(Open_N−1)   (|Y|>4 gộp ở mép: {int((np.abs(y) > lim).sum())} transition)'); ax.set_ylabel('Số transition'); ax.set_title(f'(a) Phân phối Y toàn mẫu A1b — {int(o.n_transition)} transition / {int(o.n_franchise)} franchise')
ax = axs[1]
ax.errorbar(x, m.median_pct, yerr=[m.median_pct - m.median_pct_ci_lo, m.median_pct_ci_hi - m.median_pct], fmt='o', color=C1, capsize=4, ms=7, lw=1.8, label='Trung vị + CI 95%'); ax.vlines(x + .18, m.q1_pct, m.q3_pct, color=GR, lw=5, alpha=.5, label='Q1–Q3')
ax.axhline(0, color='k', lw=1); ax.set_xticks(x); ax.set_xticklabels([f'{p}\nn={int(r.n_transition)}\nF={int(r.n_franchise)}' for p, (_, r) in zip(POSL, m.iterrows())]); ax.set_ylim(-60, 75); ax.set_xlim(-.6, 4.6)
ax.set_ylabel('% thay đổi opening = 100·(exp(Y)−1)'); ax.set_xlabel('Nhóm vị trí (≥6 = vị trí 6–15 gộp)'); ax.set_title('(b) Trung vị % thay đổi theo vị trí'); ax.legend(frameon=False, loc='upper center', ncol=2, fontsize=8)
for xi, (_, r) in zip(x, m.iterrows()): ax.text(xi - .1, r.median_pct, f'{r.median_pct:+.1f}%', ha='right', va='center', fontsize=8)
ax = axs[2]
ax.errorbar(x, m.share_lt0 * 100, yerr=[(m.share_lt0 - m.share_lt0_ci_lo) * 100, (m.share_lt0_ci_hi - m.share_lt0) * 100], fmt='s', color=C2, capsize=4, ms=7, lw=1.8); ax.axhline(50, color='k', ls='--', lw=1)
ax.set_xticks(x); ax.set_xticklabels([f'{p}\nn={int(r.n_transition)}' for p, (_, r) in zip(POSL, m.iterrows())]); ax.set_ylim(25, 95); ax.set_xlim(-.6, 4.9); ax.set_ylabel('Tỷ lệ transition có opening giảm (Y<0), %'); ax.set_xlabel('Nhóm vị trí'); ax.set_title('(c) Tỷ lệ opening giảm theo vị trí')
for xi, (_, r) in zip(x, m.iterrows()): ax.text(xi + .1, r.share_lt0 * 100, f'{r.share_lt0:.1%}', fontsize=8, va='center')
foot(fig, 'Mẫu A1b (910 transition / 557 franchise); ở vị trí 2–5 mỗi franchise đóng góp một transition (F = n), nhóm ≥6 có 68 transition / 31 franchise. CI 95%: bootstrap theo franchise, 10.000 lần, seed 20260101. Thông điệp: opening thường giảm so với phim trước nhưng độ phân tán rất lớn; các nhóm vị trí gồm tập franchise khác nhau nên không đọc thành thay đổi trong cùng franchise. Opening chưa xác minh thị trường/tiền tệ/cửa sổ.', -0.2)
save(fig, 'Hinh1_phan_phoi_va_mau_hinh_theo_vi_tri.png')
pd.concat([A.loc[POS + ['ALL'], ['n_transition', 'n_franchise', 'median_Y', 'median_pct', 'median_pct_ci_lo', 'median_pct_ci_hi', 'q1_pct', 'q3_pct', 'n_lt0', 'share_lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi']]]).to_csv(os.path.join(FD, 'Hinh1_data_PT1_A1b.csv'))

# ---- Hinh 2: cat ngang so voi tap franchise co dinh
C5 = pd.read_csv(os.path.join(RS4, 'T4_C5_PT2lite_fixed_franchise_sets.csv')); fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6))
for ax, (nm, ttl) in zip(axs, (('B3 = {2,3,4}', '(a) Tập cố định {2,3,4}'), ('B4 = {2,3,4,5}', '(b) Tập cố định {2,3,4,5}'))):
    s = C5[C5.set == nm]; xs = s.position.values
    ax.errorbar(xs, s.median_pct, yerr=[s.median_pct - s.median_pct_ci_lo, s.median_pct_ci_hi - s.median_pct], fmt='o-', color=C1, capsize=4, label=f'Cùng {int(s.n_franchise.iloc[0])} franchise (tập cố định), CI 95%')
    ax.plot(xs + .06, s.cross_section_median_pct, 's--', color=C2, label='Cắt ngang A1b (mọi franchise có Y ở vị trí đó)')
    for xv, v in zip(xs, s.median_pct): ax.text(xv + .07, v + 2, f'{v:+.1f}%', ha='left', va='bottom', fontsize=8, color=C1)
    ax.set_xlim(xs.min() - .4, xs.max() + .5)
    ax.axhline(0, color='k', lw=1); ax.set_xticks(xs); ax.set_xlabel('Vị trí N (transition N−1→N)'); ax.set_ylabel('Trung vị % thay đổi opening'); ax.set_title(ttl); ax.legend(frameon=False, fontsize=8, loc='upper right')
foot(fig, 'Mẫu A1b. Tập cố định: franchise có Y ở mọi vị trí trong tập (n = 69 và 32 franchise); cắt ngang: 512 / 204 / 85 / 41 transition ở vị trí 2 / 3 / 4 / 5. Thông điệp: trên cùng một tập franchise, trung vị ở vị trí 2 và 3 khác bảng cắt ngang (+37,1% và +0,8% so với −14,4% và −17,8%; CI ở vị trí 3 chứa 0) nên chênh lệch giữa nhóm vị trí phụ thuộc mạnh vào thành phần franchise. Tập cố định chỉ gồm franchise có đủ các phim sau (chọn lọc), không phải franchise điển hình. CI: bootstrap theo franchise của tập cố định.', -0.1)
save(fig, 'Hinh2_cat_ngang_vs_tap_franchise_co_dinh.png'); C5.to_csv(os.path.join(FD, 'Hinh2_data.csv'), index=False)

# ---- Hinh 3: D
D = pd.read_csv(os.path.join(RS56, 'R3c_D_values_per_franchise.csv')); d = D[D.in_A1b]; p3 = pd.read_csv(os.path.join(RS56, 'R3_PT3_D_all_samples.csv')).set_index('sample').loc['A1b']
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8)); ax = axs[0]; lim = 4
ax.hist(np.clip(d.D, -lim, lim), bins=np.arange(-lim, lim + .01, .25), color=C1, alpha=.8, edgecolor='white'); ax.axvline(0, color='k', lw=1.3); ax.axvline(p3.median_D, color=C2, lw=2); ax.set_ylim(0, 40)
ax.set_xlabel('D = Y(2→3) − Y(1→2)   (|D|>4 gộp ở mép)'); ax.set_ylabel('Số franchise'); ax.set_title(f'(a) Phân phối D — {len(d)} franchise (A1b)')
ax.text(0.98, 0.97, f'Trung vị D = {p3.median_D:.3f}\nCI 95% [{p3.median_D_ci_lo:.3f}; {p3.median_D_ci_hi:.3f}]\nD<0: {int(p3.n_D_lt0)} ({p3.share_D_lt0:.1%}); D>0: {int(p3.n_D_gt0)}', transform=ax.transAxes, ha='right', va='top', fontsize=8.5, bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
ax = axs[1]; ax.scatter(np.clip(d.Y12, -lim, lim), np.clip(d.Y23, -lim, lim), s=14, alpha=.55, color=C1); ax.plot([-lim, lim], [-lim, lim], color=C2, lw=1.3, label='y = x (D = 0)'); ax.axhline(0, color='k', lw=.6); ax.axvline(0, color='k', lw=.6)
ax.set_xlabel('Y(1→2)'); ax.set_ylabel('Y(2→3)'); ax.set_title('(b) Mỗi chấm một franchise'); ax.legend(frameon=False, loc='upper right')
ax.text(0.02, 0.03, f'Trung vị Y(1→2) = {pct(p3.median_Y12):+.1f}%, Y(2→3) = {pct(p3.median_Y23):+.1f}%\nY(2→3)<0 ở {p3.share_Y23_lt0:.1%} franchise', transform=ax.transAxes, fontsize=8, va='bottom', bbox=dict(boxstyle='round', fc='white', ec='#bbb'))
foot(fig, 'Mẫu A1b: franchise có Y ở cả vị trí 2 và 3 (176 franchise, 352 transition). Thông điệp: D<0 nghĩa là mức thay đổi opening ở 2→3 thấp hơn ở 1→2, không có nghĩa opening phim 3 thấp hơn phim 2. Hai Y dùng chung opening phim 2 (hệ số −2 trong D). Mẫu D chỉ gồm franchise có Y ở vị trí 3 (chọn lọc: trung vị Y(1→2) +24,4% so với −14,4% của toàn bộ vị trí 2). |Y|>4 hiển thị tại ±4. CI: bootstrap theo franchise, 10.000 lần.', -0.1)
save(fig, 'Hinh3_phep_so_D.png'); d[['franchise_id', 'Y12', 'Y23', 'D']].to_csv(os.path.join(FD, 'Hinh3_data.csv'), index=False)

# ---- Hinh 4: thanh phan va chon loc
O = pd.read_csv(os.path.join(RS4, 'R10_observability_position3_groups.csv')); O = O[O.group != 'TONG_vi_tri_2'].reset_index(drop=True); C1p = pd.read_csv(os.path.join(RS4, 'T4_C1_sample_composition_by_position.csv')); C2b = pd.read_csv(os.path.join(RS4, 'T4_C2b_CH_vs_rest_by_position.csv'))
lab = ['Có Y ở vị trí 3\n(mẫu PT3)', 'Có phim 3 trong master,\nthiếu opening phim 3', 'Collection quan sát\nchỉ có 2 phim', 'Phim vị trí 3 bị cờ\nunreleased trong dữ liệu']
fig, axs = plt.subplots(1, 2, figsize=(13.5, 4.9), gridspec_kw={'width_ratios': [1.2, 1]}); ax = axs[0]; xx = np.arange(4)
ax.errorbar(xx, O.median_pct_pos2, yerr=[O.median_pct_pos2 - O.median_pct_ci_lo, O.median_pct_ci_hi - O.median_pct_pos2], fmt='o', color=C1, capsize=5, ms=7); ax.axhline(0, color='k', lw=1); ax.axhline(A.loc['2'].median_pct, color=C2, ls='--', lw=1)
ax.text(1.5, 10, f'đường đỏ: trung vị vị trí 2 toàn mẫu {A.loc["2"].median_pct:+.1f}%', color=C2, fontsize=8, ha='center'); ax.set_xticks(xx); ax.set_xticklabels([f'{l}\nn={int(n)}' for l, n in zip(lab, O.n_franchise)], fontsize=7.5)
ax.set_ylabel('Trung vị % thay đổi opening ở vị trí 2'); ax.set_title('(a) Vị trí 2 theo việc có quan sát được Y ở vị trí 3 (512 franchise)')
ax = axs[1]; a1 = C1p[(C1p['sample'] == 'A1b') & C1p.group.isin(POS)].set_index('group').loc[POS]; c2 = C2b.set_index('group').loc[POS]
ax.bar(x - .2, c2.share_of_A1b_in_CH * 100, .4, color=C1, label='% transition thuộc chuỗi CH'); ax2 = ax.twinx(); ax2.plot(x, a1.open_prev_median / 1e6, 'D-', color=C2, label='Trung vị opening phim trước (triệu, đơn vị chưa xác minh)'); ax2.spines['right'].set_visible(True)
ax.set_xticks(x); ax.set_xticklabels([f'{p}\nn={int(n)}' for p, n in zip(POSL, a1.n_transition)]); ax.set_ylabel('% transition thuộc CH'); ax2.set_ylabel('Trung vị opening phim trước (triệu)'); ax.set_xlabel('Nhóm vị trí'); ax.set_ylim(0, 100); ax2.set_ylim(10, 28); ax.set_title('(b) Thành phần mẫu theo vị trí (A1b)')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.5, loc='upper left')
foot(fig, 'Mẫu A1b. (a) 176 + 67 + 258 + 11 = 512 franchise có Y ở vị trí 2; CI 95% bootstrap theo franchise (nhóm n=11 CI rất rộng). Nhóm theo dữ liệu (master, films, pairs_audit), không theo nguyên nhân; nhóm cuối phản ánh cờ unreleased tại thời điểm dữ liệu (2026-10-22), không phải tình trạng phát hành hiện tại. (b) Các nhóm vị trí cao gồm nhiều franchise có chuỗi dài và phim trước lớn hơn. Thông điệp: tập franchise có Y ở vị trí 3 khác tập còn lại ngay từ vị trí 2; thành phần mẫu thay đổi theo vị trí.', -0.24)
save(fig, 'Hinh4_thanh_phan_mau_va_chon_loc.png'); O.to_csv(os.path.join(FD, 'Hinh4a_data.csv'), index=False); pd.concat([a1[['n_transition', 'open_prev_median']], c2[['n_CH', 'share_of_A1b_in_CH']]], axis=1).to_csv(os.path.join(FD, 'Hinh4b_data.csv'))

# ---- Hinh 5: do vung nhom >=6
C9 = pd.read_csv(os.path.join(RS4, 'T4_C9_robustness_ge6_configs.csv')); mn = C9[C9.ci_lo.notna()].reset_index(drop=True); lo_r = C9[C9.config.str.contains('transition ngang nhau: ')]; fr_r = C9[C9.config.str.contains('franchise ngang nhau: ')]
nice = lambda c: c.replace('transition ngang nhau', 'mỗi transition ngang nhau').replace('franchise ngang nhau (1/kf)', 'mỗi franchise ngang nhau (1/k_f)')
fig, axs = plt.subplots(1, 2, figsize=(14.5, 5), gridspec_kw={'width_ratios': [1.4, 1]}); yv = np.arange(len(mn))[::-1]; ax = axs[0]
ax.errorbar(mn.median_pct, yv, xerr=[mn.median_pct - mn.ci_lo, mn.ci_hi - mn.median_pct], fmt='o', color=C1, capsize=4); ax.axvline(0, color='k', lw=1)
ax.axvspan(lo_r.median_pct.min(), lo_r.median_pct.max(), color=GR, alpha=.18, label=f'bỏ từng franchise (A1b), transition ngang nhau: {lo_r.median_pct.min():+.1f}% đến {lo_r.median_pct.max():+.1f}%')
ax.axvspan(fr_r.median_pct.min(), fr_r.median_pct.max(), color=C2, alpha=.10, label=f'bỏ từng franchise (A1b), franchise ngang nhau: {fr_r.median_pct.min():+.1f}% đến {fr_r.median_pct.max():+.1f}%')
ax.set_yticks(yv); ax.set_yticklabels([f'{nice(c)} (n={int(n)}, F={int(f)})' for c, n, f in zip(mn.config, mn.n_transition, mn.n_franchise)], fontsize=8); ax.set_xlabel('Trung vị % thay đổi opening, nhóm ≥6 (CI 95%)'); ax.set_title('(a) Trung vị nhóm ≥6 theo mẫu và trọng số'); ax.legend(frameon=False, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.45, -0.14))
ax = axs[1]; ax.errorbar(mn.share_lt0 * 100, yv, xerr=[(mn.share_lt0 - mn.share_lt0_ci_lo) * 100, (mn.share_lt0_ci_hi - mn.share_lt0) * 100], fmt='s', color=C2, capsize=4); ax.axvline(50, color='k', ls='--', lw=1); ax.set_yticks(yv); ax.set_yticklabels([]); ax.set_xlabel('Tỷ lệ transition có opening giảm (%)'); ax.set_title('(b) Tỷ lệ giảm nhóm ≥6')
foot(fig, 'Nhóm ≥6 gồm các vị trí 6–15 gộp, 26–31 franchise (A2: 26). CI 95% từng cấu hình từ bootstrap theo franchise của mẫu đó; không phải CI của chênh lệch giữa cấu hình. Thông điệp: chiều của trung vị đổi giữa âm và dương theo cấu hình (chưa có chiều nhất quán); tỷ lệ giảm quanh 50% ở mọi cấu hình đã kiểm tra.', -0.22)
save(fig, 'Hinh5_do_vung_nhom_tu_vi_tri_6.png'); C9.to_csv(os.path.join(FD, 'Hinh5_data.csv'), index=False)

# ---- Phu luc: sao chep bieu do co san (nguyen trang)
cp = [('PL1_phan_phoi_Y_theo_vi_tri_boxplot.png', S56, 'figures/F4_PT1_Y_distribution_by_position_A1b.png'), ('PL2_chuoi_CH_va_mau_hinh_dau.png', S56, 'figures/F6_PT4_chain_Y_and_sign_patterns.png'),
      ('PL3_ty_le_dao_chieu_theo_cap.png', T4, 'figures/T4_F4_reversal_rate_adjacent_pairs.png'), ('PL4_do_nhay_chenh_lech_theo_cap_mau.png', S56, 'figures/F7_sensitivity_paired_differences.png'),
      ('PL5_trong_so_nhom_tu_vi_tri_6.png', S56, 'figures/F8_weighting_ge6_transition_vs_franchise.png'), ('PL6_do_phu_vi_tri_x_thap_nien.png', S56, 'figures/F9_coverage_position_by_decade_A1b.png')]
# F9 ten that: tim file
import glob
def find(base, rel):
    pth = os.path.join(base, rel)
    if os.path.exists(pth): return pth
    g = glob.glob(os.path.join(base, os.path.dirname(rel), os.path.basename(rel).split('_')[0] + '_*.png')); return g[0] if g else None
for newname, base, rel in cp:
    src = find(base, rel) or find(os.path.join(base, 'inherited_step5_6') if base == T4 else base, rel)
    if src is None and base == S56: src = find(os.path.join(R, 'inherited_task4_v2', 'inherited_step5_6'), rel)
    if src: shutil.copy(src, os.path.join(FA, newname)); print('appendix', newname)
    else: print('KHONG TIM THAY', rel)
print('figures OK')
