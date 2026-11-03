"""Independent numeric fixtures for the diagonal-only branch; no external requests."""
import json
from pathlib import Path
import numpy as np
import pytest
from src.compute.dualpol import cpr_db,signed_difference,stretch,composite,hint_masks,threshold_sensitivity,profile_cpr
from src.export.dualpol_render import palette_rgba,load_palettes,css_gradient,rgba_cog
from affine import Affine
import rasterio

LIMITS={'hh':[-30,0],'hv':[-40,-5],'ratio':[0,20]}
HINTS={'hh_low_db':-17,'hv_low_db':-24,'hh_rise_db':3,'hv_stable_abs_db':1,'hv_rise_db':3}


def test_cpr_log_power_identity_sign_and_missing_values():
    hh_power=np.array([[.1,.01,np.nan,0]])
    hv_power=np.array([[.01,.001,.1,.01]])
    with np.errstate(divide='ignore',invalid='ignore'):
        hh=10*np.log10(hh_power);hv=10*np.log10(hv_power)
        expected=10*np.log10(hv_power[:,:2]/hh_power[:,:2])
    actual=cpr_db(hh,hv)
    np.testing.assert_allclose(actual[:,:2],expected,atol=1e-6)
    assert np.isnan(actual[0,2:]).all()
    np.testing.assert_allclose(actual[:,:2],-(hh-hv)[:,:2])


def test_baseline_and_successive_preserve_endpoint_support_and_zero():
    a=np.array([[1,2,np.nan]],dtype='float32');b=np.array([[4,np.nan,8]],dtype='float32')
    result=signed_difference(b,a)
    assert result[0,0]==3 and np.isnan(result[0,1:]).all()
    assert signed_difference(a,a)[0,0]==0
    assert np.isnan(signed_difference(b,a,np.zeros(a.shape,bool))).all()


def test_fixed_composite_has_reproducible_known_rgb_and_transparent_missing():
    hh=np.array([[-30,0,np.nan],[-15,-15,-15]],dtype='float32')
    hv=np.array([[-40,-5,-20],[-25,-25,-25]],dtype='float32')
    rgba=composite(hh,hv,LIMITS)
    np.testing.assert_array_equal(rgba[0,0],[0,0,128,255])
    np.testing.assert_array_equal(rgba[0,1],[255,255,64,255])
    np.testing.assert_array_equal(rgba[0,2],[0,0,0,0])
    np.testing.assert_array_equal(rgba[1,0],rgba[1,1])
    # Neighbors/date distributions do not change a pixel's fixed stretch.
    changed=composite(hh[1:,:1],hv[1:,:1],LIMITS)
    np.testing.assert_array_equal(changed[0,0],rgba[1,0])
    np.testing.assert_array_equal(stretch(np.array([-100,100]),[-30,0]),[0,255])


def test_hint_boundaries_alternatives_overlap_and_baseline_missing():
    hh=np.array([[-17,-10,-20,np.nan,-30]],dtype='float32');hv=np.array([[-24,-20,-24,-24,-30]],dtype='float32')
    bh=np.array([[-20,-13,-20,-20,np.nan]],dtype='float32');bv=np.array([[-24,-21,-27,-24,-30]],dtype='float32')
    result=hint_masks(hh,hv,bh,bv,HINTS)
    np.testing.assert_array_equal(result['bits'],[[3,2,5,255,1]])
    assert not result['change_valid'][0,-1]
    first=hint_masks(hh,hv,None,None,HINTS)
    assert first['change_valid'] is None
    np.testing.assert_array_equal(first['bits'],[[1,0,1,255,1]])


def test_sensitivity_exact_inclusive_counts_fixed_support_and_monotonicity():
    hh=np.array([[-20,-17,-14,np.nan]],dtype='float32');hv=np.array([[-27,-24,-21,-30]],dtype='float32')
    common=np.array([[True,True,False,True]])
    cuts_h=[-20,-17,-14];cuts_v=[-27,-24,-21]
    row=threshold_sensitivity(hh,hv,common,.0001,cuts_h,cuts_v)
    expected=[[int(((hh<=h)&(hv<=v)&common&np.isfinite(hh)&np.isfinite(hv)).sum()) for v in cuts_v] for h in cuts_h]
    assert row['candidate_pixels']==expected
    assert row['common_valid_pixels']==2
    assert (np.diff(row['candidate_pixels'],axis=0)>=0).all()
    assert (np.diff(row['candidate_pixels'],axis=1)>=0).all()
    assert row['candidate_area_km2'][1][1]==.0002


def test_all_missing_is_unavailable_not_zero_or_coloured_data():
    missing=np.full((2,2),np.nan,dtype='float32')
    assert np.isnan(cpr_db(missing,missing)).all()
    assert not composite(missing,missing,LIMITS)[...,3].any()
    row=threshold_sensitivity(missing,missing,np.ones((2,2),bool),.0001,[-18,-17],[-25,-24])
    assert row['candidate_pixels'] is None and row['candidate_area_km2'] is None
    assert row['status']=='unavailable'


def test_profile_arithmetic_uses_identical_means_and_preserves_nulls():
    original={'observations':[{'hh_mean_db':-17,'hv_mean_db':-24,'hh_baseline_delta_db':-7,'hv_baseline_delta_db':-2,'hh_successive_delta_db':None,'hv_successive_delta_db':None}]}
    result=profile_cpr(original)['observations'][0]
    assert result['cpr_mean_db']==-7 and result['cpr_baseline_delta_db']==5
    assert result['cpr_successive_delta_db'] is None
    assert 'cpr_mean_db' not in original['observations'][0]


def test_vik_symmetric_scale_maps_exact_zero_to_palette_midpoint():
    palettes=load_palettes('data/palettes/v1');vik=palettes['vik']
    values=palette_rgba(np.array([[-8,0,8,np.nan]]),[-8,8],vik)
    np.testing.assert_array_equal(values[0,0,:3],np.rint(vik[0]*255).astype('uint8'))
    np.testing.assert_array_equal(values[0,1,:3],np.rint((vik[127]+vik[128])/2*255).astype('uint8'))
    np.testing.assert_array_equal(values[0,2,:3],np.rint(vik[-1]*255).astype('uint8'))
    assert values[0,3,3]==0
    assert '50.0%' in css_gradient(vik)
    assert palette_rgba(np.array([0.]),[-8,8],vik).shape==(1,4)


def test_rgb_cog_retains_native_grid_alpha_and_rgb_metadata(tmp_path):
    rgba=composite(np.array([[-30,np.nan],[0,-15]]),np.array([[-40,-20],[-5,-25]]),LIMITS)
    path=tmp_path/'rgba.tif';transform=Affine(10,0,500000,0,-10,2800000)
    rgba_cog(path,rgba,transform,'EPSG:32646')
    with rasterio.open(path) as ds:
        assert ds.count==4 and ds.transform==transform
        assert ds.tags(ns='IMAGE_STRUCTURE')['LAYOUT']=='COG'
        np.testing.assert_array_equal(ds.read(),np.moveaxis(rgba,-1,0))
        assert ds.colorinterp[-1].name=='alpha'
        assert ds.nodata is None


@pytest.mark.parametrize('limits',[[0,0],[1,-1],[0,np.nan]])
def test_bad_stretch_rejected(limits):
    with pytest.raises(ValueError):stretch(np.ones((2,2)),limits)


def test_incompatible_grids_and_unsorted_sweep_rejected():
    with pytest.raises(ValueError):cpr_db(np.zeros((2,2)),np.zeros((3,2)))
    with pytest.raises(ValueError):threshold_sensitivity(np.ones((2,2)),np.ones((2,2)),np.ones((2,2),bool),.1,[-17,-18],[-24])


def test_scientific_builder_refuses_to_replace_published_products():
    from src.compute.dualpol_pipeline import run
    path=Path('web/public/cases/nepal_surface/dualpol-v1/manifest.json')
    before=path.read_bytes()
    with pytest.raises(FileExistsError,match='Refusing to replace'):run()
    assert path.read_bytes()==before
