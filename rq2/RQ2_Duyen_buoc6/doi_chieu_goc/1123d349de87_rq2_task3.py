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

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',default='results');a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(a.input,low_memory=False)
    for c in ['Y','open_prev','open_curr','audience_score_prev','critic_score_prev','gap_years','franchise_position_n','release_year_n','budget_log_ratio','cast_retention_top5','log_open_prev']:d[c]=pd.to_numeric(d[c],errors='coerce')
    eligible=d.modeling_eligible.astype(str).str.lower().eq('true')
    valid=np.isfinite(d.Y)&eligible&d.transition_id.notna()&d.franchise_id.notna()
    assert d.transition_id.is_unique
    d['A10']=d.audience_score_prev/10;d['C10']=d.critic_score_prev/10
    d['part']=np.where(d.franchise_position_n==2,'2',np.where(d.franchise_position_n==3,'3','4+'))
    d['era']=pd.cut(d.release_year_n,[-np.inf,1989,1999,2009,2019,np.inf],labels=['pre1990','1990-1999','2000-2009','2010-2019','2020+']).astype(str)
    context=['gap_years','franchise_position_n','release_year_n'];base=d[valid&(d.open_prev>=1e6)&(d.open_curr>=1e6)].copy()
    principal=base.dropna(subset=['A10']+context).copy();budget=principal.dropna(subset=['budget_log_ratio']);critic=base.dropna(subset=['C10']+context);intersection=principal.dropna(subset=['C10'])
    assert (len(base),base.franchise_id.nunique(),len(principal),principal.franchise_id.nunique(),len(budget),budget.franchise_id.nunique())==(689,403,676,394,638,365)
    assert not principal.opening_inconsistent.any()
    extra=['A10']; specs={'M0':(principal,[]),'M1':(principal,extra),'M1_budget_sample':(budget,extra),'M2':(budget,extra+['budget_log_ratio']),'M3':(principal.dropna(subset=['cast_retention_top5']),extra+['cast_retention_top5']),'M1-C':(critic,['C10']),'M1_common_RT':(intersection,extra)}
    wide=d[valid&(d.open_prev>0)&(d.open_curr>0)].dropna(subset=['A10']+context).copy();wide.loc[wide.opening_inconsistent,['transition_id','franchise_id','open_prev','open_curr']].to_csv(out/'opening_flags_wide.csv',index=False)
    specs['M1_positive_excluding_flags']=(wide[~wide.opening_inconsistent],extra)
    logsample=principal.dropna(subset=['log_open_prev']);specs['M1_before_log_open']=(logsample,extra);specs['M1_plus_log_open']=(logsample,extra+['log_open_prev'])
    principal['gap_centered_sq']=(principal.gap_years-principal.gap_years.mean())**2
    specs['M1_gap_quadratic']=(principal,extra+['gap_centered_sq'])
    results={};allrows=[];metas=[]
    for name,(sample,terms) in specs.items():
        r=fit(sample,terms);results[name]=r
        t=r['table'].copy();t.insert(0,'model',name);allrows.append(t);metas.append({'model':name,**r['meta']})
        sample[['transition_id','franchise_id']].to_csv(out/(name+'_sample.csv'),index=False)
    r=results['M1'];r['diag'].to_csv(out/'M1_diagnostics_all.csv',index=False);r['diag'].query('screen_flag').sort_values('cooks_d',ascending=False).to_csv(out/'M1_influence_screen.csv',index=False);r['vif'].to_csv(out/'M1_VIF.csv',index=False)
    # Remove one franchise at a time: audit sensitivity, not automatic exclusion.
    deletion=[]
    for fid in principal.franchise_id.unique():
        rr=fit(principal[principal.franchise_id!=fid],extra)
        b=rr['table'].set_index('term').loc['A10','beta'];deletion.append({'omitted_franchise_id':fid,'beta_A10':b,'delta_beta_A10':b-r['table'].set_index('term').loc['A10','beta']})
    pd.DataFrame(deletion).sort_values('delta_beta_A10').to_csv(out/'M1_leave_one_franchise_out.csv',index=False)
    flagged=r['diag'].loc[r['diag'].cooks_d>4/len(principal),'transition_id']
    sensitivity=principal[~principal.transition_id.isin(flagged)]
    rr=fit(sensitivity,extra);t=rr['table'].copy();t.insert(0,'model','M1_excluding_Cook_screen');allrows.append(t);metas.append({'model':'M1_excluding_Cook_screen',**rr['meta']})
    coef=pd.concat(allrows,ignore_index=True);coef.to_csv(out/'coefficients_all.csv',index=False);pd.DataFrame(metas).to_csv(out/'model_summary.csv',index=False)
    f,ax=plt.subplots(1,3,figsize=(14,4));dd=r['diag'];ax[0].scatter(dd.fitted,dd.residual,s=12,alpha=.5);ax[0].axhline(0,c='black',lw=1);ax[0].set(xlabel='Fitted Y',ylabel='Residual',title='M1: residuals vs fitted');stats.probplot(dd.residual,plot=ax[1]);ax[2].scatter(principal.gap_years,dd.residual,s=12,alpha=.5);ax[2].axhline(0,c='black',lw=1);ax[2].set(xlabel='Gap (years)',ylabel='Residual',title='M1: residuals vs gap');f.tight_layout();f.savefig(out/'diagnostics.png',dpi=170);plt.close(f)
    selected=coef[(coef.term=='A10')&coef.model.isin(['M1','M1_budget_sample','M2','M3','M1_positive_excluding_flags','M1_gap_quadratic','M1_plus_log_open','M1_excluding_Cook_screen'])].copy()
    f,ax=plt.subplots(figsize=(9,5));pos=np.arange(len(selected));ax.errorbar(selected.beta,pos,xerr=np.vstack([selected.beta-selected.ci_low,selected.ci_high-selected.beta]),fmt='o',capsize=4,color='#1864ab');ax.set_yticks(pos,selected.model);ax.axvline(0,color='black',lw=1);ax.set(xlabel='Coefficient per 10 audience points; 95% franchise-cluster CI',title='RQ2: audience score association across specifications');f.tight_layout();f.savefig(out/'audience_coefficients.png',dpi=180);plt.close(f)
    (out/'run_metadata.json').write_text(json.dumps({'input_sha256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'inference':'CR1 finite-sample covariance G/(G-1)*(N-1)/(N-K); t(G-1) intervals and p-values','reference_part':'2','reference_era':'2010-2019','wide_before_flags':[len(wide),wide.franchise_id.nunique()],'wide_after_flags':[len(specs['M1_positive_excluding_flags'][0]),specs['M1_positive_excluding_flags'][0].franchise_id.nunique()],'cook_threshold':4/len(principal),'cook_flag_count':len(flagged),'leave_one_franchise_beta_range':[min(q['beta_A10'] for q in deletion),max(q['beta_A10'] for q in deletion)]},indent=2))
    print(pd.DataFrame(metas).to_string(index=False));print(coef[coef.term.isin(['A10','C10','budget_log_ratio','cast_retention_top5','gap_centered_sq'])].to_string(index=False))
if __name__=='__main__':main()
