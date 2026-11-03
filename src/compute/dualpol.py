"""Diagonal-intensity proxies and descriptive signatures, never a decomposition."""
import numpy as np


def channels(hh, hv):
    hh, hv = np.asarray(hh, dtype=np.float32), np.asarray(hv, dtype=np.float32)
    if hh.shape != hv.shape:
        raise ValueError('HH and HV must share one native grid')
    return hh, hv, np.isfinite(hh) & np.isfinite(hv)


def cpr_db(hh, hv):
    hh, hv, valid = channels(hh, hv)
    return np.where(valid, hv-hh, np.nan).astype('float32')


def signed_difference(current, reference, support=None):
    current, reference = np.asarray(current), np.asarray(reference)
    if current.shape != reference.shape:
        raise ValueError('Differences require identical grids')
    valid = np.isfinite(current) & np.isfinite(reference)
    if support is not None:
        if np.shape(support) != current.shape:
            raise ValueError('Support grid mismatch')
        valid &= support
    return np.where(valid, current-reference, np.nan).astype('float32')


def stretch(values, limits):
    low, high = limits
    if not np.isfinite([low, high]).all() or high <= low:
        raise ValueError('Finite increasing stretch limits required')
    safe = np.where(np.isfinite(values), values, low)
    return np.rint(np.clip((safe-low)/(high-low), 0, 1)*255).astype('uint8')


def composite(hh, hv, limits):
    hh, hv, valid = channels(hh, hv)
    rgb = np.stack([stretch(hh, limits['hh']), stretch(hv, limits['hv']), stretch(hh-hv, limits['ratio'])], axis=-1)
    rgb[~valid] = 0
    return np.dstack([rgb, valid.astype('uint8')*255])


def hint_masks(hh, hv, baseline_hh, baseline_hv, settings):
    hh, hv, valid = channels(hh, hv)
    code = np.zeros(hh.shape, dtype='uint8')
    low = valid & (hh <= settings['hh_low_db']) & (hv <= settings['hv_low_db'])
    code[low] |= 1
    common = None
    if baseline_hh is not None and baseline_hv is not None:
        bh, bv, baseline_valid = channels(baseline_hh, baseline_hv)
        if bh.shape != hh.shape:
            raise ValueError('Baseline hint grid mismatch')
        common = valid & baseline_valid
        dh, dv = hh-bh, hv-bv
        code[common & (dh >= settings['hh_rise_db']) & (np.abs(dv) <= settings['hv_stable_abs_db'])] |= 2
        code[common & (dv >= settings['hv_rise_db'])] |= 4
    code[~valid] = 255
    return {'bits': code, 'current_valid': valid, 'change_valid': common}


def threshold_sensitivity(hh, hv, common, area, hh_cutoffs, hv_cutoffs):
    """Exact 2-D inclusive cutoff counts on one preselected fixed footprint."""
    hh, hv, valid = channels(hh, hv)
    hcut, vcut = np.asarray(hh_cutoffs), np.asarray(hv_cutoffs)
    if np.shape(common) != hh.shape or not np.isfinite(area) or area <= 0:
        raise ValueError('Fixed support and positive pixel area required')
    if any(len(x)==0 or not np.isfinite(x).all() or np.any(np.diff(x)<=0) for x in (hcut,vcut)):
        raise ValueError('Finite strictly increasing cutoff arrays required')
    support = valid & common
    n = int(support.sum())
    # side=left preserves the inclusive <= comparison at exact boundaries.
    hbin = np.searchsorted(hcut, hh[support], side='left')
    vbin = np.searchsorted(vcut, hv[support], side='left')
    histogram = np.bincount(hbin*(len(vcut)+1)+vbin, minlength=(len(hcut)+1)*(len(vcut)+1)).reshape(len(hcut)+1,len(vcut)+1)
    counts = histogram.cumsum(0).cumsum(1)[:len(hcut),:len(vcut)]
    return {'common_valid_pixels': n, 'common_valid_area_km2': n*area,
            'hh_cutoffs_db': hcut.tolist(), 'hv_cutoffs_db': vcut.tolist(),
            'candidate_pixels': counts.tolist() if n else None,
            'candidate_area_km2': (counts*area).tolist() if n else None,
            'status': 'measured' if n else 'unavailable',
            'definition': 'HH <= HH cutoff AND HV <= HV cutoff on paired-valid pixels shared by ALL observed visits; exploratory, uncalibrated.'}


def profile_cpr(profile):
    """Linearity on the same fixed support; a mean dB ratio, not ratio of mean powers."""
    result = {**profile, 'observations': [dict(r) for r in profile['observations']]}
    for r in result['observations']:
        for suffix in ('mean_db', 'baseline_delta_db', 'successive_delta_db'):
            h, v = r.get('hh_'+suffix), r.get('hv_'+suffix)
            r['cpr_'+suffix] = None if h is None or v is None else v-h
    result['cpr_definition'] = 'HV_dB - HH_dB on the existing fixed common-valid footprint. Difference of filtered log-powers, not a polarimetric decomposition or ratio of spatial mean powers.'
    return result
