#!/usr/bin/env python3
"""Ve 5 bieu do chinh tu cac bang trong results/ (dev only). Moi bieu do co CSV tao hinh trong figures/."""
import json, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT = sys.argv[1]; R = f'{OUT}/results'; FG = f'{OUT}/figures'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.grid': True, 'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False})
st = json.load(open(f'{R}/_state.json')); SEL = st['selected']
M = pd.read_csv(f'{R}/metrics_models_dev.csv'); W = pd.read_csv(f'{R}/oof_predictions_wide.csv')
inp = pd.read_csv(f'{OUT}/inputs_dev/rq1_inputs_dev.csv').set_index('transition_id').loc[W.transition_id].reset_index()
COL = {'Y0': '#9e9e9e', 'median': '#6d8ebf', 'E0': '#1f3a5f', 'E1': '#d98c2b', 'E2': '#4d9a6b', 'E3': '#b05a8a', 'E4': '#a33b3b'}
LAB = {'Y0': 'Y=0', 'median': 'Median train', 'E0': 'E0 (log_open_prev)', 'E1': 'E1 (+gap)', 'E2': 'E2 (+vị trí)', 'E3': 'E3 (+tháng/năm)', 'E4': 'E4 (đủ 5 feature)'}

# ---- Hình 1
d1 = M[['model', 'pooled_mae', 'fold1_mae', 'fold2_mae', 'fold3_mae', 'fold4_mae', 'rmse']]; d1.to_csv(f'{FG}/fig1_data.csv', index=False)
fig, ax = plt.subplots(figsize=(9, 4.6))
for i, r in d1.iterrows():
    ax.bar(i, r.pooled_mae, color=COL[r.model], alpha=0.85, width=0.6)
    ax.scatter([i] * 4, [r.fold1_mae, r.fold2_mae, r.fold3_mae, r.fold4_mae], color='black', s=16, zorder=3, label='MAE từng fold' if i == 0 else None)
    ax.text(i, r.pooled_mae + 0.012, f'{r.pooled_mae:.4f}', ha='center', fontsize=8)
ax.set_xticks(range(len(d1))); ax.set_xticklabels([LAB[m] for m in d1.model], rotation=20, ha='right')
ax.set_ylim(0.6, 1.0); ax.set_ylabel('MAE log-change (ngoài fold, 725 dòng dev)')
ax.set_title('Hình 1. MAE gộp của baseline và E0–E4; chấm đen = MAE từng fold (trục y bắt đầu từ 0,6)')
ax.legend(loc='upper left'); fig.tight_layout(); fig.savefig(f'{FG}/fig1_mae_models.png', dpi=150); plt.close(fig)

# ---- Hình 2
d2 = W[['transition_id', 'Y', f'pred_{SEL}', 'stratum', 'quality_flag_any']].rename(columns={f'pred_{SEL}': 'prediction'}); d2.to_csv(f'{FG}/fig2_data.csv', index=False)
fig, ax = plt.subplots(figsize=(6.6, 5.6))
for s_, c_ in (('>=1M', '#1f3a5f'), ('<1M', '#d98c2b')):
    m = d2.stratum == s_; ax.scatter(d2.prediction[m], d2.Y[m], s=10, alpha=0.5, color=c_, label=f'open_prev {s_} (n={int(m.sum())})')
f_ = d2.quality_flag_any
ax.scatter(d2.prediction[f_], d2.Y[f_], s=45, marker='x', color='red', label=f'6 dòng có cờ chất lượng')
lo, hi = -11, 7; ax.plot([lo, hi], [lo, hi], 'k--', lw=1, label='y = x (dự báo hoàn hảo)')
ax.set_xlim(-2, 2); ax.set_ylim(lo, hi); ax.axhline(0, color='grey', lw=0.6)
ax.set_xlabel(f'Y dự báo ngoài fold, cấu hình {SEL} (log-change)'); ax.set_ylabel('Y thực tế = ln(Open_N) − ln(Open_N−1)')
ax.set_title(f'Hình 2. Y thực tế và Y dự báo ngoài fold ({SEL})\nTrục x chỉ từ −2 đến 2: mọi dự báo đều nằm trong khoảng này', fontsize=9)
ax.legend(loc='lower right', fontsize=8); fig.tight_layout(); fig.savefig(f'{FG}/fig2_actual_vs_pred.png', dpi=150); plt.close(fig)

# ---- Hình 3
D3 = pd.DataFrame({'transition_id': W.transition_id, 'prediction': W[f'pred_{SEL}'], 'residual': W.Y - W[f'pred_{SEL}'], 'log_open_prev': inp.log_open_prev, 'gap_years': inp.gap_years,
                   'franchise_position_n': inp.franchise_position_n, 'release_month_n': inp.release_month_n, 'release_year_n': inp.release_year_n}); D3.to_csv(f'{FG}/fig3_data.csv', index=False)
fig, axs = plt.subplots(2, 3, figsize=(12, 6.8)); axs = axs.ravel()
specs = [('prediction', 'Dự báo Y (log-change)', False), ('log_open_prev', 'log_open_prev = ln(opening N−1)', False), ('gap_years', 'gap_years (năm, thang log)', True),
         ('franchise_position_n', 'franchise_position_n', False), ('release_month_n', 'Tháng chiếu N', False), ('release_year_n', 'Năm chiếu N', False)]
YL = (-6, 6); outside = int((D3.residual.abs() > 6).sum())
for ax, (c, lab, lg) in zip(axs, specs):
    x = D3[c].values; jit = x + (np.random.default_rng(0).uniform(-0.15, 0.15, len(x)) if c in ('franchise_position_n', 'release_month_n') else 0)
    ax.scatter(jit, D3.residual, s=6, alpha=0.35, color='#1f3a5f')
    if c in ('franchise_position_n', 'release_month_n'):
        g = D3.groupby(c).residual.mean(); ax.plot(g.index, g.values, 'o-', color='red', ms=4, lw=1)
    else:
        q = pd.qcut(D3[c], 10, duplicates='drop'); g = D3.groupby(q, observed=True).agg(x=(c, 'mean'), r=('residual', 'mean')); ax.plot(g.x, g.r, 'o-', color='red', ms=4, lw=1)
    ax.axhline(0, color='k', lw=0.7); ax.set_ylim(*YL); ax.set_xlabel(lab); ax.set_ylabel('Phần dư (thực tế − dự báo)')
    if lg: ax.set_xscale('log')
fig.suptitle(f'Hình 3. Phần dư ngoài fold của {SEL} theo dự báo và feature chính; đường đỏ = trung bình theo nhóm. {outside} điểm ngoài ±6 không hiển thị', fontsize=10)
fig.tight_layout(); fig.savefig(f'{FG}/fig3_residuals.png', dpi=150); plt.close(fig)

# ---- Hình 4
E = pd.read_csv(f'{R}/error_by_group.csv'); E4 = E[E.dimension == 'open_prev'].set_index('group').loc[['<1M', '1-10M', '10-50M', '>=50M']].reset_index()
d4 = E4[['group', 'n_transitions', 'n_franchises', 'mae_Y0', 'mae_median', 'mae_E0', 'mae_selected']]; d4.to_csv(f'{FG}/fig4_data.csv', index=False)
fig, ax = plt.subplots(figsize=(8, 4.6)); w = 0.26
for j, (c, lab, col) in enumerate((('mae_Y0', 'Y=0', COL['Y0']), ('mae_median', 'Median train', COL['median']), ('mae_selected', f'{SEL} (cấu hình chọn)', COL['E0']))):
    ax.bar(np.arange(4) + (j - 1) * w, d4[c], w, label=lab, color=col)
ax.set_xticks(range(4)); ax.set_xticklabels([f"{g}\nn={n} ({f} franchise)" for g, n, f in zip(d4.group, d4.n_transitions, d4.n_franchises)])
ax.set_ylabel('MAE log-change'); ax.set_xlabel('Nhóm opening N−1 (USD)'); ax.set_title('Hình 4. MAE ngoài fold theo nhóm opening phần trước, kèm số transition'); ax.legend()
fig.tight_layout(); fig.savefig(f'{FG}/fig4_error_by_open_prev.png', dpi=150); plt.close(fig)

# ---- Hình 5
S1 = pd.read_csv(f'{R}/s1_metrics.csv'); S2 = pd.read_csv(f'{R}/s2_metrics.csv')
a1 = S1[S1.scope == '719 dong khong co'][['model', 'variant', 'pooled_mae']]; a2 = S2[S2.scope == '725 dong dev'][['model', 'variant', 'pooled_mae']]
a1.assign(panel='S1 (719 dòng không cờ)').to_csv(f'{FG}/fig5_data.csv', index=False); a2.assign(panel='S2 (725 dòng dev)').to_csv(f'{FG}/fig5_data.csv', mode='a', header=False, index=False)
fig, axs = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
for ax, a, ttl, var in ((axs[0], a1, 'S1: trên cùng 719 dòng không bị cờ', 'S1'), (axs[1], a2, 'S2: trên cùng 725 dòng dev', 'S2')):
    mods = ['Y0', 'median', 'E0']; x = np.arange(len(mods))
    for j, (v, col) in enumerate((('main', '#1f3a5f'), (var, '#d98c2b'))):
        vals = [a[(a.model == m) & (a.variant == v)].pooled_mae.iloc[0] for m in mods]
        ax.bar(x + (j - 0.5) * 0.36, vals, 0.36, color=col, label='Run chính' if v == 'main' else f'{var} (fit lại)')
        for xi, vv in zip(x, vals): ax.text(xi + (j - 0.5) * 0.36, vv + 0.008, f'{vv:.4f}', ha='center', fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels([LAB[m] for m in mods], rotation=12); ax.set_title(ttl, fontsize=9); ax.set_ylim(0.7, 0.9); ax.legend(loc='upper left')
axs[0].set_ylabel('MAE log-change ngoài fold (trục y từ 0,7)')
fig.suptitle(f'Hình 5. Run chính so với S1 và S2 trên đúng tập đánh giá tương ứng (cấu hình chọn = {SEL})', fontsize=10)
fig.tight_layout(); fig.savefig(f'{FG}/fig5_sensitivity.png', dpi=150); plt.close(fig)
print('figures ok')
