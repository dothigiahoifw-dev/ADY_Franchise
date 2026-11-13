import argparse
from pathlib import Path
from common import load_master, basic_specs, export_models
parser=argparse.ArgumentParser()
parser.add_argument('--master',required=True)
args=parser.parse_args()
out=Path(__file__).parent/'results'
out.mkdir(exist_ok=True)
data,base,samples=load_master(args.master)
export_models(basic_specs(samples),out)
(out/'model_decision.txt').write_text(
    'Chọn M1 cho liên hệ khán giả. So M1 ngân sách và M2 trên cùng mẫu. '
    'M2/M3 và M1-C bổ trợ. Gap bậc hai được kiểm tra ở bước 7.\n'
    'Xem BAO_CAO_RQ2.md bước 8 để đọc lý do và giới hạn.',encoding='utf-8')
