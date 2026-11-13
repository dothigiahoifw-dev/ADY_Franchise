from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
import numpy as np
root=Path(__file__).parent
with ZipFile(root/'tai_lieu_goc.zip') as z:
    original=pd.read_csv(BytesIO(z.read('task3/results/coefficients_all.csv')))
main=pd.read_csv(root/'buoc6/results/coefficients.csv')
checks=[]
for name,frame in main.groupby('model'):
    reference=original.loc[original.model==name].set_index('term')
    actual=frame.set_index('term')
    for column in ['beta','se_cluster','ci_low','ci_high']:
        np.testing.assert_allclose(actual[column],reference.loc[actual.index,column],atol=1e-10,rtol=1e-10)
    checks.append(f'{name}: coefficients, CR1 SE and CI match original Task 3.')
sensitivity=pd.read_csv(root/'buoc7/results/coefficients.csv')
for name in ['M1_positive_excluding_flags','M1_plus_log_open','M1_gap_quadratic','M1_excluding_Cook_screen']:
    actual=sensitivity.loc[sensitivity.model==name].set_index('term')
    reference=original.loc[original.model==name].set_index('term')
    np.testing.assert_allclose(actual[['beta','se_cluster','ci_low','ci_high']],reference.loc[actual.index,['beta','se_cluster','ci_low','ci_high']],atol=1e-10)
    checks.append(f'{name}: matches original Task 3.')
with ZipFile(root/'tai_lieu_goc.zip') as z:
    reference=pd.read_csv(BytesIO(z.read('task5/results/M2_budget_sensitivity.csv')))
actual=sensitivity.loc[sensitivity.model=='M2_without_budget_IQR'].set_index('term')
reference=reference.loc[reference.model=='M2_without_budget_IQR'].set_index('term')
np.testing.assert_allclose(actual[['beta','se_cluster','ci_low','ci_high']],reference.loc[actual.index,['beta','se_cluster','ci_low','ci_high']],atol=1e-10)
checks.append('M2 budget sensitivity: matches revised Task 5.')
d=pd.read_csv(root/'buoc5/results/principal_input.csv')
assert len(d)==676 and d.franchise_id.nunique()==394
matrix=pd.read_csv(root/'buoc5/results/M1_design.csv')
assert len(matrix)==676 and matrix[['part_3','part_4+']].sum().sum()==303
checks.append('Step 5 input and design: 676 transitions / 394 franchises verified.')
(root/'VALIDATION.txt').write_text('\n'.join(checks)+'\n',encoding='utf-8')
print('\n'.join(checks))
