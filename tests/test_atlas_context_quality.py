import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import pytest
from shapely.geometry import box

from scripts.audit_phase7 import request
from src.compute.atlas_measurements import dualpol_summary
from src.compute.atlas_terrain import height_above_drainage
from src.compute.context_v2 import rain_window
from src.compute.expanded_record import gunw_validity
from src.compute.imerg_context import imerg_window
from src.compute.thermal_pipeline import quality_mask
from src.ingest.environment import sha
from src.ingest.extract_gcov import gcov_valid_samples

ROOT = Path(__file__).resolve().parents[1]


def test_imerg_partial_time_bins_quality_and_area(tmp_path):
    epoch = int(datetime(2026,8,1,tzinfo=timezone.utc).timestamp())
    granules = []
    for clock, minute, ending, rate, offset in [('000000','0000','002959',2,0),('003000','0030','005959',6,1800)]:
        name = f'3B-HHR.MS.MRG.3IMERG.20260801-S{clock}-E{ending}.{minute}.V07B.HDF5'
        path = tmp_path/name
        with h5py.File(path,'w') as hdf:
            grid = hdf.create_group('Grid')
            grid['lon'] = [85.05,85.15]
            grid['lat'] = [27.05,27.15]
            grid['time_bnds'] = [[epoch+offset,epoch+offset+1800]]
            grid['precipitation'] = [[[rate,rate],[rate+2,rate+2]]]
            grid['precipitation'].attrs['units'] = 'mm/hr'
            grid['precipitationQualityIndex'] = [[[1.,1.],[1.,1.]]]
        granules.append({'file':name,'id':name,'sha256':sha(path),'startUtc':f'2026-08-01T00:{minute[-2:]}:00Z'})
    manifest = tmp_path/'admitted.json'
    receipt = {'schemaVersion':1,'collection':'GPM_3IMERGHH.07','lineage':'approved','minimumQualityIndex':.5,'granules':granules}
    window = rain_window('2026-08-01T00:45:00Z',start='2026-08-01T00:15:00Z')

    def run():
        manifest.write_text(json.dumps(receipt))
        return imerg_window(tmp_path,manifest,sha(manifest),box(85,27,85.2,27.1),window)

    full = run()
    assert full['totalMm'] == pytest.approx(2.5)
    assert full['expectedBins'] == full['validBins'] == 2
    assert full['completeAreaFraction'] == pytest.approx(1)
    path = tmp_path/granules[-1]['file']
    with h5py.File(path,'r+') as hdf:
        hdf['Grid/precipitationQualityIndex'][0,1,0] = 0
    granules[-1]['sha256'] = sha(path)
    partial = run()
    assert partial['totalMm'] == pytest.approx(2)
    assert partial['completeAreaFraction'] == pytest.approx(.5)
    receipt['granules'] = granules[:1]
    missing = run()
    assert missing['totalMm'] is None
    assert missing['validBins'] == 1 and missing['observedBins'] == 1
    receipt['granules'] = granules
    granules[-1]['startUtc'] = '2026-08-01T01:00:00Z'
    shifted = rain_window('2026-08-01T01:15:00Z',hours=.25)
    manifest.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='filename'):
        imerg_window(tmp_path,manifest,sha(manifest),box(85,27,85.2,27.1),shifted)


def test_product_masks_use_independent_precedence():
    assert gcov_valid_samples(np.array([1.,1,1,9,0,1]),np.array([1,0,255,1,1,2]),
                              np.array([2,2,2,2,2,0]),(9,)).tolist() == [True,False,False,False,False,False]
    assert gunw_validity(np.array([.6,.6,.6,.6,1.1]),np.array([11,111,1,267,11],dtype='uint32')).tolist() == [True,True,False,False,False]
    valid, _ = quality_mask(np.array([100,100,100,100]),np.array([0,8,0,0]),np.array([0,0,1,0]),
                            np.array([50,50,50,600]),max_uncertainty_k=5)
    assert valid.tolist() == [True,False,False,False]


def test_hand_follows_downstream_channel_and_keeps_boundary_paths_masked():
    dem = np.array([[12.,7.,2.],[5.,4.,np.nan]])
    links = np.array([1,2,-1,4,5,-1])
    area = np.array([1.,4.,6.,1.,3.,np.nan])
    order = [2,1,0,4,3]
    height, counts = height_above_drainage(dem,links,area,order,threshold_m2=4)
    np.testing.assert_allclose(height,[[5.,0.,np.nan],[np.nan,np.nan,np.nan]],equal_nan=True)
    assert counts == {'assessed':2,'masked':1,'boundaryAffected':1,'negativeHeight':0,'unresolved':2}
    height, counts = height_above_drainage(dem,links,area,order,threshold_m2=5)
    assert np.isnan(height).all() and counts['boundaryAffected']==3
    with pytest.raises(ValueError,match='precede'):
        height_above_drainage(dem,links,area,list(reversed(order)),threshold_m2=4)


def test_dualpol_uses_mean_of_pixelwise_fractions_and_valid_zero():
    values = dualpol_summary([0,0,-3000,3000,np.nan],[0,10,3000,-3000,0],np.ones(5,bool))
    assert values['validPixels'] == 4
    assert values['crossDominantPixels'] == 2
    assert values['powerShare'] == pytest.approx((.5+10/11+1+0)/4)
    assert values['cprDb'] == pytest.approx(2.5)
    assert dualpol_summary([np.nan],[0],np.ones(1,bool))['powerShare'] is None


def test_existing_scenario_replays_the_accepted_inputs_and_output():
    folder = ROOT/'web/public/cases/nepal_case_01/flood/scenarios'
    saved = json.loads((folder/'flood-0a9bccef77fdb02c8199/result.json').read_text())
    status, body = request('/api/cases/nepal_case_01/scenario/flood',saved['parameters'])
    result = json.loads(body)
    assert status == 200
    for field in ('scenario_id','parameters','inputs_sha256','model_version','rainfall_window','summary'):
        assert result[field] == saved[field]
    status, _ = request('/api/cases/nepal_case_01/scenario/flood',{**saved['parameters'],'observation_id':'acq_20261018T233918'})
    assert status == 422


def test_context_catalog_reports_only_exact_accepted_bindings():
    catalog = json.loads((ROOT/'web/atlas-contract-records.json').read_text())
    for case, row in catalog.items():
        environment = row['environment']
        assert len(environment['imerg']) == len(row['observations'])
        assert all(r['acceptedBins']==0 and r['coverage'] is None for r in environment['imerg'].values())
        if case!='nepal_surface':
            assert not environment['rain'] and not environment['thermal'] and environment['scenario'] is None
        for quality in row['quality']['gcov'].values():
            assert quality['pairedValid'] <= min(quality[p]['assessed'] for p in ('hh','hv'))
            assert all(quality[p]['assessed']+quality[p]['masked']==quality['total'] for p in ('hh','hv'))
    nepal = catalog['nepal_surface']['environment']
    assert set(nepal['rain']) == {'acq_20260819T233918','acq_20260831T233918','acq_20260912T233918'}
    assert nepal['rain']['acq_20260819T233918']['rain_24h']['meanMm'] == pytest.approx(9.07463617)
    assert nepal['rain']['acq_20260819T233918']['rain_24h']['window']['end_lag_seconds'] == 2358
