"""Reconcile the extended record with native inputs, formulas and preserved history."""
import json
from pathlib import Path
import numpy as np,rasterio
from affine import Affine
from rasterio.windows import Window
from src.compute.evidence_common import ROOT,load,save,sha
from src.compute.bangladesh_record import VERSION,CASES,REPORT,stack
from src.compute.timeseries_pipeline import canonical_observation
from src.ingest.timeseries import read_observation
from src.compute.investigation_dna import polygon_evidence

def read(path):
    with rasterio.open(path) as ds:return ds.read(1)

def validate():
    historical=load(REPORT/'historical_sha256.json')
    for path,digest in historical.items():assert sha(ROOT/path)==digest,'Historical file changed: '+path
    audit=load(REPORT/'source_audit.json');new={r['granule_id']:r for r in audit['records']};result={}
    for case in CASES:
        directory=ROOT/f'web/public/cases/{case}/{VERSION}';base=directory/'investigation';m=load(base/'manifest.json');oldbase=ROOT/f'web/public/cases/{case}/investigation';old=load(oldbase/'manifest.json')
        assert len(m['observations'])==10 and m['reference_timestamp']==old['observations'][0]['timestamp']
        assert [o['timestamp'] for o in m['observations']]==sorted({o['timestamp'] for o in m['observations']})
        assert len({o['observation_id'] for o in m['observations']})==10
        cal=load(directory/'calendar.json');assert sum(s['status']=='observed' for s in cal['slots'])==10
        gaps=[s for s in cal['slots'] if s['status']!='observed'];assert len(gaps)==1 and gaps[0]['date']=='2026-08-05' and gaps[0]['status']=='instrument_gap'
        assert sum(i['flagged'] for i in cal['intervals'])==1
        channels=stack(base,m);hh,hv=channels['hh'],channels['hv']
        valid=np.isfinite(hh)&np.isfinite(hv);common=valid.all(0);area=m['grid']['pixel_area_km2'];raw_samples=0
        priorbytime={o['timestamp']:o for o in old['observations']}
        dual=load(directory/'dualpol-v1/manifest.json');sensitivity=load(directory/'dualpol-v1/sensitivity.json')
        for key,digest in dual['provenance']['inputs_sha256'].items():assert sha(ROOT/key)==digest,key
        for key,digest in dual['provenance']['assets_sha256'].items():assert sha(directory/'dualpol-v1'/key)==digest,key
        for key,digest in dual['provenance']['code_sha256'].items():assert sha(ROOT/key)==digest,key
        for i,o in enumerate(m['observations']):
            if o['timestamp'] in priorbytime:
                for p in ['hh','hv']:assert sha(base/o['rasters'][p])==sha(oldbase/priorbytime[o['timestamp']]['rasters'][p])
            else:
                r=read_observation(ROOT/new[o['source_granule_id']]['source_file']);r['source_file']=str(ROOT/new[o['source_granule_id']]['source_file'])
                for row,col in [(100,100),(m['grid']['shape'][0]//2,m['grid']['shape'][1]//2),(m['grid']['shape'][0]-101,m['grid']['shape'][1]-101)]:
                    affine=Affine(*m['grid']['affine'])*Affine.translation(col-5,row-5)
                    for p,term in [('hh','HHHH'),('hv','HVHV')]:
                        extracted,_=canonical_observation({**r,'covariance_term':term,'polarization':term[:2],'layer_path':r['grid_path']+'/'+term},affine,m['grid']['crs'],(11,11),3)
                        assert np.isclose(extracted[5,5],(hh if p=='hh' else hv)[i,row,col],equal_nan=True,atol=1e-5);raw_samples+=1
            response=o['response'];assert np.isclose(response['paired_valid_area_km2'],int(valid[i].sum())*area)
            dark=valid[i]&(hh[i]<=-17)&(hv[i]<=-24);assert np.isclose(response['radar_dark_candidate_area_km2'],int(dark.sum())*area)
            d=dual['observations'][i];assert d['observation_id']==o['observation_id']
            cpr=read(directory/'dualpol-v1'/d['rasters']['cpr']);expected=hv[i]-hh[i];expected[~valid[i]]=np.nan;np.testing.assert_array_equal(cpr,expected)
            for p,values in [('hh',hh),('hv',hv),('cpr',hv-hh)]:
                for kind,prior in [('baseline',0),('successive',i-1)]:
                    if prior<0:assert p+'_'+kind not in d['rasters'];continue
                    actual=read(directory/'dualpol-v1'/d['rasters'][p+'_'+kind]);support=valid[i]&valid[prior]
                    np.testing.assert_array_equal(np.isfinite(actual),support);np.testing.assert_allclose(actual[support],(values[i]-values[prior])[support],atol=1e-5,rtol=0)
            sweep=sensitivity['observations'][i];assert sweep['common_valid_pixels']==int(common.sum())
            for hi,vi in [(0,0),(3,3),(6,6)]:assert sweep['candidate_pixels'][hi][vi]==int((common&(hh[i]<=sweep['hh_cutoffs_db'][hi])&(hv[i]<=sweep['hv_cutoffs_db'][vi])).sum())
        occupancy=read(base/'dark_observation_fraction.tif');counts=valid.sum(0);expected=np.full(counts.shape,np.nan,dtype='float32');np.divide((valid&(hh<=-17)&(hv<=-24)).sum(0),counts,out=expected,where=counts>=2);np.testing.assert_array_equal(occupancy,expected)
        np.testing.assert_array_equal(read(base/'valid_visit_count.tif'),counts)
        context=load(directory/'context-v2/manifest.json');dates=[o['timestamp'] for o in m['observations']]
        assert [r['timestamp'] for r in context['rain']]==dates==[r['timestamp'] for r in context['radiometric_controls']]
        assert all(r['imerg_72h_mm'] is None for r in context['rain'])
        selected=read(directory/'context-v2/stable_targets.tif')==1;controls=selected&common
        assert sha(directory/'context-v2/stable_targets.tif')==sha(ROOT/f'web/public/cases/{case}/context-v2/stable_targets.tif')
        for i,r in enumerate(context['radiometric_controls']):
            assert r['common_control_pixels']==int(controls.sum())
            for p,values in [('hh',hh),('hv',hv)]:assert np.isclose(r[p+'_median_db'],np.median(values[i][controls]))
        evidence=load(directory/'evidence-v2/manifest.json')
        for r in evidence['profiles']:
            p=r['profile'];w=p['window'];mask=read(directory/'evidence-v2'/r['footprint_raster']['file'])==1
            sl=np.s_[w['row']:w['row']+w['height'],w['col']:w['col']+w['width']];support=mask&common[sl];assert p['common_valid_pixels']==int(support.sum())
            for i,s in enumerate(p['observations']):
                for pol,values in [('hh',hh),('hv',hv)]:
                    if p['status']=='MEASURED':assert np.isclose(s[pol+'_mean_db'],values[i][sl][support].astype('float64').mean())
            assert len(r['explanations'])==10 and len(p['observations'])==10
        refs=load(directory/'references-v1/manifest.json');newids={o['observation_id'] for o in m['observations'] if o['source_granule_id'] in new}
        added=[r for r in refs['results'] if r['observation_id'] in newids];assert len(added)==12 and all(r['reference_status']=='none' and r['clear_assessable_pixels']==0 for r in added)
        assert all(len(p['profile']['observations'])==10 for p in refs['profiles'])
        selected=polygon_evidence(case,[[900,900],[911,900],[911,911],[900,911]],ROOT,directory);assert len(selected['profile']['observations'])==10
        result[case]={'observations':10,'nominal_slots':11,'permanent_outage':'2026-08-05','raw_source_interior_samples':raw_samples,'common_valid_pixels':int(common.sum()),'saved_profiles_checked':len(evidence['profiles']),'all_pixel_checks':'CPR, endpoint differences, masks, dark count, occupancy, valid visit count; independent threshold cells','reference_new_dates_unavailable':len(added)}
    output={'status':'BANGLADESH_TEN_VISIT_NATIVE_CHECKS_PASS','historical_files_unchanged':len(historical),'record_manifests_sha256':{str(p.relative_to(ROOT)):sha(p) for c in CASES for p in (ROOT/f'web/public/cases/{c}/{VERSION}').rglob('manifest.json')},'cases':result,'scope':'Numerical/source reconciliation, bindings and preservation; not cause, classification accuracy or browser validation.'}
    save(REPORT/'native_validation.json',output);return output
if __name__=='__main__':print(json.dumps(validate(),indent=2))
