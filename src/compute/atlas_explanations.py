"""Bind exploratory rules to the atlas footprint, reference and dated context."""
import json

import numpy as np
from affine import Affine
from rasterio.crs import CRS

from src.compute.explanation_fit import explanation_fit

MIN_NATIVE_RULE_SUPPORT = .8


def explanation_context(path, manifest):
    """Map dated context through canonical granule identity, including legacy Nepal IDs."""
    case_folder = path.parent.parent
    folder = case_folder/'context-v2'
    context = json.loads((folder/'manifest.json').read_text())
    if context['case_id'] != manifest['case_id']:
        raise RuntimeError('Explanation context belongs to another case')
    original = (manifest if path.parent.name == 'investigation' else
                json.loads((case_folder/'investigation/manifest.json').read_text()))
    if original['case_id'] != manifest['case_id']:
        raise RuntimeError('Explanation context source belongs to another case')
    by_granule = {(v['timestamp'], v['source_granule_id']): v['observation_id']
                  for v in manifest['observations']}
    by_legacy_id = {(v['observation_id'], v['timestamp']): by_granule.get((v['timestamp'], v['source_granule_id']))
                    for v in original['observations']}

    def bound(rows):
        return {current: row for row in rows
                if (current := by_legacy_id.get((row['observation_id'], row['timestamp']))) is not None}

    controls = context['radiometric_controls']
    return folder, context, {
        'rain': bound(context['rain']),
        'controls': bound(controls) if controls and controls[0]['timestamp'] == manifest['reference_timestamp'] else {},
    }


def footprint_median_slope(common, radar_grid, terrain_grid, slope, col_offset=0, row_offset=0):
    """Sample accepted DEM slope at each common-valid radar cell center."""
    if CRS.from_string(radar_grid['crs']) != CRS.from_string(terrain_grid['crs']):
        raise RuntimeError('Radar and slope must share the accepted projection')
    to_terrain = ~Affine(*terrain_grid['affine']) @ Affine(*radar_grid['affine'])
    rows, cols = np.nonzero(common)
    cols, rows = to_terrain @ (cols + (col_offset+.5), rows + (row_offset+.5))
    cols, rows = np.floor(cols).astype(int), np.floor(rows).astype(int)
    keep = (cols >= 0) & (cols < slope.shape[1]) & (rows >= 0) & (rows < slope.shape[0])
    values = slope[rows[keep], cols[keep]]
    valid = values[np.isfinite(values)]
    # Keep the footprint scope intact; do not substitute a smaller slope-only sample.
    return float(np.median(valid)) if valid.size and valid.size == rows.size else None


def evaluate_atlas_visit(row, reference_utc, hh, reference_hh, median_slope, context, rules):
    """Use measured dB values and retain unavailable inputs as null."""
    oid = row['observation_id']
    dh, dv, dc = (row[k+'_reference_delta_db'] for k in ('hh', 'hv', 'cpr'))
    rain = context['rain'].get(oid, {})
    ctrl = context['controls'].get(oid, {})
    offsets = [abs(ctrl[k]) for k in ('hh_baseline_shift_db', 'hv_baseline_shift_db')
               if ctrl.get(k) is not None]
    facts = {
        'hh_last_db': row['hh_mean_db'], 'hv_last_db': row['hv_mean_db'],
        'hh_delta_db': dh, 'hv_delta_db': dv,
        'hh_change_abs_db': abs(dh), 'hv_change_abs_db': abs(dv), 'cpr_change_abs_db': abs(dc),
        'mean_abs_hh_change_db': float(np.abs(hh.astype('float64') - reference_hh).mean()),
        'median_slope_degrees': median_slope,
        'rain_72h_mm': rain.get('imerg_72h_mm') if rain.get('status') != 'unavailable' else None,
        'paired_darkening': dh <= -3 and dv <= -3,
        'control_offset_abs_db': max(offsets) if offsets else None,
    }
    return {**explanation_fit(facts, rules), 'observation_id': oid, 'timestamp': row['timestamp'],
            'reference_timestamp': reference_utc, 'common_valid_pixels': int(hh.size), 'facts': facts}
