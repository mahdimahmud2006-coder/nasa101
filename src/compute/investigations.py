"""Measured surface signatures and missingness-safe river/wetland observation summaries.

Thresholds describe radar responses, not calibrated water or habitat classes.
"""
import numpy as np


def validate_stack(hh, hv):
    hh, hv = np.asarray(hh, dtype=np.float32), np.asarray(hv, dtype=np.float32)
    if hh.ndim != 3 or hh.shape != hv.shape or hh.shape[0] < 2:
        raise ValueError('Matching time × row × column HH/HV arrays with at least two visits required')
    return hh, hv, np.isfinite(hh) & np.isfinite(hv)


def radar_responses(hh, hv, hh_dark=-17., hv_dark=-24., brightening=3.):
    hh, hv, valid = validate_stack(hh, hv)
    if not all(np.isfinite(v) for v in (hh_dark, hv_dark, brightening)) or brightening <= 0:
        raise ValueError('Finite thresholds and positive brightening threshold required')
    dark = valid & (hh <= hh_dark) & (hv <= hv_dark)
    baseline_common = valid & valid[0]
    bright = baseline_common & ((hh - hh[0]) >= brightening) & ((hv - hv[0]) >= brightening)
    counts = valid.sum(axis=0)
    occupancy = np.full(counts.shape, np.nan, dtype=np.float32)
    np.divide(dark.sum(axis=0), counts, out=occupancy, where=counts >= 2)
    transitions = []
    for i in range(len(hh)):
        common = valid[0] & valid[i]
        transitions.append({'common': common, 'gain': common & dark[i] & ~dark[0],
                            'loss': common & ~dark[i] & dark[0],
                            'persistent': common & dark[i] & dark[0]})
    return {'valid': valid, 'dark': dark, 'brightening': bright,
            'baseline_common': baseline_common, 'valid_visits': counts,
            'dark_observation_fraction': occupancy, 'transitions': transitions}


def fixed_footprint_profile(hh, hv, footprint, pixel_area_km2, minimum_common_fraction=.8):
    """Keep the same physical pixels across dates and channels; never average changing samples."""
    hh, hv, valid = validate_stack(hh, hv)
    footprint = np.asarray(footprint, dtype=bool)
    if footprint.shape != hh.shape[1:] or not footprint.any():
        raise ValueError('Nonempty fixed footprint must match raster grid')
    if not np.isfinite(pixel_area_km2) or pixel_area_km2 <= 0 or not 0 < minimum_common_fraction <= 1:
        raise ValueError('Positive pixel area and common fraction within (0,1] required')
    common = footprint & valid.all(axis=0)
    count, total = int(common.sum()), int(footprint.sum())
    eligible = count / total >= minimum_common_fraction
    rows = []
    for i in range(len(hh)):
        row = {'index': i, 'hh_mean_db': None, 'hv_mean_db': None,
               'hh_baseline_delta_db': None, 'hv_baseline_delta_db': None,
               'hh_successive_delta_db': None, 'hv_successive_delta_db': None,
               'hh_minus_hv_db': None}
        if eligible:
            for name, values in [('hh', hh), ('hv', hv)]:
                row[name + '_mean_db'] = float(values[i][common].astype('float64').mean())
                row[name + '_baseline_delta_db'] = float((values[i] - values[0])[common].astype('float64').mean())
                if i:
                    row[name + '_successive_delta_db'] = float((values[i] - values[i-1])[common].astype('float64').mean())
            row['hh_minus_hv_db'] = row['hh_mean_db'] - row['hv_mean_db']
        rows.append(row)
    return {'status': 'MEASURED' if eligible else 'INSUFFICIENT_COMMON_VALID_PIXELS',
            'footprint_pixels': total, 'common_valid_pixels': count,
            'common_valid_fraction': count / total, 'footprint_area_km2': total * pixel_area_km2,
            'measured_area_km2': count * pixel_area_km2, 'observations': rows,
            'interpretation': 'Mean filtered log-backscatter on a fixed common-valid footprint. dB differences are not ground displacement. No cause or calibrated confidence is inferred.'}
