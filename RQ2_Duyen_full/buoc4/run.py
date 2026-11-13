import json
from pathlib import Path
out = Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
config = {
 'target':'ln(open_curr/open_prev)', 'estimator':'OLS',
 'covariance':'CR1 franchise_id, correction G/(G-1)*(N-1)/(N-K), t(G-1)',
 'opening_threshold':1000000,
 'part_groups':['2','3','4+'], 'part_reference':'2',
 'era_groups':['pre1990','1990-1999','2000-2009','2010-2019','2020+'],
 'era_reference':'2010-2019',
 'missing':'complete cases for each specification',
 'models':{'M0':['gap_years','part','era'],
           'M1':['gap_years','part','era','A10'],
           'M2':['gap_years','part','era','A10','budget_log_ratio'],
           'M3':['gap_years','part','era','A10','cast_retention_top5'],
           'M1-C':['gap_years','part','era','C10']},
 'selected':'M1; quadratic gap retained as sensitivity',
 'reason':'Audience association is stable across gap forms; focus on conditional audience association.',
 'pending':['cast retention formula verification','statistics step 3 comparison','peer review']}
(out/'analysis_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
