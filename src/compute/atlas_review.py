"""Footprint-level review measurements and a gated bank-transect primitive."""
from math import isclose, isfinite

import numpy as np
from pyproj import CRS
from shapely.geometry import LineString

HH_DARK_DB = -17
HV_DARK_DB = -24


def radar_review_visit(hh, hv, fixed):
    """Keep one all-visit paired-valid footprint and classify each actual visit."""
    h, v = hh[fixed], hv[fixed]
    if not h.size:
        return {'hhDb': None, 'hvDb': None, 'pairedPixels': 0, 'darkPixels': None, 'matches': None}
    h_mean, v_mean = float(h.mean(dtype='float64')), float(v.mean(dtype='float64'))
    return {'hhDb': h_mean, 'hvDb': v_mean, 'pairedPixels': int(h.size),
            'darkPixels': int(((h <= HH_DARK_DB) & (v <= HV_DARK_DB)).sum()),
            'matches': h_mean <= HH_DARK_DB and v_mean <= HV_DARK_DB}


def bank_transect_change(transect, earlier, later, crs, error_bounds_m, resolution_m):
    """Signed metric shift along an oriented transect; inputs require prior validation."""
    projection = CRS.from_user_input(crs)
    if not projection.is_projected or any(a.unit_conversion_factor != 1 for a in projection.axis_info[:2]):
        raise ValueError('Bank review requires a projected metric CRS')
    if len(error_bounds_m) != 3 or not all(isfinite(v) and v >= 0 for v in error_bounds_m):
        raise ValueError('Supply earlier and later delineation bounds and the relative registration bound')
    if not isfinite(resolution_m) or resolution_m <= 0:
        raise ValueError('Supply the effective spatial resolution')
    if (not isinstance(transect, LineString) or len(transect.coords) != 2 or
            not transect.is_valid or not isfinite(transect.length) or transect.length <= 0):
        raise ValueError('Supply a straight oriented transect')
    distances = []
    for bank in (earlier, later):
        if bank.geom_type not in ('LineString', 'MultiLineString') or not bank.is_valid or not bank.is_simple:
            return {'status': 'ambiguous_crossing', 'movementM': None}
        crossing = transect.intersection(bank)
        if crossing.geom_type != 'Point' or crossing.is_empty or not transect.crosses(bank):
            return {'status': 'ambiguous_crossing', 'movementM': None}
        distances.append(transect.project(crossing))
    shift = distances[1] - distances[0]
    bound = sum(error_bounds_m)
    limit = max(bound, resolution_m)
    if abs(shift) <= limit or isclose(abs(shift), limit, abs_tol=1e-8):
        return {'status': 'unresolved', 'movementM': None, 'uncertaintyBoundM': bound}
    return {'status': 'resolved', 'movementM': shift, 'uncertaintyBoundM': bound,
            'direction': 'along_transect' if shift > 0 else 'against_transect'}


def review_location(mask, transform, crs):
    """Choose the in-footprint cell closest to its grid centroid for navigation."""
    from pyproj import Transformer

    rows, cols = np.where(mask)
    if not rows.size:
        return None
    near = ((rows-rows.mean())**2+(cols-cols.mean())**2).argmin()
    row, col = int(rows[near]), int(cols[near])
    x, y = transform @ (col+.5, row+.5)
    lon, lat = Transformer.from_crs(crs, 4326, always_xy=True).transform(x, y, errcheck=True)
    return {'latitude': lat, 'longitude': lon, 'row': row, 'col': col,
            'boundsPixel': [int(cols.min()), int(rows.min()), int(cols.max()+1), int(rows.max()+1)],
            'scope': 'Representative footprint cell center for navigation; field position requires survey.'}
