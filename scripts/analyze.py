import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from retailflow.video import analyze_video
p=argparse.ArgumentParser(description='Analyze one local video and export Tableau data.')
p.add_argument('video'); p.add_argument('--config',default='config/store.json')
p.add_argument('--output',default='outputs/cli_run'); p.add_argument('--start',required=True)
p.add_argument('--model',default='yolo11n.pt'); p.add_argument('--device',default='cpu')
p.add_argument('--seconds',type=int,default=300); p.add_argument('--no-video',action='store_true')
a=p.parse_args()
if Path(a.output).exists(): p.error('Output already exists; choose a new folder to preserve previous runs.')
analyze_video(a.video,json.loads(Path(a.config).read_text()),a.output,a.start,a.model,device=a.device,max_seconds=a.seconds,save_video=not a.no_video)
print('Results:',a.output)
