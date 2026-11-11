"""Generate README and application claims from the YAML 1.2 JSON-subset ledger."""
import argparse,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.compute.evidence_common import load,save,sha

def block(ledger):
    return '\n\n'.join(f"- **{c['id']} · {c['status']}** — {c['text']} Limitation: {c['limitation']}" for c in ledger['claims'])
def check_numeric_text(text,ledger):
    allowed={float(v) for c in ledger['claims'] for v in c.get('values',[])}
    # Version numbers, code, routes, dates and configuration identifiers are not result prose.
    text=re.sub(r'```.*?```','',text,flags=re.S)
    for match in re.finditer(r'([+−-]?\d+(?:\.\d+)?)\s*(?:km²|dB|hectares?|pixels|Python tests|JavaScript tests)\b',text):
        value=float(match.group(1).replace('−','-'))
        if value not in allowed:raise ValueError('Numeric result absent from ledger: '+match.group(0))
def generate(version=None,check=False):
    version=version or load(ROOT/'config.claims.json')['snapshot_version']
    ledger=load(ROOT/'claims/claims.yaml');assert len({c['id'] for c in ledger['claims']})==len(ledger['claims'])
    for c in ledger['claims']:
        if c['status'] not in ['implemented','measured','hypothesized','planned']:raise ValueError('Unknown claim status')
        if not (ROOT/c['evidence_path']).exists():raise ValueError('Missing claim evidence '+c['id'])
    readme=ROOT/'README.md';text=readme.read_text();start='<!-- CLAIMS:START -->';end='<!-- CLAIMS:END -->';rendered=start+'\n'+block(ledger)+'\n'+end
    expected=text[:text.index(start)]+rendered+text[text.index(end)+len(end):]
    if check:
        if text!=expected:raise ValueError('README claims differ from ledger')
        check_numeric_text(text,ledger)
        public=load(ROOT/f'web/public/cases/{version}.json')
        if public['claims']!=ledger['claims']:raise ValueError('App claims differ from ledger')
    else:
        public=ROOT/f'web/public/cases/{version}.json'
        if public.exists():raise FileExistsError('Choose a new claim snapshot version')
        readme.write_text(expected);save(public,{'schema_version':1,'ledger_sha256':sha(ROOT/'claims/claims.yaml'),'claims':ledger['claims']})
    return {'status':'CLAIMS_MATCH','claims':len(ledger['claims']),'version':version}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default=None);parser.add_argument('--check',action='store_true');a=parser.parse_args();print(generate(a.version,a.check))
