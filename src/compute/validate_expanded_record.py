"""Check published extension against protected products and independently read raw windows."""
import json
from pathlib import Path
import h5py
import numpy as np
import rasterio
from affine import Affine
from rasterio.windows import Window
from src.compute.evidence_common import ROOT, load, sha
from src.compute.expanded_record import CASES, VERSION, REFERENCE
from src.ingest.timeseries import read_observation, incompatibilities
from src.compute.timeseries_pipeline import canonical_observation


def validate():
    registry=load(ROOT/f'web/public/cases/{VERSION}.json');assert registry['unique_gcov_granules']==10 and registry['unique_gunw_granules']==2
    result={};anchor=read_observation(ROOT/'aug19.h5')
    for case in CASES:
        directory=ROOT/f'web/public/cases/{case}/{VERSION}';m=load(directory/'manifest.json')
        assert len(m['observations'])==10 and len(m['interferometry'])==2
        dates=[o['timestamp'] for o in m['observations']];assert dates==sorted(set(dates))
        assert m['reference_timestamp']==REFERENCE and dates[m['reference_index']]==REFERENCE
        assert not any(t.startswith('2026-08-07') for t in dates)
        assert sha(ROOT/f'web/public/cases/{case}/investigation/manifest.json')==m['original_manifest_sha256']
        for filename,digest in m['assets_sha256'].items():assert sha(directory/filename)==digest
        native_samples=0
        for obs in m['observations']:
            record=read_observation(ROOT/obs['source_file']);assert not incompatibilities(anchor,record)
            assert record['granule_id']==obs['source_granule_id']
            if not obs['preserved_original_observation']:
                # A fresh independent small raw extraction, compare an interior median pixel.
                affine=Affine(*m['grid']['affine'])*Affine.translation(1195,1195)
                record['source_file']=str(ROOT/obs['source_file'])
                for pol,term in [('hh','HHHH'),('hv','HVHV')]:
                    source={**record,'covariance_term':term,'polarization':term[:2],'layer_path':record['grid_path']+'/'+term}
                    raw,_=canonical_observation(source,affine,m['grid']['crs'],(11,11),3)
                    with rasterio.open(ROOT/'web/public'/obs['rasters'][pol].lstrip('/')) as ds:
                        published=ds.read(1,window=Window(1200,1200,1,1))[0,0]
                    assert np.isclose(raw[5,5],published,equal_nan=True,atol=1e-5);native_samples+=1
        for p in m['interferometry']:
            assert p['los_displacement_cm'] is None
            with h5py.File(ROOT/p['source_file']) as f:
                for spacing,family in [(20,'wrappedInterferogram'),(80,'unwrappedInterferogram')]:
                    grid=p['grids'][str(spacing)];r,c,h,w=grid['source_window'];g=f['science/LSAR/GUNW/grids/frequencyA/'+family]
                    raw=g['HH/coherenceMagnitude'][r:r+h,c:c+w];mask=g['mask'][r:r+h,c:c+w]
                    low=mask & 255
                    valid=np.isfinite(raw)&(raw>=0)&(raw<=1)&((low//10)%10>0)&(low%10>0)&((mask&0x00FFFF00)==0)&(mask!=2**32-1)
                    with rasterio.open(ROOT/'web/public'/p['rasters'][f'coherence{spacing}'].lstrip('/')) as ds:
                        actual=ds.read(1);assert ds.res==(spacing,spacing) and list(ds.shape)==grid['shape']
                    assert np.array_equal(np.isfinite(actual),valid)
                    assert np.array_equal(actual[valid],raw[valid])
                    stats=p['statistics'][str(spacing)]
                    assert stats['valid_pixels']==int(valid.sum())
                    assert np.isclose(stats['mean_coherence'],raw[valid].astype('float64').mean())
        old=load(ROOT/f'web/public/cases/{case}/evidence-v2/manifest.json')['profiles'][0]['profile']
        new=m['profiles'][0];assert new['footprint_pixels']==old['footprint_pixels']
        if new['common_valid_pixels']==old['common_valid_pixels']:
            for previous in old['observations']:
                current=next(r for r in new['observations'] if r['timestamp']==previous['timestamp'])
                assert np.isclose(current['hh_reference_delta_db'],previous['hh_baseline_delta_db'],atol=1e-7)
        result[case]={'observed_visits':10,'native_coherence_pairs':2,'raw_gcov_interior_pixel_samples':native_samples,
                      'tracked_footprint_pixels':new['footprint_pixels'],'expanded_common_valid_pixels':new['common_valid_pixels']}
    return {'status':'EXPANDED_NATIVE_SOURCE_CHECKS_PASS','cases':result,
            'scope':'Raw source/canonical sample reconciliation, full coherence crop masks/values, hashes and temporal semantics. No physical cause or displacement validation.'}


if __name__=='__main__':print(json.dumps(validate(),indent=2))
