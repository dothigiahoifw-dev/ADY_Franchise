import argparse
from pathlib import Path
from common import load_master, basic_specs, fit, pd, np, plt
parser=argparse.ArgumentParser()
parser.add_argument('--master',required=True)
args=parser.parse_args()
out=Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
data,base,samples=load_master(args.master)
rows=[]
for name,(frame,terms) in basic_specs(samples).items():
    result=fit(frame,terms)
    term='C10' if name=='M1-C' else 'A10'
    if term not in result['table'].term.values:
        continue
    row=result['table'].set_index('term').loc[term].to_dict()
    row.update(model=name,n=len(frame),franchises=frame.franchise_id.nunique())
    rows.append(row)
table=pd.DataFrame(rows)
table['ratio_change_percent']=100*np.expm1(table.beta)
table['ratio_low_percent']=100*np.expm1(table.ci_low)
table['ratio_high_percent']=100*np.expm1(table.ci_high)
table.to_csv(out/'final_audience_critic_table.csv',index=False)
audience=table.loc[table.model!='M1-C']
fig,ax=plt.subplots(figsize=(8,4))
positions=np.arange(len(audience))
ax.errorbar(audience.beta,positions,
 xerr=np.vstack([audience.beta-audience.ci_low,audience.ci_high-audience.beta]),
 fmt='o',capsize=4)
ax.set_yticks(positions,audience.model)
ax.axvline(0,color='gray')
ax.set_xlabel('Audience coefficient per 10 points, 95% franchise-cluster CI')
fig.tight_layout()
fig.savefig(out/'final_coefficients.png',dpi=170)
plt.close(fig)
(out/'handoff_status.txt').write_text(
    'Modeling ready for review. Pending statistics-step-3 comparison, '
    'peer review and cast-retention definition verification.\n')
