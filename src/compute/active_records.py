"""Resolve the explicitly activated local record; historical products stay addressable."""
import re
from pathlib import Path
from src.compute.evidence_common import ROOT,load

def registry_path(root=ROOT):
    root=Path(root); pointer=root/'config.records.json'
    name=load(pointer).get('investigation_registry','investigations.json') if pointer.exists() else 'investigations.json'
    if not re.fullmatch(r'[a-zA-Z0-9_-]+\.json',name):raise ValueError('Invalid investigation registry')
    return root/'web/public/cases'/name

def case_directory(case,root=ROOT):
    root=Path(root)
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',case):raise ValueError('Invalid case')
    pointer=root/'config.records.json';version=load(pointer).get('cases',{}).get(case) if pointer.exists() else None
    base=root/'web/public/cases'/case
    if version is not None:
        if not isinstance(version,str) or not re.fullmatch(r'[a-zA-Z0-9_-]+',version):raise ValueError('Invalid record version')
        base=base/version
    return base
