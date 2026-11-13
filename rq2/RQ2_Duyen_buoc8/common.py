"""RQ2 round 1. Python >=3.10; pip install numpy pandas scipy matplotlib.
Run: python rq2_task3.py --input /path/analysis_master_transitions.csv --out results
OLS via numpy.linalg.lstsq; CR1 clustered covariance, t(G-1) inference.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def design(d, extras):
    x=pd.DataFrame({'Intercept':np.ones(len(d)), 'gap_years':d.gap_years},index=d.index)
    for z in ['3','4+']: x['part_'+z]=(d.part==z).astype(float)
    for z in ['pre1990','1990-1999','2000-2009','2020+']: x['era_'+z]=(d.era==z).astype(float)
    for z in extras:x[z]=d[z]
    return x.astype(float)

def fit(d,extras):
    X=design(d,extras); x=X.to_numpy(); y=d.Y.to_numpy(); n,k=x.shape
    assert np.linalg.matrix_rank(x)==k
    b=np.linalg.lstsq(x,y,rcond=None)[0]; e=y-x@b; bread=np.linalg.inv(x.T@x)
    codes,groups=pd.factorize(d.franchise_id); g=len(groups)
    score=np.zeros((g,k)); np.add.at(score,codes,x*e[:,None])
    cov=(g/(g-1))*((n-1)/(n-k))*bread@(score.T@score)@bread
    se=np.sqrt(np.diag(cov)); crit=stats.t.ppf(.975,g-1)
    table=pd.DataFrame({'term':X.columns,'beta':b,'se_cluster':se,'ci_low':b-crit*se,'ci_high':b+crit*se,'p_value':2*stats.t.sf(abs(b/se),g-1)})
    h=np.einsum('ij,jk,ik->i',x,bread,x); mse=e@e/(n-k)
    cook=e**2/(k*mse)*h/(1-h)**2
    diag=d[['transition_id','franchise_id']].copy();diag['residual']=e;diag['fitted']=x@b;diag['leverage']=h;diag['studentized_internal']=e/np.sqrt(mse*(1-h));diag['cooks_d']=cook
    diag['screen_flag']=(cook>4/n)|(h>2*k/n)|(abs(diag.studentized_internal)>3)
    vif=[]
    for j in range(1,k):
        yy=x[:,j]; ee=yy-np.delete(x,j,axis=1)@np.linalg.lstsq(np.delete(x,j,axis=1),yy,rcond=None)[0]
        vif.append({'term':X.columns[j],'vif':(np.sum((yy-yy.mean())**2)/np.sum(ee**2))})
    yy=e**2; ee=yy-x@np.linalg.lstsq(x,yy,rcond=None)[0]; bp=n*(1-ee@ee/np.sum((yy-yy.mean())**2))
    r2=1-e@e/np.sum((y-y.mean())**2)
    return {'table':table,'diag':diag,'vif':pd.DataFrame(vif),'meta':{'n':n,'franchises':g,'k':k,'r2':r2,'adj_r2':1-(1-r2)*(n-1)/(n-k),'bp_lm':bp,'bp_p_descriptive_only':stats.chi2.sf(bp,k-1)},'b':b}


def load_master(path):
    data = pd.read_csv(path, low_memory=False)
    numeric = ['Y', 'open_prev', 'open_curr', 'audience_score_prev',
               'critic_score_prev', 'gap_years', 'franchise_position_n',
               'release_year_n', 'budget_log_ratio', 'cast_retention_top5',
               'log_open_prev']
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors='coerce')
    if data.transition_id.duplicated().any():
        raise ValueError('Duplicate transition_id')
    data['A10'] = data.audience_score_prev / 10
    data['C10'] = data.critic_score_prev / 10
    data['part'] = np.select(
        [data.franchise_position_n.eq(2), data.franchise_position_n.eq(3)],
        ['2', '3'], default='4+')
    data['era'] = pd.cut(
        data.release_year_n, [-np.inf, 1989, 1999, 2009, 2019, np.inf],
        labels=['pre1990', '1990-1999', '2000-2009', '2010-2019', '2020+'])
    valid = (np.isfinite(data.Y)
             & data.modeling_eligible.astype(str).str.lower().eq('true')
             & data.franchise_id.notna() & data.transition_id.notna())
    context = ['gap_years', 'franchise_position_n', 'release_year_n']
    base = data.loc[valid & data.open_prev.ge(1e6) & data.open_curr.ge(1e6)].copy()
    principal = base.dropna(subset=['A10'] + context).copy()
    wide = data.loc[valid & data.open_prev.gt(0) & data.open_curr.gt(0)].dropna(
        subset=['A10'] + context).copy()
    principal['gap_centered_sq'] = (principal.gap_years-principal.gap_years.mean())**2
    samples = {
        'principal': principal,
        'budget': principal.dropna(subset=['budget_log_ratio']).copy(),
        'critic': base.dropna(subset=['C10'] + context).copy(),
        'common_rt': principal.dropna(subset=['C10']).copy(),
        'wide': wide.loc[~wide.opening_inconsistent].copy()}
    return data, base, samples

def basic_specs(samples):
    d = samples['principal']
    return {
        'M0': (d, []),
        'M1': (d, ['A10']),
        'M1_budget_sample': (samples['budget'], ['A10']),
        'M2': (samples['budget'], ['A10', 'budget_log_ratio']),
        'M3': (d.dropna(subset=['cast_retention_top5']), ['A10', 'cast_retention_top5']),
        'M1-C': (samples['critic'], ['C10']),
        'M1_common_RT': (samples['common_rt'], ['A10'])}

def export_models(specifications, out):
    coefficients, summary = [], []
    for name, (sample, terms) in specifications.items():
        result = fit(sample, terms)
        coefficients.append(result['table'].assign(model=name))
        summary.append(dict(model=name, **result['meta']))
        sample[['transition_id', 'franchise_id']].to_csv(
            out / (name + '_sample.csv'), index=False)
    pd.concat(coefficients, ignore_index=True).to_csv(out/'coefficients.csv', index=False)
    pd.DataFrame(summary).to_csv(out/'model_summary.csv', index=False)
