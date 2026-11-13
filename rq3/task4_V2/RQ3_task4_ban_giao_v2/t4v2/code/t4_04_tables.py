"""Task 4 / RQ3 - lap bang quyet dinh, bang do vung theo phat hien, bang dien giai, R5_v2 (them cot mau). So lieu lay tu results/ (khong go tay)."""
import argparse, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); R = ap.parse_args().root
RS = os.path.join(R, 'results'); INH = os.path.join(R, 'inherited_step5_6', 'results')
P = pd.read_csv(os.path.join(INH, 'R2_PT1_by_position_all_samples.csv')); R5 = pd.read_csv(os.path.join(INH, 'R5_sensitivity_paired_differences.csv'))
R3 = pd.read_csv(os.path.join(INH, 'R3_PT3_D_all_samples.csv')).set_index('sample'); R3b = pd.read_csv(os.path.join(INH, 'R3b_PT3_D_sensitivity_paired.csv'))
W = pd.read_csv(os.path.join(INH, 'R6_weighting_ge6_transition_vs_franchise.csv')); L = pd.read_csv(os.path.join(INH, 'R7_LOFO_ge6_A1b_optional.csv'))
C6 = pd.read_csv(os.path.join(RS, 'T4_C6_extreme_Y_scenario.csv')); C5 = pd.read_csv(os.path.join(RS, 'T4_C5_PT2lite_fixed_franchise_sets.csv')); C5b = pd.read_csv(os.path.join(RS, 'T4_C5b_PT2lite_within_franchise_differences.csv'))
C7 = pd.read_csv(os.path.join(RS, 'T4_C7_reversal_rate_adjacent_pairs.csv')).set_index('tap_cap'); C4 = pd.read_csv(os.path.join(RS, 'T4_C4_zero_difference_diagnosis.csv'))
O = pd.read_csv(os.path.join(RS, 'R10_observability_position3_groups.csv')).set_index('group'); C9 = pd.read_csv(os.path.join(RS, 'T4_C9_robustness_ge6_configs.csv'))
pc = lambda x: f'{x:+.1f}%'; pp = lambda x: f'{x:+.2f}'
# R5_v2: them cot sample cho dong trong so
R5v = R5.copy(); R5v.insert(0, 'sample', R5v.apply(lambda r: r.from_.split('(')[0] if r.contrast == 'weights' else '', axis=1))
R5v.to_csv(os.path.join(RS, 'R5_v2_sensitivity_paired_differences_with_sample_col.csv'), index=False)
GL = {'2': 'vị trí 2', '3': 'vị trí 3', '4': 'vị trí 4', '5': 'vị trí 5', '>=6': 'nhóm ≥6', 'ALL': 'toàn mẫu'}


def rob(g):
    parts = []
    for c, lab in (('A0->A1b', 'A0→A1b'), ('A1b->A1', 'A1b→A1'), ('A1->A2', 'A1→A2')):
        r = R5[(R5.contrast == c) & (R5.group == g) & (R5.statistic == 'median')].iloc[0]
        parts.append(f'{lab}: {pp(r.delta_pct_points)} điểm % [{pp(r.delta_pct_points_ci_lo)}; {pp(r.delta_pct_points_ci_hi)}]')
    e = C6[(C6.contrast == 'A1b: bo |Y|>3 - giu') & (C6.group == g) & (C6.statistic == 'median')].iloc[0]
    parts.append(f'bỏ |Y|>3: {pp(e.delta_pct_points)} [{pp(e.ci_lo)}; {pp(e.ci_hi)}]')
    return '; '.join(parts)


rows = []
def add(fd, mau, est, bang, gh, dien): rows.append(dict(Phat_hien=fd, Mau_va_so=mau, Uoc_luong_CI=est, Bang_chung_do_vung=bang, Gioi_han=gh, Cach_dien_dat_duoc_phep=dien))
for g in ['ALL', '2', '3', '4', '5', '>=6']:
    r = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]
    est = f'trung vị Y {r.median_Y:+.3f} ({pc(r.median_pct)}; CI {pc(r.median_pct_ci_lo)} đến {pc(r.median_pct_ci_hi)}); Y<0 {r.share_lt0:.1%} (CI {r.share_lt0_ci_lo:.1%}–{r.share_lt0_ci_hi:.1%}); Q1–Q3 {pc(r.q1_pct)} đến {pc(r.q3_pct)}'
    mau = f'A1b, {GL[g]}: {int(r.n_transition)} transition / {int(r.n_franchise)} franchise'
    if g == 'ALL':
        add('Toàn mẫu: opening thường giảm so với phim trước', mau, est, rob(g), 'Số gộp chủ yếu phản ánh vị trí 2 (512/910 transition); không phải xu hướng chung của mọi franchise', 'Trong các transition quan sát được, trung vị thay đổi opening là âm và khoảng 57% transition giảm; mô tả, không nhân quả')
    elif g in ('2', '3', '5'):
        add(f'{GL[g].capitalize()}: trung vị Y âm', mau, est, rob(g) + '; chiều âm giữ trong các mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3 đã xét; PT2 trên tập franchise cố định cho kết quả khác ở vị trí 2 và 3 (xem hàng PT2-lite)', 'Tập franchise của nhóm khác nhóm khác; chọn lọc theo việc quan sát được Y ở vị trí tiếp theo; chưa xác minh thị trường/tiền tệ/cửa sổ', f'Ở các transition vào {GL[g]} quan sát được, trung vị opening thấp hơn phim trước (bảng cắt ngang); không đọc thành thay đổi trong cùng franchise')
    elif g == '4':
        add('Vị trí 4: chưa có chiều rõ; CI rộng và chứa 0', mau, est, rob(g), 'CI rộng; trung vị nhỏ so với độ phân tán', 'Ở vị trí 4 chưa có chiều rõ (CI rộng và chứa 0); không diễn giải là “phục hồi”')
    else:
        a2 = C9[C9.config == 'A2 / transition ngang nhau'].iloc[0]; f1 = C9[C9.config == 'A1 / franchise ngang nhau (1/kf)'].iloc[0]
        lo_r = C9[C9.config.str.contains('transition ngang nhau: ')]
        add('Nhóm ≥6: chưa có chiều tăng/giảm nhất quán của trung vị; tỷ lệ giảm quanh 50%', mau, est,
            f'trung vị đổi dấu giữa cấu hình: A2 {pc(a2.median_pct)}; A1 trọng số franchise {pc(f1.median_pct)}; bỏ từng franchise {pc(lo_r.median_pct.min())} đến {pc(lo_r.median_pct.max())}; bỏ |Y|>3: {pp(C6[(C6.contrast=="A1b: bo |Y|>3 - giu")&(C6.group==">=6")&(C6.statistic=="median")].iloc[0].delta_pct_points)} điểm %; tỷ lệ Y<0 từ 47% đến 52% mọi cấu hình',
            'Gộp vị trí 6–15; 31 franchise (26 ở A2); CI rộng (khoảng 35 điểm %)', 'Với nhóm ≥6, dữ liệu không cho thấy chiều tăng hay giảm nhất quán của trung vị; khoảng một nửa transition giảm')
r = R3.loc['A1b']; sens = '; '.join(f"{k}: n={int(R3.loc[k].n_franchise)}, trung vị D {R3.loc[k].median_D:+.3f} [{R3.loc[k].median_D_ci_lo:+.3f}; {R3.loc[k].median_D_ci_hi:+.3f}]" for k in ['A0', 'A1', 'A2'])
b3 = C5b[(C5b.set == 'B3 = {2,3,4}') & C5b.contrast.str.contains(r'Y\(2->3\)')].iloc[0]
add('PT3: mức thay đổi opening ở 2→3 thấp hơn ở 1→2 trong đa số franchise của mẫu D', f'A1b, franchise có Y ở vị trí 2 và 3: {int(r.n_franchise)} franchise / {2*int(r.n_franchise)} transition',
    f'trung vị D {r.median_D:+.3f} (CI {r.median_D_ci_lo:+.3f} đến {r.median_D_ci_hi:+.3f}); D<0 {r.share_D_lt0:.1%} (CI {r.share_D_lt0_ci_lo:.1%}–{r.share_D_lt0_ci_hi:.1%}); trung vị Y(1→2) {pc(100*(np.exp(r.median_Y12)-1))}, Y(2→3) {pc(100*(np.exp(r.median_Y23)-1))}',
    f'độ nhạy mẫu: {sens}; tập cố định {{2,3,4}} n={int(b3.n_franchise)}: trung vị D {b3.median_D:+.3f} [{b3.median_D_ci_lo:+.3f}; {b3.median_D_ci_hi:+.3f}]; cùng chiều ở A0/A1/A2 và tập cố định {2,3,4} đã xét',
    'D dùng chung opening phim 2; mẫu D chỉ gồm franchise có opening phim 3 (chọn lọc); trung vị Y(1→2) của mẫu này cao (+24%) so với toàn mẫu vị trí 2 (−14%)',
    'Trong các franchise có opening ở cả ba phim đầu, mức thay đổi opening từ phim 2 sang 3 thường thấp hơn từ phim 1 sang 2; không nói opening phim 3 giảm hay franchise “mệt mỏi”')
d34 = C5b[C5b.set.str.startswith('tat ca') & C5b.contrast.str.contains(r'Y\(3->4\)')].iloc[0]; d45 = C5b[C5b.set.str.startswith('tat ca') & C5b.contrast.str.contains(r'Y\(4->5\)')].iloc[0]
add('D ở transition cao hơn (bổ trợ): 3→4 chưa phân biệt với 0; 4→5 thấp hơn', f'A1b: D34 n={int(d34.n_franchise)}; D45 n={int(d45.n_franchise)}', f'D34 {d34.median_D:+.3f} [{d34.median_D_ci_lo:+.3f}; {d34.median_D_ci_hi:+.3f}]; D45 {d45.median_D:+.3f} [{d45.median_D_ci_lo:+.3f}; {d45.median_D_ci_hi:+.3f}]',
    'không chạy độ nhạy theo mẫu', 'Cỡ mẫu nhỏ; chọn lọc mạnh hơn', 'Chỉ nêu như kết quả bổ trợ có CI rộng')
ch = C7.loc['cap_trong_CH']; al = C7.loc['tat_ca_cap']; nc = C7.loc['cap_ngoai_CH']
add('PT4/CH: đảo chiều giữa hai transition kề nhau xảy ra ở khoảng một nửa số cặp', 'A1b, chuỗi CH: 58 franchise / 234 transition / 176 cặp kề nhau',
    f'49/58 franchise có ≥1 đảo chiều; theo cặp: CH {ch.reversal_share:.1%} (CI {ch.ci_lo:.1%}–{ch.ci_hi:.1%}), mọi cặp kề nhau {al.reversal_share:.1%} ({al.ci_lo:.1%}–{al.ci_hi:.1%}; {int(al.n_pairs)} cặp/{int(al.n_franchises)} franchise), cặp ngoài CH {nc.reversal_share:.1%} ({nc.ci_lo:.1%}–{nc.ci_hi:.1%})',
    f'49/58 franchise có ≥1 đảo chiều; 89/176 cặp ({ch.reversal_share:.1%}); mức tham chiếu giả định dấu độc lập: {ch.reference_if_signs_independent:.1%} theo cặp (không phải kiểm định, không kết luận dấu độc lập); CH_A2: 48/55 franchise',
    'CH gồm franchise có chuỗi dài (chọn lọc); hai transition kề nhau chia sẻ một opening; mức 50% chỉ là tham chiếu giả định dấu độc lập', 'Khoảng một nửa số cặp kề nhau đổi chiều (89/176) và 49/58 franchise có ít nhất một đảo chiều; không kết luận dấu thực sự độc lập và không giải thích 49/58 bằng độ dài chuỗi')
g0, g1, g2, g3 = O.loc['G0_co_Y_o_vi_tri_3'], O.loc['G1_co_transition_vt3_nhung_thieu_opening_phim_3'], O.loc['G2_collection_quan_sat_chi_co_2_phim'], O.loc['G3_phim_vi_tri_3_bi_co_unreleased_dung_cap_2_3']
add('Chọn lọc: Y ở vị trí 2 khác nhau theo việc có quan sát được Y ở vị trí 3', 'A1b, 512 franchise có Y ở vị trí 2: 176 / 67 / 258 / 11 theo nhóm dữ liệu',
    f'trung vị vị trí 2: có Y3 {pc(g0.median_pct_pos2)} [{pc(g0.median_pct_ci_lo)}; {pc(g0.median_pct_ci_hi)}]; thiếu opening phim 3 {pc(g1.median_pct_pos2)}; collection chỉ 2 phim {pc(g2.median_pct_pos2)}; phim vị trí 3 bị cờ unreleased trong dữ liệu {pc(g3.median_pct_pos2)} (n=11, CI {pc(g3.median_pct_ci_lo)} đến {pc(g3.median_pct_ci_hi)})',
    'Tách nhóm dựa trên master (y_ineligible_reason), bảng films (số phim trong collection) và pairs_audit (đúng cặp 2→3 bị cờ unreleased_film, phim 3 có ngày sau ngày thu thập 2026-10-22; chi tiết R10c); khớp 176+67+258+11 = 512', 'Nhóm theo dữ liệu quan sát, không theo nguyên nhân kinh tế; chưa giải thích vì sao nhóm khác nhau; không mô tả đây là “có/không sản xuất phim 3” và không khẳng định phim 3 “chưa phát hành” ở hiện tại', 'Tập franchise có Y ở vị trí 3 có opening phim 2 tăng so với phim 1 khác rõ so với tập còn lại; đây là mô tả sự khác nhau giữa tập quan sát được, chưa phải giải thích cơ chế chọn lọc')
b = C5[(C5.set == 'B3 = {2,3,4}')].set_index('position')
add('PT2-lite: trên cùng một tập franchise, trung vị theo vị trí khác bảng cắt ngang', 'A1b, tập {2,3,4}: 69 franchise; {2,3,4,5}: 32 franchise',
    f'tập {{2,3,4}}: trung vị vị trí 2 {pc(b.loc[2].median_pct)} [{pc(b.loc[2].median_pct_ci_lo)}; {pc(b.loc[2].median_pct_ci_hi)}], vị trí 3 {pc(b.loc[3].median_pct)}, vị trí 4 {pc(b.loc[4].median_pct)}; cắt ngang A1b: {pc(b.loc[2].cross_section_median_pct)}, {pc(b.loc[3].cross_section_median_pct)}, {pc(b.loc[4].cross_section_median_pct)}',
    'xem bảng T4_C5', 'Tập chỉ gồm franchise có đủ các phim sau (chọn lọc); cỡ mẫu nhỏ', 'Trên tập franchise cố định, trung vị ở vị trí 2 và 3 khác bảng cắt ngang (+37,1% và +0,8% so với −14,4% và −17,8%); thành phần franchise ảnh hưởng mạnh; không dùng làm quỹ đạo franchise điển hình')
pd.DataFrame(rows).to_csv(os.path.join(RS, 'T4_interpretation_table.csv'), index=False, encoding='utf-8-sig')
open(os.path.join(RS, 'T4_interpretation_table.md'), 'w', encoding='utf-8').write('| Phát hiện | Mẫu và số franchise/transition | Ước lượng + CI | Bằng chứng độ vững | Giới hạn | Cách diễn đạt được phép |\n|---|---|---|---|---|---|\n' + '\n'.join('| ' + ' | '.join(str(v).replace('|', '/') for v in r.values()) + ' |' for r in rows))
print('tables OK', len(rows))
