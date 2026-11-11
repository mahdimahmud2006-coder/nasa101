"""Check what Git will publish without printing matched secret contents."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATTERNS=(
    rb'-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----',
    rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b',
    rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b',
    rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    rb'(?i)authorization\s*[:=]\s*["\x27]?Bearer\s+[A-Za-z0-9_.-]{25,}',
    rb'\bsk-(?:proj-|svcacct-)[A-Za-z0-9_-]{30,}\b',
)


def audit(staged=False):
    entries=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)
    changed=None
    if staged:
        changed=set(subprocess.check_output(
            ['git','diff','--cached','--name-only','--diff-filter=ACMRT','-z'],cwd=ROOT).split(b'\0'))
    files=[]
    for row in filter(None,entries.split(b'\0')):
        spec,name=row.split(b'\t',1)
        if changed is None or name in changed:
            mode,oid,stage=spec.split()
            if stage!=b'0':
                raise ValueError('Resolve the index conflicts before auditing')
            files.append((name,mode,oid))
    names=b''.join(name+b'\0' for name,_,_ in files)
    ignored=subprocess.run(['git','check-ignore','--no-index','--stdin','-z'],cwd=ROOT,
        input=names,stdout=subprocess.PIPE,check=False)
    if ignored.returncode not in (0,1):
        raise RuntimeError('Git could not check the ignore rules')
    ignored_names=set(ignored.stdout.split(b'\0'))
    findings=[]
    blobs=[]
    for name,mode,oid in files:
        path=os.fsdecode(name)
        if name in ignored_names:
            findings.append({'path':path,'reason':'Tracked path matches .gitignore'})
        if mode not in (b'100644',b'100755'):
            findings.append({'path':path,'reason':'Unexpected file type in publication set'})
        else:
            blobs.append((path,oid))
    objects=b''.join(oid+b'\n' for _,oid in blobs)
    sizes=subprocess.check_output(['git','cat-file','--batch-check=%(objectsize)'],input=objects,cwd=ROOT)
    total=0
    for (path,oid),raw_size in zip(blobs,sizes.splitlines(),strict=True):
        size=int(raw_size)
        total+=size
        if size>=50*1024**2:
            findings.append({'path':path,'reason':'Oversized Git file; move to runtime distribution'})
        elif Path(path).suffix.lower() not in {'.parquet','.zip','.woff2'}:
            content=subprocess.check_output(['git','cat-file','blob',oid.decode('ascii')],cwd=ROOT)
            if any(re.search(pattern,content) for pattern in PATTERNS):
                findings.append({'path':path,'reason':'Potential credential pattern; inspect locally'})
    result={'status':'PASS' if not findings else 'FAIL','files_checked':len(files),'total_bytes':total,
            'findings':findings,'scope':'Git index, known credential patterns, ignored paths and oversized files.'}
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');args=p.parse_args();raise SystemExit(0 if audit(args.staged)['status']=='PASS' else 1)
