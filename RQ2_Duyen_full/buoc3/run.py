import argparse
from pathlib import Path
from common import load_master, pd, np
parser = argparse.ArgumentParser()
parser.add_argument('--master', required=True)
args = parser.parse_args()
out = Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
data, base, samples = load_master(args.master)
overview = []
for name, frame in [('master', data), ('base', base), *samples.items()]:
    overview.append(dict(sample=name, transitions=len(frame),
                         franchises=frame.franchise_id.nunique()))
pd.DataFrame(overview).to_csv(out/'sample_overview.csv', index=False)
variables = ['Y', 'audience_score_prev', 'critic_score_prev', 'gap_years',
             'franchise_position_n', 'release_year_n', 'budget_log_ratio', 'cast_retention_top5']
coverage = pd.DataFrame({'variable':variables,
    'nonmissing_in_base':[base[c].notna().sum() for c in variables]})
coverage['base_n'] = len(base)
coverage.to_csv(out/'coverage.csv',index=False)
samples['principal'][variables].describe().to_csv(out/'principal_descriptive.csv')
for name, frame in samples.items():
    frame[['transition_id','franchise_id']].to_csv(out/(name+'_ids.csv'),index=False)
