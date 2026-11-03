import numpy as np
import pytest
from src.compute.reference_design import choose_reference,hls_quality,descriptive_overlap

def test_reference_tolerance_inclusive_and_ties_fixed():
    candidates=[{'id':'b','timestamp':'2026-08-20T00:00:00Z','cloud_cover':1},
                {'id':'a','timestamp':'2026-08-20T00:00:00Z','cloud_cover':1}]
    assert choose_reference(candidates,'2026-08-19T00:00:00Z',86400)['id']=='a'
    assert choose_reference(candidates,'2026-08-19T00:00:00Z',86399) is None
    candidates[0]['cloud_cover']=0
    assert choose_reference(candidates,'2026-08-19T00:00:00Z',86400)['id']=='b'

def test_cloud_water_fill_and_aerosol_bits():
    clear,water=hls_quality(np.array([0,32,2,4,8,16,255,96],dtype='uint8'))
    assert clear.tolist()==[True,True,False,False,False,False,False,True]
    assert water[:2].tolist()==[False,True]

def test_overlap_retains_zero_and_missing_and_masks():
    r=descriptive_overlap([1,1,0],[0,1,1],[1,0,1],.0009)
    assert r['intersection_area_km2']==0 and r['reference_water_area_km2']==.0009
    assert not {'precision','recall','IoU','accuracy'}&r.keys()
    assert descriptive_overlap([1],[1],[0],.0009)['reference_water_area_km2'] is None
    with pytest.raises(ValueError):descriptive_overlap([1],[1,0],[1],1)

def test_frozen_design_hashes_and_published_coverage():
    from src.compute.validate_references import validate
    result=validate()
    assert result['assessable_comparisons']==14
    assert result['unavailable_comparisons']==40
