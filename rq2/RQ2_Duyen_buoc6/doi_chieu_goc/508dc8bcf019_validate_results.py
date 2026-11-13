import sys
from pathlib import Path
import numpy as np,pandas as pd
import statsmodels.api as sm
sys.path.insert(0,str(Path(__file__).parent))
from rq2_task3 import design
p=Path(__file__).parent
raw=pd.read_csv(sys.argv[1]);s=pd.read_csv(p/'results/M1_sample.csv')
d=raw.set_index('transition_id').loc[s.transition_id].reset_index()
d['part']=np.where(d.franchise_position_n==2,'2',np.where(d.franchise_position_n==3,'3','4+'))
d['era']=pd.cut(d.release_year_n,[-np.inf,1989,1999,2009,2019,np.inf],labels=['pre1990','1990-1999','2000-2009','2010-2019','2020+']).astype(str);d['A10']=d.audience_score_prev/10
m=sm.OLS(d.Y,design(d,['A10'])).fit(cov_type='cluster',cov_kwds={'groups':d.franchise_id,'use_correction':True},use_t=True)
t=pd.read_csv(p/'results/coefficients_all.csv').query("model=='M1'")
np.testing.assert_allclose(t.beta,m.params,atol=1e-10);np.testing.assert_allclose(t.se_cluster,m.bse,atol=1e-10);np.testing.assert_allclose(t[['ci_low','ci_high']],m.conf_int(),atol=1e-10)
print('PASS: M1 coefficients, CR1 standard errors and t-based confidence intervals match statsmodels within 1e-10.')
print(m.summary().as_text())
