#!/usr/bin/env python3
"""Hinh 1: MAE test theo mo hinh va tang (kem moc MAE dev ngoai fold); Hinh 2: delta_MAE test kem khoang boot theo franchise (bo tro)."""
import sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = sys.argv[1]; R = f'{OUT}/results'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.grid': True, 'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False})
M = pd.read_csv(f'{R}/test_metrics.csv'); DC = pd.read_csv(f'{R}/dev_vs_test_mae.csv'); PC = pd.read_csv(f'{R}/test_paired_comparison.csv')
M.merge(DC[['scope', 'model', 'dev_oof_mae']], on=['scope', 'model'])[['scope', 'model', 'n_transitions', 'n_franchises', 'mae_log', 'dev_oof_mae']].to_csv(f'{OUT}/figures/fig1_data.csv', index=False)
PC[['reference', 'scope', 'n_transitions', 'delta_MAE', 'boot_ci95_low', 'boot_ci95_high']].to_csv(f'{OUT}/figures/fig2_data.csv', index=False)
COL = {'Y0': '#9e9e9e', 'median': '#6d8ebf', 'E0': '#1f3a5f'}; LAB = {'Y0': 'Y=0', 'median': 'Median (dev)', 'E0': 'E0'}
fig, axs = plt.subplots(1, 3, figsize=(12, 4.4))
for ax, sc in zip(axs, ['tat ca', 'open_prev >=1M', 'open_prev <1M']):
    d = M[M.scope == sc]; dv = DC[DC.scope == sc].set_index('model')
    for i, m in enumerate(['Y0', 'median', 'E0']):
        v = d[d.model == m].mae_log.iloc[0]; ax.bar(i, v, color=COL[m], width=0.6); ax.text(i, v + 0.01, f'{v:.4f}', ha='center', fontsize=8)
        ax.scatter(i, dv.loc[m, 'dev_oof_mae'], marker='D', color='orange', zorder=3, s=26, label='MAE dev (ngoài fold)' if i == 0 else None)
    n, f = int(d.n_transitions.iloc[0]), int(d.n_franchises.iloc[0]); ax.set_title(f'{sc}: n={n} transition, {f} franchise', fontsize=9)
    ax.set_xticks(range(3)); ax.set_xticklabels([LAB[m] for m in ['Y0', 'median', 'E0']]); ax.set_ylim(0.5 if sc != 'open_prev <1M' else 1.0, None)
axs[0].set_ylabel('MAE log-change'); axs[0].legend(loc='lower left', fontsize=8)
fig.suptitle('Hình 1. MAE log trên 193 transition test (cột) và MAE dev ngoài fold (kim cương cam). Trục y không bắt đầu từ 0', fontsize=10); fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig1_test_mae.png', dpi=150); plt.close(fig)
fig, ax = plt.subplots(figsize=(8, 4.2)); labs = []
for i, (_, r) in enumerate(PC.iterrows()):
    ax.errorbar(r.delta_MAE, i, xerr=[[r.delta_MAE - r.boot_ci95_low], [r.boot_ci95_high - r.delta_MAE]], fmt='o', color='#1f3a5f', capsize=3)
    labs.append(f"E0 so với {'median dev' if r.reference == 'median' else 'Y=0'} — {r.scope} (n={r.n_transitions})")
ax.axvline(0, color='k', lw=0.8); ax.set_yticks(range(len(PC))); ax.set_yticklabels(labs, fontsize=8); ax.invert_yaxis()
ax.set_xlabel('ΔMAE = MAE_baseline − MAE_E0 (dương: E0 sai số thấp hơn)\nthanh = khoảng bootstrap 95% theo franchise (bổ trợ)')
ax.set_title('Hình 2. ΔMAE trên test, dự báo cố định, bootstrap theo franchise', fontsize=10); fig.tight_layout(); fig.savefig(f'{OUT}/figures/fig2_delta_mae.png', dpi=150); plt.close(fig)
print('ok')
