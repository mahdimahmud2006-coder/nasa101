import io,json
from types import SimpleNamespace
from pathlib import Path
import pytest
from src.api import app
from scripts.generate_claims import generate,check_numeric_text
class Connection:
    def __init__(self,path,payload=None):
        body=json.dumps(payload).encode() if payload is not None else b'';verb='POST' if payload is not None else 'GET'
        self.input=io.BytesIO((f'{verb} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n').encode()+body);self.output=bytearray()
    def makefile(self,*a,**k):return self.input
    def sendall(self,b):self.output.extend(b)
def request(path,payload=None):
    c=Connection(path,payload);app.Handler(c,('127.0.0.1',1),SimpleNamespace(server_name='localhost',server_port=8000));head,body=bytes(c.output).split(b'\r\n\r\n',1);return int(head.split()[1]),json.loads(body)
def test_generated_claims_and_reject_new_numeric_result():
    assert generate(check=True)['status']=='CLAIMS_MATCH'
    ledger=json.loads(Path('claims/claims.yaml').read_text())
    with pytest.raises(ValueError,match='absent'):check_numeric_text('We measured 999999 km² of change.',ledger)
    check_numeric_text(Path('README.md').read_text(),ledger)
def test_app_numeric_result_literals_covered_by_ledger():
    ledger=json.loads(Path('claims/claims.yaml').read_text())
    for pattern in ['*.html','*.mjs','*.js']:
        for p in Path('web').glob(pattern):check_numeric_text(p.read_text(),ledger)
def test_local_claims_and_point_reasoning_have_no_probabilities():
    status,claims=request('/api/claims');assert status==200 and claims['claims']
    status,r=request('/api/cases/nepal_surface/investigation-reasoning?row=1200&col=1200');assert status==200
    assert r['dna']['coherence'] is None;assert len(r['explanations'][0]['hypotheses'])==6;assert r['explanations'][0]['probabilities'] is None
def test_polygon_runtime_uses_fixed_native_pixels_and_rejects_bad_shape():
    status,r=request('/api/cases/jamuna_river/investigation-polygon',{'vertices':[[900,900],[911,900],[911,911],[900,911]]});assert status==200
    assert r['profile']['footprint_pixels']==121 and len(r['profile']['observations'])==10
    status,_=request('/api/cases/jamuna_river/investigation-polygon',{'vertices':[[-1,0],[1,0],[1,1]]});assert status==422
