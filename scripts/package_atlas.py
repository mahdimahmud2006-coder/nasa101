"""Assemble the offline atlas from checked-in web assets; standard library only."""
import hashlib
import json
import re
from base64 import b64encode
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def bundle_atlas_controller(web, portable=False):
    """Inline the atlas' named relative imports for the self-contained edition."""
    modules=[]
    visiting=set()
    done=set()
    dependency=re.compile(r"^(?:import|export) \{[^\n]+\} from '\./(atlas[-\w]*\.mjs)';[ \t]*$",re.M)
    def visit(name):
        if name in done:return
        if name in visiting:raise ValueError('Circular atlas module dependency')
        visiting.add(name)
        source=(web/name).read_text()
        if portable and name=='atlas.mjs':
            source=source.replace("import {createAtlasLabs} from './atlas-labs.mjs';",
                'const createAtlasLabs=()=>({update(){},pick:()=>false,overlay:()=>null});')
        for ref in dependency.findall(source):visit(ref)
        source=dependency.sub('',source)
        if re.search(r'^import\s',source,re.M):raise ValueError('Unexpected atlas import')
        modules.append(source)
        visiting.remove(name);done.add(name)
    visit('atlas.mjs')
    return '\n'.join(modules)

def package(root=ROOT):
    web=root/'web'
    source=(web/'index.html').read_text()
    if source.count('<!-- atlas:start -->')!=1 or source.count('<!-- atlas:end -->')!=1:raise ValueError('Expected one investigation workspace')
    body=source.split('<!-- atlas:start -->')[1].split('<!-- atlas:end -->')[0]
    body=re.sub(r'<!-- labs:only -->.*?<!-- labs:end -->|<!-- local:only -->.*?<!-- local:end -->','',body,flags=re.S)
    body=body.replace('href="/guide.html"','href="#atlas-guide-reference"').replace('href="./"','href="#atlas"')
    data=(web/'atlas-record.json').read_text().replace('<','\\u003c')
    identity=json.dumps(json.loads((web/'atlas-contract-records.json').read_text()),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    notebook=b64encode((web/'atlas-replay.ipynb').read_bytes()).decode()
    body=body.replace('href="/atlas-replay.ipynb"',f'href="data:application/x-ipynb+json;base64,{notebook}"')
    controller=bundle_atlas_controller(web, portable=True)
    if '</script' in controller.lower():raise ValueError('Unsafe inline script terminator')
    style=re.sub(r'/\* simulations-workspace:start \*/.*?/\* simulations-workspace:end \*/','',(web/'atlas.css').read_text(),flags=re.S)
    fonts=(web/'fonts.css').read_text()
    for font in ('source-sans-3','jetbrains-mono'):
        payload=b64encode((web/f'fonts/{font}.woff2').read_bytes()).decode()
        fonts=fonts.replace(f'./fonts/{font}.woff2','data:font/woff2;base64,'+payload)
    style=(web/'tokens.css').read_text()+fonts+style+(web/'atlas-ui.css').read_text()
    target=root/'output/atlas/TerraPulse.html';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TerraPulse · Investigation atlas</title><style>body{margin:0;background:var(--tp-ink-0)}'+style+'</style><body data-portable="yes"><main>'+body+'</main><script type="application/json" id="atlas-data">'+data+'</script><script type="application/json" id="atlas-identity">'+identity+'</script><script type="module">'+controller+'</script></body></html>')
    receipt={'file':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
             'data_sha256':hashlib.sha256(data.encode()).hexdigest(),'identity_sha256':hashlib.sha256(identity.encode()).hexdigest(),'edition':'Offline atlas; saved footprints, no local API or network required.'}
    (target.parent/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt));return target
if __name__=='__main__':package()
