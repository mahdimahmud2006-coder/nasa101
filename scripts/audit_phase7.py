"""Socket-free runtime rehearsal and scoped accessibility source checks; not browser QA."""
import io,json,re,socket,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.api.app import Handler

class QuietHandler(Handler):
    def log_message(self,*args):pass
class Connection:
    def __init__(self,path,body=None):
        b=json.dumps(body).encode() if body is not None else b'';verb='POST' if body is not None else 'GET'
        self.input=io.BytesIO((f'{verb} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(b)}\r\n\r\n').encode()+b);self.output=bytearray()
    def makefile(self,*a,**k):return self.input
    def sendall(self,data):self.output.extend(data)
def request(path,body=None):
    c=Connection(path,body);QuietHandler(c,('127.0.0.1',1),SimpleNamespace(server_name='localhost',server_port=8000))
    head,body=bytes(c.output).split(b'\r\n\r\n',1);return int(head.split()[1]),body

class Page(HTMLParser):
    def __init__(self):super().__init__();self.assets=[];self.controls=[];self.labels=set();self.label_depth=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='label':self.label_depth+=1;self.labels.add(a.get('for'))
        if tag=='script' and a.get('src'):self.assets.append(a['src'])
        if tag=='link' and a.get('rel')=='stylesheet':self.assets.append(a['href'])
        if tag in ['input','select','textarea']:self.controls.append((a.get('id'),bool(self.label_depth or a.get('aria-label') or a.get('aria-labelledby'))))
    def handle_endtag(self,tag):
        if tag=='label':self.label_depth-=1

def contrast(a,b):
    def lum(color):
        rgb=[int(color[i:i+2],16)/255 for i in [1,3,5]]
        return sum(v*w for v,w in zip([c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb],[.2126,.7152,.0722]))
    x,y=sorted([lum(a),lum(b)]);return (y+.05)/(x+.05)

def audit():
    paths=set();pages={}
    for name in ['index','investigations','change-lab','timeseries','comparison']:
        text=(ROOT/f'web/{name}.html').read_text();p=Page();p.feed(text)
        missing=[id for id,labelled in p.controls if not labelled and id not in p.labels]
        assert not missing,(name,missing)
        assert 'workspace-rail' in text and 'tp-skip' in text and 'aria-live="polite"' in text
        pages[name]={'form_controls_with_source_labels':len(p.controls),'missing_form_labels':missing,'shared_navigation':True,'live_region_present':True}
        paths.add('/' if name=='index' else '/'+name+'.html');paths.update(p.assets)
    # Imported modules are served locally too. This is source inspection, not observed browser traffic.
    for path in (ROOT/'web').glob('*'):
        if path.suffix in ['.mjs','.js','.css']:
            paths.add('/'+path.name);text=path.read_text()
            assert not re.search(r'(?:fetch\(|from\s+|import\s*)[\s\'\"]*https?://',text),'External runtime import/fetch: '+path.name
    paths.update(['/api/project','/api/claims','/api/investigations','/cases/time-axis-v1/calendars.json','/cases/interferometry-v2.json'])
    # Include the active version's sidecars, not just the frozen original manifests.
    from src.compute.active_records import registry_path,case_directory
    paths.add('/cases/'+registry_path(ROOT).name)
    for row in json.loads(registry_path(ROOT).read_text())['cases']:
        if row.get('record_base'):
            base=row['record_base'];paths.update(base+'/'+name for name in ['investigation/manifest.json','dualpol-v1/manifest.json','dualpol-v1/sensitivity.json','context-v2/manifest.json','evidence-v2/manifest.json','references-v1/manifest.json','calendar.json'])
    for case in ['nepal_surface','nepal_impact_corridor','jamuna_river','tanguar_wetland']:
        paths.add(f'/cases/{case}/references-v1/manifest.json');paths.add(f'/cases/{case}/evidence-v2/manifest.json')
    checked=[]
    def denied(*a,**k):raise AssertionError('Network forbidden in offline rehearsal')
    with patch.object(socket,'socket',denied),patch.object(socket,'create_connection',denied),patch.object(socket,'getaddrinfo',denied):
        for path in sorted(paths):
            status,body=request(path);assert status==200,(path,status);assert body
            checked.append({'path':path,'status':status,'bytes':len(body)})
        # Include the active version's sidecars, not just the frozen original manifests.
    from src.compute.active_records import registry_path,case_directory
    paths.add('/cases/'+registry_path(ROOT).name)
    for row in json.loads(registry_path(ROOT).read_text())['cases']:
        if row.get('record_base'):
            base=row['record_base'];paths.update(base+'/'+name for name in ['investigation/manifest.json','dualpol-v1/manifest.json','dualpol-v1/sensitivity.json','context-v2/manifest.json','evidence-v2/manifest.json','references-v1/manifest.json','calendar.json'])
    for case in ['nepal_surface','nepal_impact_corridor','jamuna_river','tanguar_wetland']:
            path=f'/api/cases/{case}/investigation-polygon';status,body=request(path,{'vertices':[[900,900],[911,900],[911,911],[900,911]]})
            assert status==200;assert json.loads(body)['dna']['coherence'] is None;checked.append({'path':path,'status':status,'method':'POST'})
    colors=[('#d9e9ee','#101e29'),('#0b2527','#87e4d4'),('#e5eff1','#142a34'),('#a7bbc6','#111c26')]
    ratios=[{'foreground':a,'background':b,'ratio':contrast(a,b)} for a,b in colors];assert all(r['ratio']>=4.5 for r in ratios)
    css=(ROOT/'web/workspace-shell.css').read_text();assert ':focus-visible' in css and 'prefers-reduced-motion' in css
    return {'status':'SCOPED_SOURCE_AND_NETWORK_DENIED_HANDLER_CHECKS_PASS','pages':pages,'requests':checked,'new_theme_text_contrast_pairs':ratios,
            'network_policy':'Python socket creation and DNS denied during handler requests; no external request permitted.',
            'browser_visual_keyboard_accessibility_gpu':'UNVERIFIED: prior browser local-URL policy block; no workaround attempted.',
            'physical_wifi_ethernet_disconnect':'PENDING_USER_REHEARSAL','whole_app_wcag_conformance':'NOT_ESTABLISHED',
            'scope':'Native form-label source coverage, four theme color pairs, local source delivery and representative local reasoning. Not rendered layout, full assistive-technology testing or browser network observation.'}

if __name__=='__main__':print(json.dumps(audit(),indent=2))
