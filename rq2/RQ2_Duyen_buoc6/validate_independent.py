import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from common import load_master, basic_specs, design
parser = argparse.ArgumentParser()
parser.add_argument('--master', required=True)
args = parser.parse_args()
root = Path(__file__).parent
data, base, samples = load_master(args.master)
stored = pd.read_csv(root/'results/coefficients.csv')
messages = []
for name, (sample, terms) in basic_specs(samples).items():
    matrix = design(sample, terms)
    result = sm.OLS(sample.Y, matrix).fit(
        cov_type='cluster',
        cov_kwds={'groups':sample.franchise_id, 'use_correction':True},
        use_t=True)
    actual = stored.loc[stored.model.eq(name)].set_index('term').loc[matrix.columns]
    np.testing.assert_allclose(actual.beta, result.params, atol=1e-10)
    np.testing.assert_allclose(actual.se_cluster, result.bse, atol=1e-10)
    np.testing.assert_allclose(actual[['ci_low','ci_high']], result.conf_int(), atol=1e-10)
    messages.append(name + ': PASS independent statsmodels coefficient/CR1 SE/CI comparison.')
(root/'results/independent_validation.txt').write_text('\n'.join(messages)+'\n')
print('\n'.join(messages))
