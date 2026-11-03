#!/usr/bin/env python3
"""Publish saved search metadata as a new local-only UI sidecar, never rerun science."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def publish(source,destination):
    files=['calendars.json','nepal_098_016.json','bangladesh_069_014.json']
    if destination.exists():
        raise FileExistsError('Choose a new sidecar destination; existing products cannot be replaced')
    bundle=json.loads((source/'calendars.json').read_text())
    for calendar in bundle['series'].values():
        for q in calendar['queries']:
            if 'response_path' in q:
                path=ROOT/q['response_path']
                if hashlib.sha256(path.read_bytes()).hexdigest()!=q['response_sha256']:
                    raise ValueError('Source query checksum mismatch')
        loaded=[s['observed_timestamp'] for s in calendar['slots'] if s['status']=='observed']
        for case in calendar['case_ids']:
            m=json.loads((ROOT/f'web/public/cases/{case}/investigation/manifest.json').read_text())
            if loaded!=[o['timestamp'] for o in m['observations']]:
                raise ValueError('Calendar is stale for '+case)
    destination.mkdir(parents=True)
    for name in files:shutil.copyfile(source/name,destination/name)
    print('Published',destination)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'data/candidates/phase1_2026_11_02_final')
    parser.add_argument('--destination',type=Path,default=ROOT/'web/public/cases/time-axis-v1')
    args=parser.parse_args();publish(args.source,args.destination)
