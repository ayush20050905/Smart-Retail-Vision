import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from retailflow.demo import generate
root=Path(__file__).resolve().parents[1]
print(generate(json.loads((root/'config/store.json').read_text()),root/'data/demo'))
