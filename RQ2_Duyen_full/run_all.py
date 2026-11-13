import argparse
import subprocess
import sys
from pathlib import Path
parser=argparse.ArgumentParser(description='Run RQ2 steps 3 to 8.')
parser.add_argument('--master',required=True,type=Path)
args=parser.parse_args()
master=args.master.resolve()
root=Path(__file__).parent
if not master.is_file():
    parser.error('Master CSV does not exist.')
for step in range(3,9):
    subprocess.run([sys.executable,str(root/f'buoc{step}/run.py'),
                    '--master',str(master)],check=True)
print('Completed steps 3 to 8. Read buoc8/BAO_CAO_RQ2.md for review status.')
