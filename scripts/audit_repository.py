"""Check Git's publication set without printing matched secret contents."""
import argparse,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATTERNS=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b',rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b',rb'\bAKIA[A-Z0-9]{16}\b',rb'(?i)authorization\s*[:=]\s*["\x27]?Bearer\s+[A-Za-z0-9_.-]{25,}']
FORBIDDEN_PREFIXES=('database/','dist/','output/','runtime-downloads/','.venv','.aws/','.ssh/','.codex/','.agents/')
def audit(staged=False):
    command=['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'] if staged else ['git','ls-files','-z']
    names=subprocess.check_output(command,cwd=ROOT).decode().split('\0');findings=[];count=0;total=0
    for name in filter(None,names):
        path=ROOT/name
        if not path.is_file():continue
        count+=1;size=path.stat().st_size;total+=size
        if name.startswith(FORBIDDEN_PREFIXES) or path.name in {'.netrc','.git-credentials','credentials.json'} or (path.name.startswith('.env') and not path.name.endswith('.example')):findings.append({'path':name,'reason':'Machine-local, acquired or secret file'})
        if size>=50*1024**2:findings.append({'path':name,'reason':'Oversized Git file; move to runtime distribution'})
        if path.suffix.lower() in {'.h5','.hdf5','.he5','.tif','.tiff','.npz'} or name.startswith('web/public/cases/') and path.suffix.lower() in {'.png','.webp'}:findings.append({'path':name,'reason':'Acquired/generated runtime binary belongs in release assets'})
        if size<=8*1024**2 and path.suffix.lower() not in {'.png','.webp','.parquet','.zip'}:
            content=path.read_bytes()
            for pattern in PATTERNS:
                if re.search(pattern,content):findings.append({'path':name,'reason':'Potential credential pattern; inspect locally'});break
    result={'status':'PASS' if not findings else 'FAIL','files_checked':count,'total_bytes':total,'findings':findings,'scope':'Current publication set, known credential patterns and large/local files; not a certificate that every possible secret format is absent.'}
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');args=p.parse_args();raise SystemExit(0 if audit(args.staged)['status']=='PASS' else 1)
