"""Check separately sourced terrain, geometry masks, frozen controls and rain null semantics."""
import json
import numpy as np,rasterio
from src.compute.evidence_common import ROOT,load,sha

def validate():
    sources=load(ROOT/'data/context/context-v2/terrain/sources.json')
    for item in sources['items']:assert sha(ROOT/item['file'])==item['sha256']
    result={}
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        directory=ROOT/f'web/public/cases/{case}/context-v2';m=load(directory/'manifest.json');sel=load(directory/'stable_target_selection.json')
        assert sha(directory/'stable_targets.tif')==sel['mask_sha256']
        with rasterio.open(directory/'stable_targets.tif') as ds:assert int((ds.read(1)==1).sum())==sel['selected_pixels']
        for layer in m['layers'].values():
            with rasterio.open(directory/layer['raster']) as ds:assert list(ds.shape)==m['grid']['shape'] and ds.crs.to_string()==m['grid']['crs']
        for row in m['rain']:
            assert row['status']=='unavailable' and all(row[k] is None for k in ['imerg_24h_mm','imerg_72h_mm','imerg_168h_mm','imerg_since_previous_mm'])
            assert row['windows']['24h']['end_exclusive_utc']==row['timestamp']
        counts={r['common_control_pixels'] for r in m['radiometric_controls']};assert len(counts)==1
        result[case]={'status':'PASS','frozen_control_pixels':sel['selected_pixels'],'rain':'unavailable, not zero','median_slope_degrees':m['terrain_summary']['median_slope_degrees']}
    histogram=load(ROOT/'data/context/context-v2/h1_source_histograms.json');assert len(histogram['records'])==6
    for row in histogram['records']:
        for pol in ['hh','hv']:assert sum(row['histogram_counts'][pol])+sum(row['tails_below_above'][pol])==row['valid_pixels'][pol]
    return {'status':'CONTEXT_V2_CHECKS_PASS','cases':result,'whole_source_scenes_checked':6,'physical_cause':'unresolved'}
if __name__=='__main__':print(json.dumps(validate(),indent=2))
