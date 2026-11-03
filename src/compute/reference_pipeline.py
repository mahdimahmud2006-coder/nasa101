"""Publish the frozen descriptive HLS evaluation without changing earlier products."""
import shutil
from affine import Affine
from pyproj import Transformer
from src.compute.evidence_common import ROOT, load, save, sha
from src.compute.investigation_dna import polygon_evidence

def run():
    freeze=load(ROOT/'reference/freeze_manifest.json')
    assert all(sha(ROOT/p)==h for p,h in freeze['sha256'].items())
    source=ROOT/'data/references/v1/hls-v2'
    results=load(source/'results.json'); sources=load(source/'sources.json')
    assert results['design_sha256']==sha(ROOT/'reference/design.json')
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in sources['items'])
    footprints=load(ROOT/'reference/frozen_footprints.geojson')['features']
    summaries={}
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        output=ROOT/f'web/public/cases/{case}/references-v1'
        if output.exists(): raise FileExistsError(output)
        output.mkdir()
        rows=[]; profiles=[]
        for record in results['results']:
            if record['case_id']!=case: continue
            record=dict(record)
            # Catalog time matching with zero eligible pixels is not evidence.
            record['reference_status']='date-matched, descriptive' if record.get('clear_assessable_pixels',0)>0 else 'none'
            if record.get('thumbnail'):
                p=ROOT/record['thumbnail']; shutil.copy2(p,output/p.name)
                record['thumbnail']='/cases/'+case+'/references-v1/'+p.name
                record['thumbnail_sha256']=sha(p)
            record['scope']='Only this frozen footprint at this observed visit; not the entire crop or a user-selected polygon.'
            rows.append(record)
        m=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json')
        transformer=Transformer.from_crs('EPSG:4326',m['grid']['crs'],always_xy=True)
        inverse=~Affine(*m['grid']['affine'])
        for feature in footprints:
            props=feature['properties']
            if props['case_id']!=case: continue
            vertices=[list(inverse*transformer.transform(*p)) for p in feature['geometry']['coordinates'][0][:-1]]
            evidence=polygon_evidence(case,vertices)
            evidence['profile']['label']='Frozen reference: '+props['role'].replace('_',' ')
            evidence['profile']['selection']='Frozen before new reference inspection; role labels are not verified event/stability truth.'
            evidence['reference_footprint_id']=props['id']
            evidence['reference_status']='none'  # Computed per selected visit in the client/export.
            evidence['reference_design_sha256']=results['design_sha256']
            profiles.append(evidence)
        bundle={'schema_version':1,'case_id':case,'claim_status':'measured','freeze_commit':results['freeze_commit'],
                'design':load(ROOT/'reference/design.json'),'design_sha256':results['design_sha256'],
                'source_results_sha256':sha(source/'results.json'),'source_manifest_sha256':sha(source/'sources.json'),
                'radar_manifest_sha256':sha(ROOT/f'web/public/cases/{case}/investigation/manifest.json'),
                'rules_sha256':sha(ROOT/'rules/explanations.yaml'),'profiles':profiles,'results':rows,
                'reference_definition':'HLS Fmask water on eligible optical pixels; independent algorithmic context, not OPERA DSWx or ground truth.',
                'qa_policy':'Exclude fill, cloud, cloud adjacency, shadow, snow and cirrus/reserved low bits; aerosol bits are retained, not a separate exclusion.',
                'limitations':['Geographic comparison roles are not independently verified stable/unaffected labels.',
                  'No accuracy metrics or physical cause are inferred; no threshold tuning after reference inspection.',
                  'Only clear reference pixel centers with finite nearest-grid HH/HV enter overlap; partial coverage is explicit.',
                  'Native radar footprint means and reference-grid overlap use different sampling grids.',
                  'OPERA DSWx and DIST catalogs are screened only; no OPERA reference raster is accepted in this version.']}
        save(output/'manifest.json',bundle)
        summaries[case]={'comparisons':len(rows),'assessable':sum(r['reference_status']!='none' for r in rows),'frozen_footprints':len(profiles)}
    save(ROOT/'reports/phase5_2026_11_03/build.json',{'cases':summaries,'source_native_window_bytes':sum(s['size_bytes'] for s in sources['items']),'full_tiles_downloaded':0})
    return summaries

if __name__=='__main__': print(run())
