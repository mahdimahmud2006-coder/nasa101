"""Preserve current artifacts around the existing report-writing verification command."""
from pathlib import Path
import hashlib,json,subprocess,shutil
root=Path.cwd();phase=root/'reports/phase3_2026_11_02/after'
roots=['data/derived','web/public','docs/reports','dist']
paths=sorted({p for folder in roots for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}|{p for p in (root/'docs').iterdir() if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.svg','.pdf','.webp'}})
digest=lambda p: hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
before={str(p.relative_to(root)):digest(p) for p in paths}
backup=Path('/tmp/terrapulse-phase3-after-backup');backup.mkdir(exist_ok=True)
# Existing validators regenerate these reports and figures, including hardware-dependent timings.
for p in paths:
 if str(p.relative_to(root)).startswith('docs/reports/'):
  q=backup/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
(phase/'preverify_outputs.json').write_text(json.dumps(before,indent=2)+'\n')
with (phase/'make_verify.log').open('w') as stream:
 result=subprocess.run(['make','verify'],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
changes=[]
for filename,old in before.items():
 p=root/filename
 if not p.exists() or digest(p)!=old:
  row={'path':filename,'before_sha256':old,'verification_sha256':digest(p) if p.exists() else None}
  saved=backup/filename
  if saved.is_file():
   out=phase/'validator_generated'/filename;out.parent.mkdir(parents=True,exist_ok=True)
   if p.exists():shutil.copy2(p,out)
   shutil.copy2(saved,p);row['historical_bytes_restored']=True
  else:row['historical_bytes_restored']=False
  changes.append(row)
after_mismatches=[name for name,old in before.items() if not (root/name).is_file() or digest(root/name)!=old]
summary={'command':'make verify','exit_code':result.returncode,'preexisting_output_files':len(before),'validator_report_changes':changes,'all_preexisting_outputs_preserved':not after_mismatches,'remaining_mismatches':after_mismatches,'note':'Current validation output is retained in make_verify.log. Existing validators may rewrite timing reports; changed generated reports are saved in this phase evidence directory and original historical bytes restored. No failed validator is reclassified as passing.'}
(phase/'verification_preservation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
raise SystemExit(result.returncode if result.returncode else (1 if after_mismatches else 0))
