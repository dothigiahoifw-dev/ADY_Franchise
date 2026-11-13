"""Tao bang thu nghiem R8 tu results/ (khong go tay so lieu). Chay: python code/04_test_matrix.py --root ."""
import argparse, os
import numpy as np, pandas as pd
R = argparse.ArgumentParser(); R.add_argument('--root', default='.'); R = R.parse_args().root
RS = os.path.join(R, 'results')
P = pd.read_csv(os.path.join(RS, 'R2_PT1_by_position_all_samples.csv'))
S = pd.read_csv(os.path.join(RS, 'R5_sensitivity_paired_differences.csv'))
W = pd.read_csv(os.path.join(RS, 'R6_weighting_ge6_transition_vs_franchise.csv'))
D = pd.read_csv(os.path.join(RS, 'R3_PT3_D_all_samples.csv')).set_index('sample')
DS = pd.read_csv(os.path.join(RS, 'R3b_PT3_D_sensitivity_paired.csv'))
L = pd.read_csv(os.path.join(RS, 'R7_LOFO_ge6_A1b_optional.csv'))
CP = pd.read_csv(os.path.join(RS, 'R4c_PT4_position_contribution_and_median.csv'))
PAT = pd.read_csv(os.path.join(RS, 'R4b_PT4_sign_patterns.csv'))
pc = lambda x: f'{x:+.1f}%'
rows = []
GL = {'2': '2', '3': '3', '4': '4', '5': '5', '>=6': '≥6', 'ALL': 'toàn mẫu'}


def p1(r):
    return f'trung vị {pc(r.median_pct)} [CI {pc(r.median_pct_ci_lo)}; {pc(r.median_pct_ci_hi)}]; Y<0 {r.share_lt0:.1%} [{r.share_lt0_ci_lo:.1%}; {r.share_lt0_ci_hi:.1%}]; n={int(r.n_transition)}, F={int(r.n_franchise)}'


for g in ['2', '3', '4', '5', '>=6', 'ALL']:
    r = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]
    rows.append(['PT1 CHÍNH', 'A1b; thống kê mô tả + bootstrap theo franchise', f'Vị trí {GL[g]}: trung vị Y→%, tỷ lệ Y<0', p1(r), '— (phương án chính)',
                 'Mô tả; mỗi nhóm là tập franchise khác nhau', 'Giữ làm kết quả chính theo thiết kế đã duyệt'])
for k, lab in (('A0', 'A0 (giữ 8 cặp nghi vấn)'), ('A1', 'A1 (loại thêm 3 cặp chỉ cờ global)'), ('A2', 'A2 (loại thêm cặp opening <100.000)')):
    frm = {'A0': 'A0->A1b', 'A1': 'A1b->A1', 'A2': 'A1->A2'}[k]
    for g in ['2', '3', '4', '5', '>=6', 'ALL']:
        r = P[(P['sample'] == k) & (P.group == g)].iloc[0]
        if k == 'A2':
            main = P[(P['sample'] == 'A1') & (P.group == g)].iloc[0]; ref = 'A1'
        elif k == 'A1':
            main = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]; ref = 'A1b'
        else:
            main = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]; ref = 'A1b'
        sm = S[(S.contrast == frm) & (S.group == g) & (S.statistic == 'median')].iloc[0]
        ss = S[(S.contrast == frm) & (S.group == g) & (S.statistic == 'share_lt0')].iloc[0]
        # chieu cua so sanh: A0 so voi A1b la A1b - A0, nen doi dau de bieu dien 'mau nay - mau doi chieu'
        sign = -1 if k == 'A0' else 1
        dm, dlo, dhi = sign * sm.delta_pct_points, (sign * sm.delta_pct_points_ci_lo if sign == 1 else -sm.delta_pct_points_ci_hi), (sign * sm.delta_pct_points_ci_hi if sign == 1 else -sm.delta_pct_points_ci_lo)
        ds = sign * ss.delta * 100
        rows.append([f'Độ nhạy {k}', f'{lab}; đối chiếu {ref}, mỗi lần một thay đổi', f'Vị trí {GL[g]}', p1(r),
                     f'so với {ref}: Δ trung vị {dm:+.2f} điểm % (CI chênh lệch ghép cặp [{dlo:+.2f}; {dhi:+.2f}]); Δ tỷ lệ Y<0 {ds:+.2f} điểm %; Δn={int(r.n_transition-main.n_transition):+d}',
                     'CI của chênh lệch là bootstrap ghép cặp (cụm chung), không phải CI từng mẫu', 'Chỉ đối chiếu; không đổi mẫu chính'])
for k in ['A0', 'A1b', 'A1', 'A2']:
    t = W[(W['sample'] == k)].set_index('scheme')
    a, b = t.loc['transition_equal'], t.loc['franchise_equal_1_over_kf']
    c = S[(S.contrast == 'weights') & (S.from_ == f'{k}(equal)') & (S.statistic == 'median')].iloc[0]
    cs = S[(S.contrast == 'weights') & (S.from_ == f'{k}(equal)') & (S.statistic == 'share_lt0')].iloc[0]
    rows.append(['Độ nhạy trọng số ≥6', f'{k}, nhóm ≥6; trọng số 1/k_f vs transition ngang nhau', 'Trung vị, tỷ lệ Y<0',
                 f'transition-ngang: {pc(a.median_pct)}, Y<0 {a.share_lt0:.1%}; franchise-ngang: {pc(b.median_pct)} [CI {pc(b.median_pct_ci_lo)}; {pc(b.median_pct_ci_hi)}], Y<0 {b.share_lt0:.1%}; n={int(a.n_transition)}, F={int(a.n_franchise)}; franchise lớn nhất chiếm {a.max_weight_share_single_franchise:.1%} (transition-ngang) vs {b.max_weight_share_single_franchise:.1%} (franchise-ngang) tổng trọng số',
                 f'Δ trung vị {c.delta_pct_points:+.2f} điểm % (CI ghép cặp [{c.delta_pct_points_ci_lo:+.2f}; {c.delta_pct_points_ci_hi:+.2f}]); Δ Y<0 {cs.delta*100:+.2f} điểm % [{cs.delta_ci_lo*100:+.2f}; {cs.delta_ci_hi*100:+.2f}]',
                 'Hai trọng số trả lời câu hỏi khác nhau (transition điển hình vs franchise điển hình); cùng quy tắc phân vị', 'Báo cáo cả hai; không chọn theo kết quả'])
for k in ['A1b', 'A0', 'A1', 'A2']:
    r = D.loc[k]
    ref = {'A1b': '— (phương án chính)', 'A0': 'so A1b', 'A1': 'so A1b', 'A2': 'so A1'}[k]
    extra = ''
    if k != 'A1b':
        c = {'A0': ('A0->A1b', -1), 'A1': ('A1b->A1', 1), 'A2': ('A1->A2', 1)}[k]
        dd = DS[(DS.contrast == c[0]) & (DS.statistic == 'median_D')].iloc[0]
        extra = f'Δ trung vị D {c[1]*dd.delta:+.3f} (CI chênh lệch ghép cặp [{min(c[1]*dd.delta_ci_lo, c[1]*dd.delta_ci_hi):+.3f}; {max(c[1]*dd.delta_ci_lo, c[1]*dd.delta_ci_hi):+.3f}])'
        ref = ref + '; ' + extra
    rows.append(['PT3 CHÍNH' if k == 'A1b' else f'PT3 độ nhạy {k}', f'{k}; D=Y(2→3)−Y(1→2) từng franchise; bootstrap trung vị D', 'Trung vị D, Q1–Q3, tỷ lệ D<0',
                 f'n={int(r.n_franchise)}; trung vị D {r.median_D:+.3f} [CI {r.median_D_ci_lo:+.3f}; {r.median_D_ci_hi:+.3f}]; Q1–Q3 [{r.q1_D:+.3f}; {r.q3_D:+.3f}]; D<0 {r.share_D_lt0:.1%} [{r.share_D_lt0_ci_lo:.1%}; {r.share_D_lt0_ci_hi:.1%}], D=0 {int(r.n_D_eq0)}, D>0 {r.share_D_gt0:.1%}; trung vị Y12 {r.median_Y12:+.3f}, Y23 {r.median_Y23:+.3f}',
                 ref, 'D đo thay đổi mức tăng trưởng, không phải opening phim 3 so với phim 2; mẫu D chọn lọc theo có phim thứ 3', 'Giữ làm bổ trợ theo thiết kế'])
for lab in ['CH_A1b', 'CH_A2']:
    pp = PAT[(PAT.chain_sample == lab) & (PAT.sign_pattern == '__SUMMARY__')].iloc[0]
    c2 = CP[(CP.chain_sample == lab) & (CP.position == 2)].iloc[0]
    rows.append(['PT4 CHÍNH' if lab == 'CH_A1b' else 'PT4 độ nhạy CH_A2', f'{lab}; chuỗi Y liên tục từ vị trí 2 (theo master), mô tả dấu', 'Mẫu hình dấu, đảo chiều trực tiếp',
                 f'{int(pp.n_franchise)} franchise / {int(pp.n_transition_total)} transition; toàn giảm {int(pp.n_all_decrease)}, toàn tăng {int(pp.n_all_increase)}; có ≥1 đảo chiều trực tiếp {int(pp.n_with_ge1_reversal)}; Y=0: {int(pp.n_with_zero)}; ở vị trí 2: Y<0 {c2.share_lt0:.1%} (trung vị {pc(c2.median_pct)})',
                 '— (mô tả)', 'Không có CI; không phải collection đủ; đường trung vị có thành phần franchise thay đổi theo vị trí', 'Giữ làm bổ trợ'])
rows.append(['Tùy chọn LOFO ≥6', 'A1b ≥6, bỏ lần lượt từng franchise (31 lần)', 'Trung vị, tỷ lệ Y<0',
             f'trung vị Y (transition-ngang) từ {L.median_Y_transition_w.min():+.3f} đến {L.median_Y_transition_w.max():+.3f} ({pc(100*(np.exp(L.median_Y_transition_w.min())-1))} đến {pc(100*(np.exp(L.median_Y_transition_w.max())-1))}); trung vị Y (franchise-ngang) từ {L.median_Y_franchise_w.min():+.3f} đến {L.median_Y_franchise_w.max():+.3f}; Y<0 từ {L.share_lt0_transition_w.min():.1%} đến {L.share_lt0_transition_w.max():.1%}',
             'so với A1b ≥6 đầy đủ (−1,6%; Y<0 50,0%)', 'Không bootstrap; quét ảnh hưởng một franchise. Giá trị trung vị ≥6 dịch chuyển khi bỏ một franchise', 'Tùy chọn, chạy vì rẻ; không dùng để chọn cấu hình'])
M = pd.DataFrame(rows, columns=['Phương án', 'Mẫu/phương pháp', 'Đại lượng', 'Kết quả', 'Khác biệt so với phương án chính', 'Nhận xét', 'Quyết định/lý do'])
M.to_csv(os.path.join(RS, 'R8_test_matrix.csv'), index=False, encoding='utf-8-sig')
md = ['| ' + ' | '.join(M.columns) + ' |', '|' + '---|' * len(M.columns)] + ['| ' + ' | '.join(str(v).replace('|', '/') for v in r) + ' |' for r in M.values]
open(os.path.join(RS, 'R8_test_matrix.md'), 'w', encoding='utf-8').write('\n'.join(md))
print('R8 rows', len(M))
