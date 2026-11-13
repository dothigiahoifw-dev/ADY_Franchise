"""Task 4 / RQ3 - bieu do bo sung (PNG) + du lieu ve. Doc results/ cua Task 4 va inherited_step5_6/results."""
import argparse, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); R = ap.parse_args().root
RS = os.path.join(R, 'results'); FG = os.path.join(R, 'figures'); FD = os.path.join(FG, 'data'); os.makedirs(FD, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 200, 'axes.titlesize': 11, 'axes.titleweight': 'bold'})
C1, C2, GR = '#1f5a96', '#c0504d', '#888888'
pct = lambda q: 100 * (np.exp(q) - 1)
def foot(fig, t, y=-0.12): fig.text(0.0, y, t, fontsize=7.5, color='#444', ha='left', va='top')

# ---- T4-F1: vi tri 2 theo kha nang quan sat Y o vi tri 3
O = pd.read_csv(os.path.join(RS, 'R10_observability_position3_groups.csv')); O = O[O.group != 'TONG_vi_tri_2'].reset_index(drop=True)
lab = {'G0_co_Y_o_vi_tri_3': 'Có Y ở vị trí 3\n(mẫu PT3)', 'G1_co_transition_vt3_nhung_thieu_opening_phim_3': 'Có phim 3 trong\nmaster, thiếu\nopening phim 3', 'G2_collection_quan_sat_chi_co_2_phim': 'Collection quan sát\nchỉ có 2 phim', 'G3_phim_vi_tri_3_bi_co_unreleased_dung_cap_2_3': 'Phim vị trí 3 bị cờ\nunreleased trong dữ liệu\n(đúng cặp 2→3)'}
fig, axs = plt.subplots(1, 2, figsize=(13, 4.8)); x = np.arange(len(O))
ax = axs[0]; ax.errorbar(x, O.median_pct_pos2, yerr=[O.median_pct_pos2 - O.median_pct_ci_lo, O.median_pct_ci_hi - O.median_pct_pos2], fmt='o', color=C1, capsize=5, ms=7)
ax.axhline(0, color='k', lw=1); ax.axhline(-14.4, color=C2, ls='--', lw=1); ax.text(1.5, 8, 'đường đỏ: trung vị vị trí 2\ntoàn mẫu A1b = −14,4%', color=C2, fontsize=8, ha='center')
ax.set_xticks(x); ax.set_xticklabels([f"{lab[g]}\nn={int(n)}" for g, n in zip(O.group, O.n_franchise)], fontsize=8); ax.set_ylabel('Trung vị % thay đổi opening ở vị trí 2'); ax.set_title('Y ở vị trí 2 theo khả năng quan sát Y ở vị trí 3 (A1b)')
ax = axs[1]; ax.errorbar(x, O.share_lt0_pos2 * 100, yerr=[(O.share_lt0_pos2 - O.share_lt0_ci_lo) * 100, (O.share_lt0_ci_hi - O.share_lt0_pos2) * 100], fmt='s', color=C2, capsize=5, ms=7)
ax.axhline(50, color='k', ls='--', lw=1); ax.set_xticks(x); ax.set_xticklabels([f"n={int(n)}" for n in O.n_franchise]); ax.set_ylabel('Tỷ lệ Y<0 ở vị trí 2 (%)'); ax.set_title('Tỷ lệ opening giảm ở vị trí 2'); ax.set_ylim(0, 100)
foot(fig, 'Mẫu A1b, 512 franchise có Y ở vị trí 2. Nhóm theo dữ liệu (master, films, pairs_audit), không theo nguyên nhân kinh tế.\n“Không có Y ở vị trí 3” gồm thiếu opening phim 3, collection quan sát chỉ có 2 phim, và phim vị trí 3 bị cờ unreleased trong dữ liệu\n(ngày sau 2026-10-22; tình trạng thực tế chưa xác minh). CI: bootstrap theo franchise. Nhóm n=11 CI rất rộng.')
fig.savefig(os.path.join(FG, 'T4_F1_position2_by_observability_of_Y3.png'), bbox_inches='tight'); plt.close(fig); O.to_csv(os.path.join(FD, 'T4_F1_data.csv'), index=False)

# ---- T4-F2: PT2-lite
C5 = pd.read_csv(os.path.join(RS, 'T4_C5_PT2lite_fixed_franchise_sets.csv')); fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
for ax, (nm, ttl) in zip(axs, (('B3 = {2,3,4}', 'Tập cố định {2,3,4}'), ('B4 = {2,3,4,5}', 'Tập cố định {2,3,4,5}'))):
    s = C5[C5.set == nm]; xs = s.position.values
    ax.errorbar(xs, s.median_pct, yerr=[s.median_pct - s.median_pct_ci_lo, s.median_pct_ci_hi - s.median_pct], fmt='o-', color=C1, capsize=4, label=f'Cùng {int(s.n_franchise.iloc[0])} franchise (tập cố định)')
    ax.plot(xs + .08, s.cross_section_median_pct, 's--', color=C2, label='Cắt ngang A1b (tất cả franchise có Y ở vị trí đó)')
    ax.axhline(0, color='k', lw=1); ax.set_xticks(xs); ax.set_xlabel('Vị trí N'); ax.set_ylabel('Trung vị % thay đổi'); ax.set_title(ttl); ax.legend(frameon=False, fontsize=8, loc='lower left')
foot(fig, 'PT2-lite (bổ trợ): chỉ gồm franchise có Y ở mọi vị trí trong tập nên đã chọn lọc theo việc có đủ các phim sau. CI bootstrap theo franchise của tập cố định. Dùng để xem chênh lệch cắt ngang có phụ thuộc thành phần không, không phải xu hướng franchise điển hình.')
fig.savefig(os.path.join(FG, 'T4_F2_PT2lite_fixed_sets_vs_cross_section.png'), bbox_inches='tight'); plt.close(fig); C5.to_csv(os.path.join(FD, 'T4_F2_data.csv'), index=False)

# ---- T4-F3: do vung nhom >=6
C9 = pd.read_csv(os.path.join(RS, 'T4_C9_robustness_ge6_configs.csv')); main = C9[C9.ci_lo.notna()].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(10, 5)); y = np.arange(len(main))[::-1]
ax.errorbar(main.median_pct, y, xerr=[main.median_pct - main.ci_lo, main.ci_hi - main.median_pct], fmt='o', color=C1, capsize=4)
lo_r = C9[C9.config.str.contains('transition ngang nhau: ')]; fr_r = C9[C9.config.str.contains('franchise ngang nhau: ')]
ax.axvline(0, color='k', lw=1); ax.set_yticks(y); ax.set_yticklabels([f"{c} (n={int(n)}, F={int(f)})" for c, n, f in zip(main.config, main.n_transition, main.n_franchise)], fontsize=8)
ax.axvspan(lo_r.median_pct.min(), lo_r.median_pct.max(), color=GR, alpha=.18, label=f'LOFO A1b, transition ngang nhau: {lo_r.median_pct.min():+.1f}% đến {lo_r.median_pct.max():+.1f}%')
ax.axvspan(fr_r.median_pct.min(), fr_r.median_pct.max(), color=C2, alpha=.10, label=f'LOFO A1b, franchise ngang nhau: {fr_r.median_pct.min():+.1f}% đến {fr_r.median_pct.max():+.1f}%')
ax.set_xlabel('Trung vị % thay đổi, nhóm ≥6 (CI bootstrap 95%)'); ax.set_title('Nhóm ≥6: trung vị theo mẫu và trọng số — chiều đổi giữa các cấu hình'); ax.legend(frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(0.45, -0.12))
foot(fig, 'Nhóm ≥6 gồm các vị trí 6–15, gộp; 26–31 franchise. Dải xám/đỏ: khoảng trung vị khi lần lượt bỏ từng franchise (A1b). CI từng cấu hình từ bootstrap theo franchise của mẫu đó; không phải CI của chênh lệch.', y=-0.3)
fig.savefig(os.path.join(FG, 'T4_F3_robustness_ge6_configs.png'), bbox_inches='tight'); plt.close(fig); C9.to_csv(os.path.join(FD, 'T4_F3_data.csv'), index=False)

# ---- T4-F4: ty le dao chieu
C7 = pd.read_csv(os.path.join(RS, 'T4_C7_reversal_rate_adjacent_pairs.csv')); fig, ax = plt.subplots(figsize=(9, 4.6)); x = np.arange(len(C7))
ax.errorbar(x, C7.reversal_share * 100, yerr=[(C7.reversal_share - C7.ci_lo) * 100, (C7.ci_hi - C7.reversal_share) * 100], fmt='o', color=C1, capsize=4, label='Quan sát (CI bootstrap theo franchise)')
ax.plot(x, C7.reference_if_signs_independent * 100, 'x', color=C2, ms=9, mew=2, label='Tham chiếu giả định dấu độc lập, cùng tỷ lệ Y<0 hai vị trí (không phải kiểm định)')
ax.axhline(50, color='k', lw=.6, ls=':'); ax.set_xticks(x); LB = {'tat_ca_cap': 'Mọi cặp', 'cap_trong_CH': 'Cặp trong CH', 'cap_ngoai_CH': 'Cặp ngoài CH', 'k=2->k+1': 'Transition vị trí\n2 và 3', 'k=3->k+1': 'Transition vị trí\n3 và 4', 'k=4->k+1': 'Transition vị trí\n4 và 5', 'k=>=5->..': 'Transition từ\nvị trí 5 trở đi'}
ax.set_xticklabels([f"{LB.get(t, t)}\n{int(p)} cặp\n{int(f)} franchise" for t, p, f in zip(C7.tap_cap, C7.n_pairs, C7.n_franchises)], fontsize=8)
ax.set_ylabel('Tỷ lệ cặp transition kề nhau đổi chiều (%)'); ax.set_ylim(20, 85); ax.set_title('Tỷ lệ đảo chiều theo cặp transition kề nhau (A1b)'); ax.legend(frameon=False, fontsize=8, loc='upper left')
foot(fig, 'Cặp = hai transition liên tiếp (k→k+1) cùng quan sát được Y. Hai transition kề nhau chia sẻ một opening nên dấu không độc lập về mặt cơ học; “tham chiếu” chỉ để so quy mô, không kết luận dấu độc lập. CH: 89/176 cặp đổi chiều; 49/58 franchise có ≥1 đảo chiều.', y=-0.28)
fig.savefig(os.path.join(FG, 'T4_F4_reversal_rate_adjacent_pairs.png'), bbox_inches='tight'); plt.close(fig); C7.to_csv(os.path.join(FD, 'T4_F4_data.csv'), index=False)
print('figures OK')
