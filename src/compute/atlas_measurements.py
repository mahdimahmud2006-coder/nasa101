"""Additive atlas measurements; accepted processing modules remain frozen."""
import json
import numpy as np
from pyproj import CRS
from affine import Affine
from src.compute.area import pixel_area_km2
from src.compute.dualpol import channels


def footprint_geometry(vertices, transform, crs):
    """Continuous grid-coordinate boundary, distinct from valid pixel-center support."""
    from pyproj import Geod, Transformer
    from shapely.geometry import Polygon

    points = np.asarray(vertices, dtype='float64')
    if points.ndim != 2 or points.shape[1] != 2 or not 3 <= len(points) <= 200 or not np.isfinite(points).all():
        raise ValueError('Expected a polygon with 3 to 200 finite grid vertices')
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('Invalid footprint boundary')
    projected_km2 = polygon.area * pixel_area_km2(transform, crs)
    # Subdivide each straight projected edge before inverse projection; adjacent
    # geographic vertices are integrated as geodesic arcs on the WGS84 ellipsoid.
    shape = CRS.from_user_input(crs)
    units = np.array([axis.unit_conversion_factor for axis in shape.axis_info[:2]])
    xy = np.array([transform @ tuple(pt) for pt in points])
    edge_points = []
    for a, b in zip(xy, np.roll(xy, -1, axis=0)):
        count = max(1, int(np.ceil(np.linalg.norm((b-a)*units)/250)))
        if count > 10000:
            raise ValueError('Edge exceeds supported study-window extent')
        edge_points.extend(np.linspace(a,b,count,endpoint=False))
    x,y = np.asarray(edge_points).T
    lon,lat = Transformer.from_crs(shape, 4326, always_xy=True).transform(x,y,errcheck=True)
    area,_ = Geod(ellps='WGS84').polygon_area_perimeter(lon,lat)
    return {'projected_km2':float(projected_km2),'ellipsoidal_km2':abs(float(area))/1e6,
            'method':'Drawn boundary; WGS84 ellipsoid, projected edges sampled at <=250 m. Excludes terrain surface area; separate from valid pixel counts.'}


def crosspol_fraction(hh_db, hv_db):
    """HV / (HH + HV) in linear power, derived from paired dB intensities."""
    hh,hv,valid=channels(hh_db,hv_db)
    result=np.full(hh.shape,np.nan,dtype='float32')
    # Stable logistic form, also valid when HV exceeds HH.
    d=(hv[valid].astype('float64')-hh[valid])*np.log(10)/10
    result[valid]=np.exp(-np.logaddexp(0.,-d))
    return result


def dualpol_summary(hh_db, hv_db, support):
    """Paired footprint means in dB and the mean of per-pixel power fractions."""
    hh, hv, paired = channels(hh_db, hv_db)
    valid = paired & support
    count = int(valid.sum())
    if not count:
        return dict(validPixels=0, hhDb=None, hvDb=None, cprDb=None, powerShare=None, crossDominantPixels=0)
    h, v = hh[valid], hv[valid]
    hh_mean, hv_mean = float(h.mean(dtype='float64')), float(v.mean(dtype='float64'))
    return dict(validPixels=count, hhDb=hh_mean, hvDb=hv_mean, cprDb=hv_mean-hh_mean,
                powerShare=float(crosspol_fraction(h,v).mean(dtype='float64')),
                crossDominantPixels=int((v>h).sum()))


def polygon_with_boundary(case,vertices,root,directory):
    from src.compute.investigation_dna import polygon_evidence
    result=polygon_evidence(case,vertices,root,directory)
    grid=json.loads((directory/'investigation/manifest.json').read_text())['grid']
    result['profile']['boundary_area']=footprint_geometry(vertices,Affine(*grid['affine']),grid['crs'])
    return result
