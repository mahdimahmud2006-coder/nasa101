"""Validate saved multi-case rasters, map assets, profiles and empty-data states."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from PIL import Image
from src.compute.investigation_probe import probe
from src.export.artifacts import write_json

ROOT=Path(__file__).resolve().parents[2]


def run(root=ROOT, report_directory='docs/reports/investigations_latest'):
    root=Path(root);public=root/'web/public/cases'
    registry=json.loads((public/'investigations.json').read_text());summary=[]
    for case in registry['cases']:
        folder=public/case['case_id']/'investigation'
        if case['status']=='AWAITING_DATA':
            assert not (folder/'manifest.json').exists(),'Pending case has stale ready observations'
            summary.append({'case_id':case['case_id'],'status':'AWAITING_DATA','fabricated_observations':False});continue
        manifest=json.loads((folder/'manifest.json').read_text())
        assert manifest['case_id']==case['case_id']
        assert len(manifest['observations'])>=3
        assert len(set(o['timestamp'] for o in manifest['observations']))==len(manifest['observations'])
        channels={'hh':[],'hv':[]}
        for obs in manifest['observations']:
            for pol in channels:
                with rasterio.open(folder/obs['rasters'][pol]) as source:
                    assert list(source.shape)==manifest['grid']['shape']
                    assert list(source.transform)[:6]==manifest['grid']['affine']
                    assert source.crs.to_string()==manifest['grid']['crs']
                    values=source.read(1)
                    np.testing.assert_allclose(np.isfinite(values).mean(),obs['quality'][pol]['valid_fraction'])
                    channels[pol].append(values)
            for name in filter(None,obs['layers'].values()):
                with Image.open(folder/name) as image:image.verify()
        hh,hv=np.stack(channels['hh']),np.stack(channels['hv'])
        if case['module'] in ('river','wetland'):
            valid=np.isfinite(hh)&np.isfinite(hv)
            threshold=manifest['thresholds'];area=manifest['grid']['pixel_area_km2']
            dark=valid&(hh<=threshold['radar_dark_hh_db'])&(hv<=threshold['radar_dark_hv_db'])
            for i,observation in enumerate(manifest['observations']):
                common=valid[0]&valid[i]
                expected={'paired_valid_area_km2':int(valid[i].sum())*area,
                    'radar_dark_candidate_area_km2':int(dark[i].sum())*area,
                    'baseline_common_area_km2':int(common.sum())*area,
                    'gain_dark_signature_km2':int((common&dark[i]&~dark[0]).sum())*area,
                    'loss_dark_signature_km2':int((common&~dark[i]&dark[0]).sum())*area,
                    'persistent_dark_signature_km2':int((common&dark[i]&dark[0]).sum())*area,
                    'brightening_candidate_area_km2':int((common&((hh[i]-hh[0])>=threshold['brightening_db'])&((hv[i]-hv[0])>=threshold['brightening_db'])).sum())*area}
                for key,value in expected.items():
                    np.testing.assert_allclose(observation['response'][key],value,atol=1e-8)
            count=valid.sum(axis=0)
            expected=np.full(count.shape,np.nan,dtype=np.float32)
            np.divide(dark.sum(axis=0),count,out=expected,where=count>=2)
            with rasterio.open(folder/'dark_observation_fraction.tif') as source:
                np.testing.assert_allclose(source.read(1),expected,equal_nan=True)
            with rasterio.open(folder/'valid_visit_count.tif') as source:
                np.testing.assert_array_equal(source.read(1),count)
        for profile in manifest['profiles']:
            rows=profile['observations'];assert len(rows)==len(hh)
            if profile['status']=='MEASURED':
                assert rows[0]['hh_baseline_delta_db']==0 and rows[0]['hv_baseline_delta_db']==0
                assert rows[0]['hh_successive_delta_db'] is None
                for i,row in enumerate(rows):
                    if i:
                        for pol in ['hh','hv']:
                            np.testing.assert_allclose(row[pol+'_baseline_delta_db']-rows[i-1][pol+'_baseline_delta_db'],row[pol+'_successive_delta_db'],atol=2e-6)
                if case.get('legacy_zone_raster'):
                    with rasterio.open(root/case['legacy_zone_raster']) as source:mask=source.read(1)>0
                    common=mask & np.isfinite(hh).all(axis=0)&np.isfinite(hv).all(axis=0)
                    for i,row in enumerate(rows):
                        np.testing.assert_allclose(row['hh_baseline_delta_db'],(hh[i]-hh[0])[common].mean(dtype='float64'),atol=1e-6)
                        np.testing.assert_allclose(row['hv_baseline_delta_db'],(hv[i]-hv[0])[common].mean(dtype='float64'),atol=1e-6)
                if profile.get('footprint_kind')=='study_window':
                    common=np.isfinite(hh).all(axis=0)&np.isfinite(hv).all(axis=0)
                    assert profile['common_valid_pixels']==int(common.sum())
                    for i,row in enumerate(rows):
                        np.testing.assert_allclose(row['hh_baseline_delta_db'],(hh[i]-hh[0])[common].mean(dtype='float64'),atol=1e-6)
                        np.testing.assert_allclose(row['hv_baseline_delta_db'],(hv[i]-hv[0])[common].mean(dtype='float64'),atol=1e-6)
        row,col=manifest['grid']['shape'][0]//2,manifest['grid']['shape'][1]//2
        picked=probe(folder,row,col)
        assert picked['footprint_pixels']==121
        assert all(obs['source_granule_id'].startswith('NISAR_L2_PR_GCOV_') for obs in manifest['observations'])
        summary.append({'case_id':case['case_id'],'status':'SAVED_OUTPUT_CHECKS_PASS','observations':len(hh),
                        'native_shape':manifest['grid']['shape'],'saved_profiles':len(manifest['profiles']),
                        'reference_overlap_km2':manifest['reference']['intersected_geometry_area_km2'] if manifest['reference'] else None})
    old=json.loads((root/'docs/reports/implementation_06_07_prior_artifacts.json').read_text())
    for name,digest in old.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Changed prior output: '+name
    result={'status':'SAVED_INVESTIGATION_OUTPUT_CHECKS_PASS','cases':summary,'prior_artifacts_preserved':len(old),
            'scope':'Raster/coverage/geometry/profile/asset consistency and known numerical relationships. Not physical-cause validation, water/habitat classifier accuracy, browser QA or a disconnected rehearsal.'}
    destination=root/report_directory;destination.mkdir(parents=True,exist_ok=True)
    write_json(destination/'saved_outputs.json',result);print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report-directory',default='docs/reports/investigations_latest')
    args=parser.parse_args();run(report_directory=args.report_directory)
