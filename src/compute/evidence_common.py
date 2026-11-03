"""Small helpers for additive versioned investigation products."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(path):return json.loads(Path(path).read_text())
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def mean(values):
    import numpy as np
    a=np.asarray(values);v=a[np.isfinite(a)];return float(v.mean()) if v.size else None
