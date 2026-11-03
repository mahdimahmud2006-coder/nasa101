from datetime import datetime,timezone
import numpy as np
import pytest
from src.compute.context_v2 import rain_window,integrate_rain,geometry_candidates,stable_targets

def test_exact_utc_partial_bins_preserve_total():
    window=rain_window('2026-08-17T23:21:32Z',hours=24)
    start=datetime.fromisoformat(window['start_inclusive_utc'].replace('Z','+00:00')).timestamp();end=start+86400
    times=np.arange(start//1800*1800,np.ceil(end/1800)*1800,1800,dtype='int64')
    result=integrate_rain(times,np.ones(len(times))*2,window)
    assert result['bins']==49 and result['total_mm']==pytest.approx(48)
    assert window['end_exclusive_utc']=='2026-08-17T23:21:32Z'

def test_missing_rain_not_zero_and_prior_window_exact():
    w=rain_window('2026-08-17T23:21:32Z',start='2026-07-24T23:21:33Z')
    assert w['duration_seconds']==24*86400-1
    assert integrate_rain([],[],w)['total_mm'] is None
    with pytest.raises(ValueError):integrate_rain([1,1],[0,0],w)
    with pytest.raises(ValueError):rain_window('2026-01-01T00:00:00Z',hours=0)

def test_flat_geometry_and_opposing_range_slopes():
    flat=np.zeros((5,5));inc=np.full((5,5),40.);east=np.ones((5,5));north=np.zeros((5,5))
    assert not geometry_candidates(flat,30,inc,east,north).any()
    slope=np.tile(np.arange(5)*100.,(5,1))
    assert np.all((geometry_candidates(slope,30,inc,east,north)&4)!=0)
    assert np.all((geometry_candidates(-slope,30,inc,east,north)&2)!=0)
    inc[0,0]=np.nan;assert geometry_candidates(flat,30,inc,east,north)[0,0]==255

def test_control_selection_uses_only_first_date_and_terrain():
    h=np.arange(100).reshape(10,10).astype('float32');v=h-5;z=np.arange(100).reshape(10,10);s=np.zeros((10,10))
    first,record=stable_targets(h,v,z,s);again,_=stable_targets(h,v,z,s)
    np.testing.assert_array_equal(first,again);assert record['selected_pixels']==15
    assert not stable_targets(h,v,z,s+30)[0].any()
