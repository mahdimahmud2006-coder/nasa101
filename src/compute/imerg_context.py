"""Screen and integrate an explicitly admitted IMERG Final V07 rainfall window."""
import re
from datetime import datetime, timezone

import h5py
import numpy as np
from pyproj import Transformer
from shapely.geometry import box
from shapely.ops import transform

from src.compute.context_v2 import integrate_rain, utc
from src.ingest.environment import sha


def imerg_window(root, manifest_path, approved_sha256, footprint_wgs84, window):
    """Area-weight complete native cells on one fixed geographic footprint."""
    import json
    from pathlib import Path

    if sha(manifest_path) != approved_sha256:
        raise ValueError('IMERG admission manifest checksum mismatch')
    manifest = json.loads(Path(manifest_path).read_text())
    if (manifest['schemaVersion'], manifest['collection'], manifest['lineage']) != (1, 'GPM_3IMERGHH.07', 'approved'):
        raise ValueError('Expected a reviewed Final V07 collection and lineage')
    minimum_quality = manifest['minimumQualityIndex']
    if not isinstance(minimum_quality, (int,float)) or not np.isfinite(minimum_quality) or minimum_quality < 0:
        raise ValueError('A finite nonnegative quality-index cutoff is required')
    start = utc(window['start_inclusive_utc']).timestamp()
    end = utc(window['end_exclusive_utc']).timestamp()
    if end <= start or footprint_wgs84.is_empty or not footprint_wgs84.is_valid:
        raise ValueError('Positive time window and a valid footprint required')
    expected = range(int(start//1800)*1800, int(np.ceil(end/1800))*1800, 1800)
    by_time = {}
    for granule in manifest['granules']:
        when = int(utc(granule['startUtc']).timestamp())
        if when in by_time:
            raise ValueError('Duplicate admitted IMERG bin')
        by_time[when] = granule
    bins = [(t,by_time[t]) for t in expected if t in by_time]
    result = dict(status='unavailable',totalMm=None,window=window,unit='mm',resolutionDegrees=.1,
                  expectedBins=len(expected),observedBins=len(bins),validBins=0,
                  completeAreaFraction=None,sourceIds=[g['id'] for _,g in bins],manifestSha256=approved_sha256)
    if not bins:
        return result
    root = Path(root).resolve()
    project = Transformer.from_crs(4326, 6933, always_xy=True).transform
    footprint = transform(project, footprint_wgs84)
    lon0,lat0,lon1,lat1 = footprint_wgs84.bounds
    grid_key, weights = None,None
    rates = []
    for timestamp, record in bins:
        path = (root/record['file']).resolve()
        match = re.fullmatch(r'3B-HHR\.MS\.MRG\.3IMERG\.(\d{8})-S(\d{6})-E\d{6}\.\d{4}\.V07[AB]\.HDF5', path.name)
        if not path.is_relative_to(root) or not match or path.name != record['id'] or sha(path)!=record['sha256']:
            raise ValueError('Unrecognized or changed admitted IMERG granule')
        filename_time = datetime.strptime(''.join(match.groups()), '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
        if filename_time.timestamp() != timestamp:
            raise ValueError('IMERG granule filename disagrees with its admitted bin')
        with h5py.File(path) as hdf:
            grid = hdf['Grid']
            bounds = grid['time_bnds'][()].ravel()
            if not np.array_equal(bounds,[timestamp,timestamp+1800]):
                raise ValueError('IMERG header does not match the admitted half hour')
            lon,lat = grid['lon'][:],grid['lat'][:]
            if not all(len(axis)>1 and np.allclose(np.diff(axis),.1,atol=3e-5,rtol=0) for axis in (lon,lat)):
                raise ValueError('Expected ascending IMERG native 0.1° axes')
            key = (lon.tobytes(),lat.tobytes())
            if grid_key is not None and key != grid_key:
                raise ValueError('IMERG grid changed across the requested bins')
            xs = np.flatnonzero((lon+.05>lon0)&(lon-.05<lon1))
            ys = np.flatnonzero((lat+.05>lat0)&(lat-.05<lat1))
            if not len(xs) or not len(ys):
                raise ValueError('IMERG grid does not overlap the requested footprint')
            if weights is None:
                weights = np.array([[footprint.intersection(transform(project,box(lon[x]-.05,lat[y]-.05,
                                    lon[x]+.05,lat[y]+.05))).area for y in ys] for x in xs])
                grid_key = key
            field, quality = grid['precipitation'],grid['precipitationQualityIndex']
            units = field.attrs.get('units',field.attrs.get('Units'))
            if field.shape != (1,len(lon),len(lat)) or quality.shape != field.shape or units not in ('mm/hr',b'mm/hr'):
                raise ValueError('Expected matching V07 rate and quality fields')
            selection = (0,slice(xs[0],xs[-1]+1),slice(ys[0],ys[-1]+1))
            values, scores = field[selection], quality[selection]
            valid = np.isfinite(values)&(values>=0)&np.isfinite(scores)&(scores>=minimum_quality)
            for dataset, data in ((field,values),(quality,scores)):
                fill = dataset.attrs.get('_FillValue')
                if fill is not None:
                    valid &= data!=fill
            rates.append(np.where(valid,values,np.nan))
    samples = np.stack(rates)
    result['validBins'] = int((np.isfinite(samples)&(weights>0)).any(axis=(1,2)).sum())
    complete = np.isfinite(samples).all(axis=0)&(weights>0)
    if len(bins) != len(expected):
        complete[:] = False
    covered = float(weights[complete].sum())
    result['completeAreaFraction'] = min(1.,covered/footprint.area)
    if covered:
        mean_rates = np.average(samples[:,complete],weights=weights[complete],axis=1)
        result.update(status='measured',totalMm=integrate_rain([t for t,_ in bins],mean_rates,window)['total_mm'])
    return result
