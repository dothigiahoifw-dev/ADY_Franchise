import argparse
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np
from scipy import stats
from rq2_task3 import fit, plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('master', type=Path)
    parser.add_argument('--task3-results', type=Path, required=True)
    args = parser.parse_args()
    out = Path(__file__).parent / 'results'
    out.mkdir(exist_ok=True)
    fingerprint = hashlib.sha256(args.master.read_bytes()).hexdigest()
    assert fingerprint == json.loads((args.task3_results/'run_metadata.json').read_text())['input_sha256']
    data = pd.read_csv(args.master, low_memory=False).set_index('transition_id', drop=False)
    def sample(name):
        ids = pd.read_csv(args.task3_results / f'{name}_sample.csv')
        return data.loc[ids.transition_id].copy()
    d = sample('M1')
    def prepare(frame):
        frame['A10'] = frame.audience_score_prev / 10
        frame['part'] = np.select([frame.franchise_position_n.eq(2),frame.franchise_position_n.eq(3)],['2','3'],default='4+')
        frame['era'] = pd.cut(frame.release_year_n,[-np.inf,1989,1999,2009,2019,np.inf],labels=['pre1990','1990-1999','2000-2009','2010-2019','2020+'])
        frame['gap_sq'] = (frame.gap_years - d.gap_years.mean())**2
        return frame
    prepare(d)
    diag = pd.read_csv(args.task3_results/'M1_influence_screen.csv')
    audit = diag.merge(d.reset_index(drop=True)[['transition_id','gap_years','open_prev','open_curr','opening_inconsistent','Y','audience_score_prev']],on='transition_id',validate='one_to_one')
    audit.to_csv(out/'influence_review.csv',index=False)
    rows=[]; vifs=[]; all_terms=[]
    specs = {'M1':(d,['A10']), 'M1_quadratic':(d,['A10','gap_sq']),
             'M2':(prepare(sample('M2')),['A10','budget_log_ratio']),
             'M3':(prepare(sample('M3')),['A10','cast_retention_top5'])}
    for label, subset in [('gap_le_20',d[d.gap_years<=20]),('without_Cook',d[~d.transition_id.isin(diag.loc[diag.cooks_d>4/len(d),'transition_id'])])]:
        specs[label]=(subset,['A10'])
        specs[label+'_quadratic']=(subset,['A10','gap_sq'])
    fits={}
    for name,(frame,terms) in specs.items():
        result=fit(frame,terms)
        fits[name]=result
        table=result['table']
        all_terms.append(table.assign(model=name))
        audience=table.set_index('term').loc['A10'].to_dict()
        gap=table.set_index('term').loc['gap_sq'].to_dict() if 'gap_sq' in terms else {}
        rows.append(dict(model=name, **result['meta'], **audience,
                         gap_sq=gap.get('beta'), gap_low=gap.get('ci_low'), gap_high=gap.get('ci_high')))
        vifs.append(result['vif'].assign(model=name))
    summary=pd.DataFrame(rows)
    summary.to_csv(out/'task4_models.csv',index=False)
    pd.concat(all_terms).to_csv(out/'task4_coefficients.csv',index=False)
    vif=pd.concat(vifs)
    vif.to_csv(out/'vif.csv',index=False)
    rt=sample('M1_common_RT')
    comparisons=[]
    for name,frame,var in [('audience',d,'audience_score_prev'),('audience_common_RT',rt,'audience_score_prev'),('critic',rt,'critic_score_prev'),('budget',sample('M2'),'budget_log_ratio')]:
        comparisons.append(dict(variable=name,n=len(frame),franchises=frame.franchise_id.nunique(),pearson=stats.pearsonr(frame[var],frame.Y).statistic,spearman=stats.spearmanr(frame[var],frame.Y).statistic))
    pd.DataFrame(comparisons).to_csv(out/'same_sample_statistics.csv',index=False)
    rt_pair=rt[['audience_score_prev','critic_score_prev']]
    metadata=dict(master_sha256=fingerprint, rt_n=len(rt),rt_pearson=rt_pair.corr().iloc[0,1],rt_spearman=rt_pair.corr(method='spearman').iloc[0,1],gap_gt20=int((d.gap_years>20).sum()),gap_gt25=int((d.gap_years>25).sum()),screen_n=len(audit),screen_opening_flags=int(audit.opening_inconsistent.sum()),max_Y_error=float(abs(audit.Y-np.log(audit.open_curr/audit.open_prev)).max()))
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
    fig, (ax,hist)=plt.subplots(2,1,sharex=True,figsize=(8,5.5),height_ratios=[3,1])
    x=np.linspace(d.gap_years.min(),d.gap_years.max(),200)
    for name,label in [('M1','Gap tuyến tính'),('M1_quadratic','Gap bậc hai')]:
        b=fits[name]['table'].set_index('term').beta
        y=b.gap_years*(x-5)+b.get('gap_sq',0)*((x-d.gap_years.mean())**2-(5-d.gap_years.mean())**2)
        ax.plot(x,y,label=label)
    ax.axhline(0,color='gray',lw=.8)
    ax.set_ylabel('Chênh lệch Y so với gap 5 năm')
    ax.legend()
    hist.hist(d.gap_years,bins=np.arange(0,39,2),color='#2867a1')
    hist.set(xlabel='Khoảng cách phát hành (năm)',ylabel='Số cặp')
    fig.tight_layout()
    fig.savefig(out/'gap_comparison.png',dpi=170)
    print(summary[['model','n','franchises','beta','ci_low','ci_high','r2','gap_sq','gap_low','gap_high']].to_string(index=False))
    print(vif.groupby('model').vif.max())
    print(metadata)
    print(pd.DataFrame(comparisons).to_string(index=False))

if __name__=='__main__':
    main()
