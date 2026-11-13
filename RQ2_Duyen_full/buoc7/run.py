import argparse
from pathlib import Path
from common import load_master, basic_specs, fit, export_models, pd, np, stats, plt
parser=argparse.ArgumentParser()
parser.add_argument('--master',required=True)
args=parser.parse_args()
out=Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
data,base,samples=load_master(args.master)
d=samples['principal']
main=fit(d,['A10'])
diagnostics=main['diag']
diagnostics.to_csv(out/'M1_diagnostics_all.csv',index=False)
screen=diagnostics.loc[diagnostics.screen_flag].copy()
screen.to_csv(out/'M1_influence_screen.csv',index=False)
ids=diagnostics.loc[diagnostics.cooks_d>4/len(d),'transition_id']
without_cook=d.loc[~d.transition_id.isin(ids)]
budget=samples['budget']
q=budget.budget_log_ratio.quantile([.25,.75])
width=q.loc[.75]-q.loc[.25]
flag=(budget.budget_log_ratio<q.loc[.25]-1.5*width)|(budget.budget_log_ratio>q.loc[.75]+1.5*width)
budget.loc[flag,['transition_id','franchise_id','budget_log_ratio','Y']].to_csv(out/'budget_IQR_screen.csv',index=False)
specs={
 'M1_positive_excluding_flags':(samples['wide'],['A10']),
 'M1_plus_log_open':(d.dropna(subset=['log_open_prev']),['A10','log_open_prev']),
 'M1_gap_quadratic':(d,['A10','gap_centered_sq']),
 'M1_excluding_Cook_screen':(without_cook,['A10']),
 'gap_le_20':(d.loc[d.gap_years<=20],['A10']),
 'gap_le_20_quadratic':(d.loc[d.gap_years<=20],['A10','gap_centered_sq']),
 'without_Cook_quadratic':(without_cook,['A10','gap_centered_sq']),
 'M2_without_budget_IQR':(budget.loc[~flag],['A10','budget_log_ratio'])}
export_models(specs,out)
vifs=[]
for name,(frame,terms) in basic_specs(samples).items():
    vifs.append(fit(frame,terms)['vif'].assign(model=name))
pd.concat(vifs).to_csv(out/'vif.csv',index=False)
deletion=[]
for franchise in d.franchise_id.unique():
    result=fit(d.loc[d.franchise_id!=franchise],['A10'])
    value=result['table'].set_index('term').loc['A10','beta']
    deletion.append(dict(omitted_franchise_id=franchise,beta_A10=value))
pd.DataFrame(deletion).to_csv(out/'leave_one_franchise_out.csv',index=False)
review_columns=['transition_id','gap_years','open_prev','open_curr','Y','audience_score_prev']
review_columns += [c for c in ['title_prev','title_curr'] if c in d]
screen.merge(d[review_columns],on='transition_id',validate='one_to_one').to_csv(out/'influence_review.csv',index=False)
correlations=[]
for name,frame,column in [('audience',d,'audience_score_prev'),
                         ('critic',samples['common_rt'],'critic_score_prev'),
                         ('budget',budget,'budget_log_ratio')]:
    correlations.append(dict(variable=name,n=len(frame),franchises=frame.franchise_id.nunique(),
        pearson=stats.pearsonr(frame[column],frame.Y).statistic,
        spearman=stats.spearmanr(frame[column],frame.Y).statistic))
pd.DataFrame(correlations).to_csv(out/'same_sample_statistics.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(10,4))
axes[0].scatter(budget.budget_log_ratio,budget.Y,s=14,alpha=.5)
axes[0].set(xlabel='Budget log ratio',ylabel='Y')
axes[1].hist(budget.budget_log_ratio,bins=25)
axes[1].set(xlabel='Budget log ratio',ylabel='Transitions')
fig.tight_layout()
fig.savefig(out/'budget_review.png',dpi=170)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4))
axes[0].scatter(d.gap_years,diagnostics.residual,s=14,alpha=.5)
axes[0].axhline(0,color='black')
axes[0].set(xlabel='Gap years',ylabel='M1 residual')
stats.probplot(diagnostics.residual,plot=axes[1])
fig.tight_layout()
fig.savefig(out/'M1_residuals.png',dpi=170)
plt.close(fig)
# Gap curves relative to a five-year release interval, with observed support.
quadratic=fit(d,['A10','gap_centered_sq'])
x=np.linspace(d.gap_years.min(),d.gap_years.max(),200)
fig,(curve,histogram)=plt.subplots(2,1,figsize=(8,5.5),sharex=True,height_ratios=[3,1])
for label,result in [('Linear gap',main),('Quadratic gap',quadratic)]:
    b=result['table'].set_index('term').beta
    y=b.gap_years*(x-5)
    if 'gap_centered_sq' in b.index:
        y += b['gap_centered_sq']*((x-d.gap_years.mean())**2-(5-d.gap_years.mean())**2)
    curve.plot(x,y,label=label)
curve.set_ylabel('Difference in Y relative to 5-year gap')
curve.legend()
histogram.hist(d.gap_years,bins=np.arange(0,39,2))
histogram.set(xlabel='Gap years',ylabel='Transitions')
fig.tight_layout()
fig.savefig(out/'gap_comparison.png',dpi=170)
plt.close(fig)
rt=samples['common_rt'][['audience_score_prev','critic_score_prev']]
pd.DataFrame([{
    'n':len(rt),
    'pearson':rt.corr().iloc[0,1],
    'spearman':rt.corr(method='spearman').iloc[0,1]}]).to_csv(
        out/'rt_score_correlation.csv',index=False)
pd.DataFrame([main['meta']]).to_csv(out/'M1_diagnostic_summary.csv',index=False)
