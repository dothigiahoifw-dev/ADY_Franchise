import importlib.util, hashlib, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

base=Path('/mnt/data/ady_run_v3_3')
spec=importlib.util.spec_from_file_location('v33','/mnt/data/complete_dp_pipeline_v3_3.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
models=base/'data/analytical/transitions_model_rq1.csv'
core=base/'data/analytical/transitions.csv'
diag=base/'data/analytical/transitions_diagnostic.csv'
rel=base/'reports/film_relationship_labels.csv'
rel_summary=base/'reports/relationship_type_summary.csv'
d=pd.read_csv(diag, low_memory=False); r=pd.read_csv(rel)
with zipfile.ZipFile('/mnt/data/ADY_DP_v3_2_diagnostics_and_attribute_audit.zip') as z:
 for f, p in [('data/analytical/transitions_model_rq1.csv', models), ('data/analytical/transitions.csv',core)]:
  assert z.read(f)==p.read_bytes(), f'previous v3.2 core changed: {f}'
assert len(d)==25943 and d['Y'].notna().sum()==918
assert d['transition_id'].nunique()==len(d)
assert len(r)==39871 and r['film_key'].nunique()==len(r)
assert d.relationship_type_n_status.eq('UNVERIFIED_TITLE_HEURISTIC').all()
assert d['relationship_type_n'].notna().all()
assert 'relationship_type_n' not in pd.read_csv(models, nrows=1).columns
assert pd.read_csv(base/'reports/relationship_type_summary.csv')['valid_transitions'].sum() == len(d)
# Independently verify Y from raw without using pipeline function
raw_open=pd.read_csv('/mnt/data/box_office_detailed(2).csv',dtype={'film_key':str}).set_index('film_key')['opening_weekend_gross']
sub=d[d.Y.notna()]
pd_open=pd.to_numeric(sub.film_key_prev.map(raw_open),errors='coerce').to_numpy()
cr_open=pd.to_numeric(sub.film_key_curr.map(raw_open),errors='coerce').to_numpy()
assert np.allclose(np.log(cr_open)-np.log(pd_open),sub.Y.to_numpy(),atol=1e-12)
# Known-title test corpus: preserve uncertainty when story type unknown
example=pd.DataFrame([
 {'film_key':'a','tmdb_collection_id':'10','title':'Star Wars','release_date_ref':'1977-05-25'},
 {'film_key':'b','tmdb_collection_id':'10','title':'The Empire Strikes Back','release_date_ref':'1980-05-20'},
 {'film_key':'c','tmdb_collection_id':'10','title':'Star Wars: Episode I - The Phantom Menace','release_date_ref':'1999-05-19'},
 {'film_key':'d','tmdb_collection_id':'10','title':'Star Wars: Episode II - Attack of the Clones','release_date_ref':'2002-05-15'},
 {'film_key':'e','tmdb_collection_id':'230','title':'The Godfather','release_date_ref':'1972-03-14'},
 {'film_key':'f','tmdb_collection_id':'230','title':'The Godfather Part II','release_date_ref':'1974-12-20'},
 {'film_key':'g','tmdb_collection_id':'300','title':'Our Movie','release_date_ref':'2000-01-01'},
 {'film_key':'h','tmdb_collection_id':'300','title':'Our Movie Spin-Off: Small Tale','release_date_ref':'2002-01-01'},
 {'film_key':'i','tmdb_collection_id':'400','title':'First Film','release_date_ref':'2000-01-01'},
 {'film_key':'j','tmdb_collection_id':'400','title':'Other Film','release_date_ref':'2000-01-01'},
])
check=m.infer_relationship_labels(example).set_index('film_key')
assert check.loc['f','relationship_type_candidate']=='sequel_candidate'
assert check.loc['d','relationship_type_candidate']=='numbered_installment_unknown_type'
assert check.loc['c','relationship_type_candidate']=='unclassified'
assert check.loc['h','relationship_type_candidate']=='spinoff_candidate'
assert check.loc['j','relationship_type_candidate']=='unclassified'
print('PASS: identical RQ1 and core datasets vs v3.2; Y checked against raw; 39,871 unique labels; 25,943 mapped transitions; title heuristic smoke tests; no RQ1 leakage')
print('types:',pd.read_csv(rel_summary).set_index('relationship_type_n')['pairs_with_opening_Y'].to_dict())
