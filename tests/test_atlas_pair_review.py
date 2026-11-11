"""Independent checks for descriptive pair arithmetic and the field review gates."""
import json
from pathlib import Path

import h5py
import numpy as np
import pytest
import rasterio
from shapely.geometry import LineString, box, mapping

from scripts.audit_atlas_validation import check_reference_split
from src.compute.atlas_admission import active_manifests, admitted_pairs
from src.compute.atlas_review import bank_transect_change
from src.compute.coherence_change import coherence_delta, comparison_policy
from src.compute.atlas_spatial import native_profile

ROOT = Path(__file__).resolve().parents[1]


def test_descriptive_delta_requires_a_shared_valid_native_grid():
    a = np.array([.4,.9,np.nan,.1,.2])
    b = np.array([.7,.5,.1,1.1,-.1])
    np.testing.assert_allclose(coherence_delta(a,b), [.3,-.4,np.nan,np.nan,np.nan], equal_nan=True)
    with pytest.raises(ValueError, match='same grid'):
        coherence_delta(a,b[:2])
    catalog = json.loads((ROOT/'web/atlas-contract-records.json').read_text())
    first, last = catalog['nepal_surface']['pairs']
    assert comparison_policy(first,last)
    for mismatch in ({'intervalSeconds':24*86400},{'firstId':'wrong'},{'sourceSlc':['wrong','other']},
                     {'grid':{**last['grid'],'crs':'EPSG:4326'}},{'lookDirection':'Right'},{'channel':'HV'}):
        assert not comparison_policy(first,{**last,**mismatch})


def test_nepal_values_match_raw_mask_and_nearest_footprint_centers():
    catalog = json.loads((ROOT/'web/atlas-contract-records.json').read_text())
    records = json.loads((ROOT/'web/atlas-record.json').read_text())
    for case in ('nepal_surface','nepal_impact_corridor'):
        path = ROOT/'web/public'/records[case]['manifest_path']
        manifest = json.loads(path.read_text())
        expected = catalog[case]['coherenceComparisons'][0]
        native = []
        for pair in manifest['interferometry']:
            def read(key):
                with rasterio.open(ROOT/'web/public'/pair['rasters'][key].lstrip('/')) as src:
                    return src.read(1)
            raw, flag = read('coherence20'), read('mask20')
            low = flag & 255
            valid = (np.isfinite(raw) & (raw>=0) & (raw<=1) & ((low//10)%10>0) &
                     (low%10>0) & ((flag & 0x00FFFF00)==0) & (flag!=2**32-1))
            assert int(valid.sum()) == pair['statistics']['20']['valid_pixels']
            native.append(np.where(valid,raw,np.nan))
        delta = native[1].astype('float64') - native[0]
        assert expected['crop']['assessed'] == np.isfinite(delta).sum()
        assert expected['crop']['median'] == pytest.approx(np.nanmedian(delta))
        with rasterio.open(path.parent/'tracked_footprint.tif') as ds:
            mask, inverse = ds.read(1)==1, ~ds.transform
        transform = rasterio.Affine(*catalog[case]['pairs'][0]['grid']['affine'])
        row,col = np.indices(delta.shape)
        x,y = transform @ (col+.5,row+.5)
        col,row = (np.floor(v).astype(int) for v in inverse @ (x,y))
        inside = (row>=0)&(row<mask.shape[0])&(col>=0)&(col<mask.shape[1])
        selected = np.zeros(delta.shape,bool)
        selected[inside] = mask[row[inside],col[inside]]
        assert expected['footprints'][0]['assessed'] == np.isfinite(delta[selected]).sum()
        assert expected['footprints'][0]['median'] == pytest.approx(np.nanmedian(delta[selected]))
        if case=='nepal_surface':
            row,col = np.argwhere(mask)[0].tolist()
            local = native_profile(ROOT,case,path,{'kind':'point','row':row,'col':col})
            check = local['profile']['coherence']['deltas']['pair_1']
            left,top = max(0,col-5),max(0,row-5)
            right,bottom = min(mask.shape[1],col+6),min(mask.shape[0],row+6)
            target_row,target_col = np.indices(delta.shape)
            xs,ys = transform @ (target_col+.5,target_row+.5)
            cols,rows = inverse @ (xs,ys)
            values = delta[(rows>=top)&(rows<bottom)&(cols>=left)&(cols<right)]
            assert check['footprintPixels'] == len(values)
            assert check['assessed'] == np.isfinite(values).sum()
            assert check['median'] == pytest.approx(np.nanmedian(values))


@pytest.mark.parametrize('case', ('jamuna_river','tanguar_wetland'))
def test_bangladesh_coherence_matches_downloaded_pair_pixels(case):
    path = active_manifests(ROOT)[case]
    manifest = json.loads(path.read_text())
    pairs = admitted_pairs(ROOT, path, manifest)
    catalog = json.loads((ROOT/'web/atlas-contract-records.json').read_text())[case]
    assert [pair['endUtc'][:10] for pair in catalog['pairs']] == ['2026-10-04','2026-10-16']
    planes = []
    for pair in pairs:
        with h5py.File(ROOT/pair['source_file']) as file:
            for spacing, family in [('20','wrappedInterferogram'),('80','unwrappedInterferogram')]:
                top,left,height,width = pair['grids'][spacing]['source_window']
                window = np.s_[top:top+height,left:left+width]
                group = file[f'science/LSAR/GUNW/grids/frequencyA/{family}']
                raw = group['HH/coherenceMagnitude'][window]
                flag = group['mask'][window]
                low = flag & 255
                valid = (np.isfinite(raw) & (raw>=0) & (raw<=1) & ((low//10)%10>0) &
                         (low%10>0) & ((flag & 0x00FFFF00)==0) & (flag!=2**32-1))
                expected = np.where(valid,raw,np.nan)
                raster = ROOT/'web/public'/pair['rasters']['coherence'+spacing].lstrip('/')
                with rasterio.open(raster) as ds:
                    np.testing.assert_array_equal(ds.read(1), expected)
                if spacing == '20':
                    planes.append(expected)
    delta = planes[1]-planes[0]
    comparison = catalog['coherenceComparisons'][0]
    assert comparison['crop']['assessed'] == np.isfinite(delta).sum()
    assert comparison['crop']['median'] == pytest.approx(np.nanmedian(delta))
    native = native_profile(ROOT, case, path, {'kind':'point','row':1000,'col':1000})
    assert native['profile']['coherence']['deltas'][pairs[-1]['pair_id']]['assessed'] > 0


def test_bank_transect_sign_and_limits():
    transect = LineString([(0,0),(100,0)])
    bank = lambda x: LineString([(x,-50),(x,50)])
    params = ('EPSG:32645',[2,2,1],20)
    assert bank_transect_change(transect,bank(20),bank(55),*params) == {
        'status':'resolved','movementM':pytest.approx(35),'uncertaintyBoundM':5,'direction':'along_transect'}
    assert bank_transect_change(transect,bank(55),bank(20),*params)['movementM'] == pytest.approx(-35)
    for x in (20,21,40):
        assert bank_transect_change(transect,bank(20),bank(x),*params)['status'] == 'unresolved'
    double = LineString([(40,-10),(40,10),(80,10),(80,-10)])
    assert bank_transect_change(transect,bank(20),double,*params)['status'] == 'ambiguous_crossing'


def test_reference_split_blocks_scene_and_spatial_leakage():
    first = {'split':'development','sceneIds':['hls-a'],'visitIds':['nisar-a'],'blockId':'a',
             'bufferedGeometry':mapping(box(88,23,89,24))}
    last = {'split':'holdout','sceneIds':['hls-b'],'visitIds':['nisar-b'],'blockId':'b',
            'bufferedGeometry':mapping(box(90,24,91,25))}
    assert check_reference_split([first,last]) == {'developmentUnits':1,'holdoutUnits':1}
    for leak in ({'sceneIds':['hls-a']},{'visitIds':['nisar-a']},{'blockId':'a'},
                 {'bufferedGeometry':mapping(box(88.9,23.9,90,25))}):
        with pytest.raises(ValueError, match='leak'):
            check_reference_split([first,{**last,**leak}])
