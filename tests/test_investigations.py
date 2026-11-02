"""Scientific contracts for the shared investigation/river/wetland engine."""
import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.transform import from_origin
from src.compute.investigations import radar_responses, fixed_footprint_profile
from src.compute.investigation_pipeline import processing_release, sources_for, build_case
from src.compute.investigation_probe import probe
from src.api import app
from test_timeseries_api import request


def test_dark_transitions_preserve_missingness_and_baseline_denominators():
    hh=np.array([[[-20,-12,-20]], [[-12,-20,np.nan]], [[-20,-20,np.nan]]],dtype='float32')
    hv=np.array([[[-27,-16,-27]], [[-16,-27,np.nan]], [[-27,-27,np.nan]]],dtype='float32')
    result=radar_responses(hh,hv)
    assert result['transitions'][1]['loss'].tolist()==[[True,False,False]]
    assert result['transitions'][1]['gain'].tolist()==[[False,True,False]]
    assert result['transitions'][1]['common'].sum()==2
    np.testing.assert_allclose(result['dark_observation_fraction'][0,:2],[2/3,2/3])
    assert np.isnan(result['dark_observation_fraction'][0,2])
    assert result['valid_visits'].tolist()==[[3,3,1]]


def test_brightening_requires_both_channels_and_baseline_common_validity():
    hh=np.array([[[-20,-20,np.nan]], [[-16,-16,-16]]],dtype='float32')
    hv=np.array([[[-28,-28,-28]], [[-24,-27,-24]]],dtype='float32')
    result=radar_responses(hh,hv)
    assert result['brightening'][1].tolist()==[[True,False,False]]
    assert not result['brightening'][0].any()


def test_profiles_use_one_fixed_common_sample_not_changing_means():
    hh=np.array([[[0,100]], [[-7,np.nan]], [[-6,np.nan]]],dtype='float32')
    hv=hh-10
    result=fixed_footprint_profile(hh,hv,np.ones((1,2),bool),.0001,.5)
    assert result['common_valid_pixels']==1 and result['measured_area_km2']==.0001
    assert [r['hh_baseline_delta_db'] for r in result['observations']]==[0,-7,-6]
    assert result['observations'][0]['hh_successive_delta_db'] is None
    assert result['observations'][2]['hh_successive_delta_db']==1
    assert result['observations'][2]['hh_minus_hv_db']==10
    insufficient=fixed_footprint_profile(hh,hv,np.ones((1,2),bool),.0001)
    assert insufficient['status']=='INSUFFICIENT_COMMON_VALID_PIXELS'
    assert all(r['hh_baseline_delta_db'] is None for r in insufficient['observations'])


@pytest.mark.parametrize('hh,hv',[(np.zeros((1,2,2)),np.zeros((1,2,2))),(np.zeros((3,2,2)),np.zeros((3,3,2)))])
def test_invalid_stacks_rejected(hh,hv):
    with pytest.raises(ValueError):radar_responses(hh,hv)


def test_bad_thresholds_or_areas_rejected():
    stack=np.zeros((3,2,2))
    with pytest.raises(ValueError):radar_responses(stack,stack,brightening=-1)
    with pytest.raises(ValueError):fixed_footprint_profile(stack,stack,np.ones((2,2)),0)
    with pytest.raises(ValueError):fixed_footprint_profile(stack,stack,np.zeros((2,2)),.0001)


def test_processing_release_gate_distinguishes_reprocessings():
    assert processing_release('NISAR_L2_PR_GCOV_foo_P05023_N_F_J_001')=='P05023'
    assert processing_release('NISAR_L2_PR_GCOV_foo_X05026_N_F_J_001')=='X05026'
    with pytest.raises(ValueError):processing_release('missing')


def test_pending_case_does_not_fabricate_a_manifest(tmp_path):
    case={'case_id':'river','source_files':[],'source_directory':'database/shared','granule_pattern':'*.h5'}
    record=build_case({'minimum_observations':3},case,tmp_path,tmp_path/'out')
    assert record['status']=='AWAITING_DATA' and record['local_source_count']==0
    assert not (tmp_path/'out').exists()


def test_explicit_and_shared_source_discovery_is_deduplicated(tmp_path):
    folder=tmp_path/'shared';folder.mkdir();(folder/'one.h5').touch()
    case={'source_files':['shared/one.h5'],'source_directory':'shared','granule_pattern':'*.h5'}
    assert len(sources_for(case,tmp_path))==1


@pytest.fixture
def saved_case(tmp_path,monkeypatch):
    public=tmp_path/'public';folder=public/'cases/sample/investigation';folder.mkdir(parents=True)
    observations=[]
    for i in range(3):
        observation={'observation_id':str(i),'timestamp':f'2026-08-{i+1:02d}T00:00:00Z','rasters':{}}
        for pol,offset in [('hh',0),('hv',10)]:
            name=f'{pol}_{i}.tif'
            with rasterio.open(folder/name,'w',driver='GTiff',height=12,width=12,count=1,dtype='float32',crs='EPSG:32645',transform=from_origin(300000,3100000,10,10),nodata=np.nan) as dst:dst.write(np.full((12,12),-i-offset,dtype='float32'),1)
            observation['rasters'][pol]=name
        observations.append(observation)
    manifest={'case_id':'sample','grid':{'shape':[12,12],'affine':list(from_origin(300000,3100000,10,10))[:6],'crs':'EPSG:32645','pixel_area_km2':.0001},'observations':observations}
    (folder/'manifest.json').write_text(json.dumps(manifest))
    (public/'cases/investigations.json').write_text(json.dumps({'cases':[{'case_id':'sample','status':'OBSERVATIONS_READY'}]}))
    monkeypatch.setattr(app,'PUBLIC',public)
    return folder,manifest


def test_probe_reads_native_rasters_and_records_clipped_edge_footprint(saved_case):
    folder,_=saved_case;result=probe(folder,0,0)
    assert result['window']=={'row':0,'col':0,'height':6,'width':6}
    assert result['common_valid_pixels']==36
    assert result['observations'][2]['hh_baseline_delta_db']==-2
    assert result['observations'][2]['hv_baseline_delta_db']==-2
    assert result['observations'][2]['hh_minus_hv_db']==10
    assert 80<result['longitude']<90 and 20<result['latitude']<30


def test_registry_and_manifest_endpoints_use_saved_data(saved_case):
    _,manifest=saved_case
    assert request('/api/investigations')[0]==200
    status,body=request('/api/cases/sample/investigation');assert status==200 and json.loads(body)==manifest
    status,body=request('/api/cases/sample/investigation-probe?row=5&col=6')
    assert status==200 and json.loads(body)['common_valid_pixels']==121


@pytest.mark.parametrize('query',['row=-1&col=0','row=12&col=0','row=bad&col=1','row=1'])
def test_probe_outside_or_bad_coordinates_are_rejected(saved_case,query):
    assert request('/api/cases/sample/investigation-probe?'+query)[0]==422


def test_no_silent_synthetic_data_on_missing_case(saved_case):
    assert request('/api/cases/missing/investigation')[0]==404
    assert request('/api/cases/missing/investigation-probe?row=0&col=0')[0]==404


@pytest.mark.parametrize('module',['river','wetland'])
def test_both_hydrology_build_paths_process_real_small_hdf_arrays(tmp_path,monkeypatch,module):
    """Synthetic test inputs only: exercise extraction, maps and exported native occupancy together."""
    import h5py
    from pyproj import Transformer
    from src.compute import investigation_pipeline as pipeline
    from src.ingest.timeseries import PHYSICAL_KEYS
    records={}
    for i,(hh,hv) in enumerate([(-15,-20),(-20,-27),(-15,-20)]):
        path=tmp_path/f'visit{i}.h5';grid='/science/LSAR/GCOV/grids/frequencyA'
        with h5py.File(path,'w') as hdf:
            g=hdf.create_group(grid)
            g.create_dataset('HHHH',data=np.full((10,10),10**(hh/10),dtype='float32'))
            g.create_dataset('HVHV',data=np.full((10,10),10**(hv/10),dtype='float32'))
            mask=np.ones((10,10),dtype='uint8')
            if i==2:mask[0,0]=0
            g.create_dataset('mask',data=mask);g.create_dataset('numberOfLooks',data=np.ones((10,10),dtype='float32'))
            g.create_dataset('xCoordinates',data=np.arange(500005,500100,10,dtype='float64'))
            g.create_dataset('yCoordinates',data=np.arange(2800095,2800000,-10,dtype='float64'))
            g.create_dataset('projection',data=32645)
        item={key:'same' for key in PHYSICAL_KEYS}
        item.update(product='GCOV',level='L2',source_file=str(path),acquisition_start=f'2026-08-{1+i*12:02d}T00:00:00Z',
                    granule_id=f'NISAR_L2_PR_GCOV_test_{i}_P05023_N_F_J_001',covariance_terms=['HHHH','HVHV'],
                    spacing=[10,-10],origin_center=[500005,2800095],shape=[10,10],crs='EPSG:32645',
                    grid_path=grid,layer_path=grid+'/HHHH',covariance_term='HHHH',frequency='frequencyA',doi='synthetic-fixture')
        records[path.name]=item
    monkeypatch.setattr(pipeline,'read_observation',lambda path,*args:records[Path(path).name])
    center=list(Transformer.from_crs(32645,4326,always_xy=True).transform(500050,2800050))
    config={'minimum_observations':3,'frequency':'frequencyA','terms':['HHHH','HVHV'],'median_filter_size':1,
            'minimum_valid_fraction':.8,'radar_dark_hh_db':-17.,'radar_dark_hv_db':-24.,'brightening_db':3.,
            'baseline_disturbance_db':3.,'collection':'SYNTHETIC_TEST_ONLY','source_policy':'Synthetic fixtures, never application observations'}
    case={'case_id':module,'module':module,'title':module,'question':'test','source_files':[f'visit{i}.h5' for i in range(3)],
          'source_directory':'absent','granule_pattern':'*.h5','center':center,'size_m':[100,100],'selection_note':'Synthetic test fixture'}
    out=tmp_path/'out';record=build_case(config,case,tmp_path,out)
    assert record['status']=='OBSERVATIONS_READY'
    folder=out/module/'investigation';manifest=json.loads((folder/'manifest.json').read_text())
    assert manifest['observations'][1]['response']['gain_dark_signature_km2']==pytest.approx(.01)
    with rasterio.open(folder/'dark_observation_fraction.tif') as ds:
        values=ds.read(1)
        assert values[0,0]==pytest.approx(.5)
        assert values[1,1]==pytest.approx(1/3)
    assert all((folder/manifest['observations'][1]['layers'][key]).is_file() for key in ['water','river','wetland'])


def test_selective_build_preserves_unselected_registry_and_files(tmp_path,monkeypatch):
    from src.compute import investigation_pipeline as pipeline
    cases=[{'case_id':'keep','module':'surface'},{'case_id':'build','module':'river'}]
    (tmp_path/'config.json').write_text(json.dumps({'cases':cases}))
    parent=tmp_path/'web/public/cases';parent.mkdir(parents=True)
    original={'case_id':'keep','status':'OBSERVATIONS_READY','observation_count':3,'sentinel':'preserve exact metadata'}
    (parent/'investigations.json').write_text(json.dumps({'cases':[original,{'case_id':'build','status':'AWAITING_DATA'}]}))
    target=parent/'keep/investigation';target.mkdir(parents=True);(target/'manifest.json').write_bytes(b'preserve existing bytes')
    called=[]
    def build(config,case,root,destination):
        called.append(case['case_id']);folder=destination/case['case_id']/'investigation';folder.mkdir(parents=True)
        (folder/'manifest.json').write_text('new outputs')
        return {**case,'status':'OBSERVATIONS_READY'}
    monkeypatch.setattr(pipeline,'build_case',build)
    result=pipeline.run('config.json',root=tmp_path,case_ids=['build'])
    assert called==['build'] and result['cases'][0]==original
    assert (target/'manifest.json').read_bytes()==b'preserve existing bytes'
    assert (parent/'build/investigation/manifest.json').read_text()=='new outputs'
    assert not (parent/'investigations.json.tmp').exists()


def test_selective_build_rejects_unknown_case_before_changing_outputs(tmp_path):
    from src.compute.investigation_pipeline import run
    (tmp_path/'config.json').write_text(json.dumps({'cases':[{'case_id':'known'}]}))
    with pytest.raises(ValueError,match='Unknown investigation cases'):
        run('config.json',root=tmp_path,case_ids=['missing'])
    assert not (tmp_path/'web').exists()
