"""Independent native-pixel checks of additive diagonal-only products."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path):
    with rasterio.open(path) as ds:return ds.read(1)

def validate(root=ROOT):
    root=Path(root);config=json.loads((root/'config.dualpol.json').read_text());version=config['product_version'];report={}
    palettes=root/config['palette_directory'];source=json.loads((palettes/'provenance.json').read_text())
    for key,value in source.items():
        if isinstance(value,dict) and 'sha256' in value:assert digest(palettes/key)==value['sha256']
    original_cividis=None
    for node in ast.parse((palettes/'matplotlib_source').read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_cividis_data' for t in node.targets):original_cividis=ast.literal_eval(node.value)
    np.testing.assert_array_equal(json.loads((palettes/'cividis.json').read_text()),original_cividis)
    np.testing.assert_array_equal(json.loads((palettes/'vik.json').read_text()),np.loadtxt(palettes/'vik_source'))
    for case in config['source_cases']:
        directory=root/f'web/public/cases/{case}/{version}';source_dir=directory.parent/'investigation'
        m=json.loads((directory/'manifest.json').read_text());old=json.loads((source_dir/'manifest.json').read_text())
        assert m['grid']==old['grid']
        for name,h in m['provenance']['inputs_sha256'].items():assert digest(root/name)==h,name
        for name,h in m['provenance']['code_sha256'].items():assert digest(root/name)==h,name
        assert m['provenance']['config_sha256']==digest(root/'config.dualpol.json')
        for name,h in m['provenance']['assets_sha256'].items():assert digest(directory/name)==h,name
        hh=np.stack([read(source_dir/o['rasters']['hh']) for o in old['observations']]);hv=np.stack([read(source_dir/o['rasters']['hv']) for o in old['observations']]);valid=np.isfinite(hh)&np.isfinite(hv);common=valid.all(0)
        sweep=json.loads((directory/'sensitivity.json').read_text());checked=0
        for i,o in enumerate(m['observations']):
            cpr=read(directory/o['rasters']['cpr']);expected=hv[i]-hh[i];expected[~valid[i]]=np.nan
            np.testing.assert_array_equal(cpr,expected)
            with rasterio.open(directory/o['rasters']['composite']) as ds:
                rgba=ds.read();assert ds.count==4 and ds.tags(ns='IMAGE_STRUCTURE')['LAYOUT']=='COG'
                np.testing.assert_array_equal(rgba[3]>0,valid[i])
                for channel,values,limits in [(0,hh[i],config['display_limits']['hh']),(1,hv[i],config['display_limits']['hv']),(2,hh[i]-hv[i],config['display_limits']['ratio'])]:
                    expected_rgb=np.rint(np.clip((values[valid[i]]-limits[0])/(limits[1]-limits[0]),0,1)*255).astype('uint8')
                    np.testing.assert_array_equal(rgba[channel][valid[i]],expected_rgb)
            bits=read(directory/o['rasters']['hint_bits']);np.testing.assert_array_equal(bits==255,~valid[i])
            settings=config['hints'];low=valid[i]&(hh[i]<=settings['hh_low_db'])&(hv[i]<=settings['hv_low_db']);np.testing.assert_array_equal((bits!=255)&((bits&1)!=0),low)
            if i:
                support=valid[i]&valid[0]
                expected_hh=support&((hh[i]-hh[0])>=settings['hh_rise_db'])&(np.abs(hv[i]-hv[0])<=settings['hv_stable_abs_db'])
                expected_hv=support&((hv[i]-hv[0])>=settings['hv_rise_db'])
                np.testing.assert_array_equal((bits!=255)&((bits&2)!=0),expected_hh);np.testing.assert_array_equal((bits!=255)&((bits&4)!=0),expected_hv)
            else:assert o['hint_statistics']['hint_hh'] is None and o['hint_statistics']['hint_hv'] is None
            for pol,values in [('hh',hh),('hv',hv),('cpr',hv-hh)]:
                for kind,prior in [('baseline',0),('successive',i-1)]:
                    if prior<0:assert pol+'_'+kind not in o['rasters'];continue
                    actual=read(directory/o['rasters'][pol+'_'+kind]);support=valid[i]&valid[prior]
                    np.testing.assert_array_equal(np.isfinite(actual),support)
                    np.testing.assert_allclose(actual[support],(values[i]-values[prior])[support],rtol=0,atol=1e-5)
            s=sweep['observations'][i];assert s['common_valid_pixels']==int(common.sum())
            counts=np.asarray(s['candidate_pixels']);assert (np.diff(counts,axis=0)>=0).all() and (np.diff(counts,axis=1)>=0).all()
            for hi,vi in [(0,0),(0,6),(3,3),(6,0),(6,6)]:
                expected_count=int((common&(hh[i]<=s['hh_cutoffs_db'][hi])&(hv[i]<=s['hv_cutoffs_db'][vi])).sum())
                assert counts[hi,vi]==expected_count
                assert abs(s['candidate_area_km2'][hi][vi]-expected_count*m['grid']['pixel_area_km2'])<1e-10
                checked+=1
        records=pq.read_table(directory/'profiles.parquet').to_pylist()
        assert len(records)==sum(len(p['observations']) for p in old['profiles'])
        for row in records:
            original=old['profiles'][row['profile_index']]['observations'][row['index']]
            for suffix in ('mean_db','baseline_delta_db','successive_delta_db'):
                h,v=original.get('hh_'+suffix),original.get('hv_'+suffix)
                assert row['cpr_'+suffix]==(None if h is None or v is None else v-h)
        report[case]={'status':'PASS','observations':len(m['observations']),'native_cpr_rgb_difference_masks_and_hint_flags':'all pixels checked','sensitivity_independent_cutoff_cells_checked':checked,'parquet_rows_checked':len(records)}
    return {'status':'DUALPOL_NATIVE_CHECKS_PASS','cases':report,'palettes':'upstream source checksums and derived tables match','scope':'Numerical/export checks, not physical-mechanism validation or browser visual QA.'}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
