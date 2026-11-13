import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
root=Path(__file__).parent
sys.path.insert(0,str(root/'code/task3'))
from rq2_task3 import fit
parser=argparse.ArgumentParser()
parser.add_argument('--input',required=True)
args=parser.parse_args()
raw=pd.read_csv(args.input,low_memory=False).set_index('transition_id',drop=False)
ids=pd.read_csv(root/'results/M2_sample.csv')
d=raw.loc[ids.transition_id].copy()
d['A10']=d.audience_score_prev/10
d['part']=np.select([d.franchise_position_n.eq(2),d.franchise_position_n.eq(3)],['2','3'],default='4+')
d['era']=pd.cut(d.release_year_n,[-np.inf,1989,1999,2009,2019,np.inf],labels=['pre1990','1990-1999','2000-2009','2010-2019','2020+'])
flag=pd.read_csv(root/'results/budget_IQR_screen.csv')
sub=d[~d.transition_id.isin(flag.transition_id)]
tables=[]
for name,sample in [('M2_full',d),('M2_without_budget_IQR',sub)]:
 r=fit(sample,['A10','budget_log_ratio'])
 t=r['table'].copy()
 t['model']=name
 t['n']=len(sample)
 t['franchises']=sample.franchise_id.nunique()
 tables.append(t)
out=pd.concat(tables)
out.to_csv(root/'results/M2_budget_sensitivity.csv',index=False)
print(out[out.term.isin(['A10','budget_log_ratio'])].to_string(index=False))
