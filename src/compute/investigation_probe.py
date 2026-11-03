"""Read a reproducible fixed 11×11 native-pixel neighborhood from saved HH/HV rasters."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from pyproj import Transformer
from src.compute.investigations import fixed_footprint_profile


def probe(directory, row, col):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    height,width=manifest['grid']['shape']
    if not 0<=row<height or not 0<=col<width:
        raise ValueError('Selected pixel outside the case')
    r,c=max(0,row-5),max(0,col-5)
    h,w=min(height,row+6)-r,min(width,col+6)-c
    window=Window(c,r,w,h)
    channels={'hh':[],'hv':[]}
    for obs in manifest['observations']:
        for pol in channels:
            with rasterio.open(directory/obs['rasters'][pol]) as source:
                channels[pol].append(source.read(1,window=window))
    result=fixed_footprint_profile(np.stack(channels['hh']),np.stack(channels['hv']),np.ones((h,w),bool),manifest['grid']['pixel_area_km2'])
    for record,observation in zip(result['observations'],manifest['observations']):
        record.update(observation_id=observation['observation_id'],timestamp=observation['timestamp'])
    a,b,c0,d,e,f=manifest['grid']['affine']
    x,y=a*(col+.5)+b*(row+.5)+c0,d*(col+.5)+e*(row+.5)+f
    lon,lat=Transformer.from_crs(manifest['grid']['crs'],'EPSG:4326',always_xy=True).transform(x,y)
    return {'case_id':manifest['case_id'],'record_version':manifest.get('record_version','original'),'label':f'Fixed neighborhood at {lat:.5f}° N, {lon:.5f}° E',
            'selection':'User-selected native neighborhood, clipped at grid edges; not an independent event reference.',
            'center_row':row,'center_col':col,'longitude':lon,'latitude':lat,
            'window':{'row':r,'col':c,'height':h,'width':w},**result}
