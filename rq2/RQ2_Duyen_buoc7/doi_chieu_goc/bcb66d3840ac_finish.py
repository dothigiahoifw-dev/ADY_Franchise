from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import json
import argparse
p=Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, type=Path)
args = parser.parse_args()
master=pd.read_csv(args.input,low_memory=False)
ids=pd.read_csv(p/'results/M2_sample.csv')
d=master.set_index('transition_id').loc[ids.transition_id].reset_index()
f,(ax,hist)=plt.subplots(1,2,figsize=(10,4))
ax.scatter(d.budget_log_ratio,d.Y,s=16,alpha=.55,color='#1764a0')
ax.set(xlabel='Thay đổi ngân sách (log ratio)',ylabel='Y',title='Ngân sách và thay đổi opening (638 cặp)')
hist.hist(d.budget_log_ratio,bins=25,color='#1764a0',edgecolor='white')
hist.set(xlabel='Thay đổi ngân sách (log ratio)',ylabel='Số cặp',title='Phân bố biến ngân sách trên mẫu M2')
f.tight_layout()
f.savefig(p/'results/budget_review.png',dpi=170)
plt.close(f)
q=d.budget_log_ratio.quantile([.25,.75]);iqr=q.loc[.75]-q.loc[.25]
flag=(d.budget_log_ratio<q.loc[.25]-1.5*iqr)|(d.budget_log_ratio>q.loc[.75]+1.5*iqr)
cols=['transition_id','franchise_id','budget_log_ratio','Y']
d.loc[flag,cols].to_csv(p/'results/budget_IQR_screen.csv',index=False)
summary={'n':len(d),'pearson':stats.pearsonr(d.budget_log_ratio,d.Y).statistic,'spearman':stats.spearmanr(d.budget_log_ratio,d.Y).statistic,'iqr_screen_count':int(flag.sum()),'range':[d.budget_log_ratio.min(),d.budget_log_ratio.max()]}
(p/'results/budget_review.json').write_text(json.dumps(summary,indent=2))
print(summary)
coef=pd.read_csv(p/'results/coefficients_all.csv')
main=coef[coef.model.isin(['M0','M1','M1_budget_sample','M2','M3','M1-C'])].copy()
main.to_csv(p/'results/main_model_coefficients.csv',index=False)
