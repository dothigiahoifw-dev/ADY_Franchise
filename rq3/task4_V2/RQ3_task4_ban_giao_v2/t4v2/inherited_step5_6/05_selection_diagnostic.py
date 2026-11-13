"""Chan doan chon loc (mo ta, khong thay doi thiet ke): Y o vi tri 2 cua franchise CO / KHONG CO Y o vi tri 3 va cua chuoi CH. Mau A1b; CI bootstrap theo franchise (universe A1b)."""
import argparse, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import rq3_engine as E
R = argparse.ArgumentParser(); R.add_argument('--root', default='.'); R = R.parse_args().root
cfg = json.load(open(os.path.join(R, 'config.json')))
T = pd.read_csv(os.path.join(R, 'input_tables', 'T1_transitions_A0_with_sample_flags.csv'))
d = T[T.in_A1b].reset_index(drop=True)
has3 = set(d[d.franchise_position_n == 3].franchise_id)
chf = set(d[d.in_CH_A1b].franchise_id)
p2 = d[d.franchise_position_n == 2]
groups = {'Vi tri 2: franchise CO Y o vi tri 3': p2[p2.franchise_id.isin(has3)], 'Vi tri 2: franchise KHONG co Y o vi tri 3': p2[~p2.franchise_id.isin(has3)],
          'Vi tri 2: franchise thuoc chuoi CH': p2[p2.franchise_id.isin(chf)], 'Vi tri 2: franchise KHONG thuoc CH': p2[~p2.franchise_id.isin(chf)]}
boot = E.Boot(d.franchise_id.unique(), B=cfg['bootstrap']['B'], seed=cfg['bootstrap']['seed'])
defs = {}
for k, g in groups.items():
    defs[k + '|med'] = E.Def(g.Y, g.franchise_id, 'wq'); defs[k + '|lt0'] = E.Def(g.Y, g.franchise_id, 'lt0')
pts, reps = E.run(defs, boot)
rows = []
for k, g in groups.items():
    lo, hi, _ = E.ci(reps[k + '|med']); l2, h2, _ = E.ci(reps[k + '|lt0'])
    rows.append(dict(nhom=k, n_franchise=len(g), median_Y=pts[k + '|med'], median_pct=100 * (np.exp(pts[k + '|med']) - 1), median_pct_ci_lo=100 * (np.exp(lo) - 1), median_pct_ci_hi=100 * (np.exp(hi) - 1),
                     share_lt0=pts[k + '|lt0'], share_lt0_ci_lo=l2, share_lt0_ci_hi=h2))
out = pd.DataFrame(rows)
D = pd.read_csv(os.path.join(R, 'input_tables', 'T2_D_table_franchises_with_Y2_and_Y3.csv')); D = D[D.in_A1b]
out['pearson_Y12_Y23_in_Dsample'] = D[['Y12', 'Y23']].corr().iloc[0, 1]; out['spearman_Y12_Y23_in_Dsample'] = D[['Y12', 'Y23']].corr(method='spearman').iloc[0, 1]
out.to_csv(os.path.join(R, 'results', 'R9_selection_diagnostic_position2_A1b.csv'), index=False)
print(out.round(3).to_string())
