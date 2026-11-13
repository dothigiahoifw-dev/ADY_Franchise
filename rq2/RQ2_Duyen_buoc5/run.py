import argparse
import hashlib
import json
from pathlib import Path
from common import load_master, basic_specs, design
parser = argparse.ArgumentParser()
parser.add_argument('--master',required=True)
args = parser.parse_args()
out = Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
data, base, samples = load_master(args.master)
columns = ['transition_id','franchise_id','Y','A10','C10','gap_years',
           'part','era','budget_log_ratio','cast_retention_top5',
           'log_open_prev','gap_centered_sq']
for name, frame in samples.items():
    frame[[c for c in columns if c in frame]].to_csv(out/(name+'_input.csv'),index=False)
for name,(frame,terms) in basic_specs(samples).items():
    matrix=design(frame,terms)
    matrix.insert(0,'franchise_id',frame.franchise_id)
    matrix.insert(0,'transition_id',frame.transition_id)
    matrix['Y']=frame.Y
    matrix.to_csv(out/(name+'_design.csv'),index=False)
(out/'metadata.json').write_text(json.dumps({
    'master_sha256':hashlib.sha256(Path(args.master).read_bytes()).hexdigest(),
    'principal_n':len(samples['principal']),
    'principal_franchises':samples['principal'].franchise_id.nunique()},indent=2))
