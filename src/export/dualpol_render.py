"""Pinned offline scientific palettes and fixed-scale radar composites."""
import json
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image
import rasterio
from rasterio.enums import ColorInterp
from rasterio.shutil import copy as copy_raster


def load_palettes(directory):
    return {name:np.asarray(json.loads((Path(directory)/(name+'.json')).read_text()),dtype='float64') for name in ('cividis','vik')}


def palette_rgba(values, limits, palette):
    low,high=limits
    if high<=low or not np.isfinite(limits).all():raise ValueError('Invalid palette limits')
    valid=np.isfinite(values)
    normalized=np.clip((np.where(valid,values,low)-low)/(high-low),0,1)
    position=normalized*(len(palette)-1)
    lower=np.floor(position).astype('int32');upper=np.minimum(lower+1,len(palette)-1)
    fraction=(position-lower)[...,None]
    rgb=np.rint((palette[lower]*(1-fraction)+palette[upper]*fraction)*255).astype('uint8')
    rgb[~valid]=0
    return np.concatenate([rgb,(valid.astype('uint8')*255)[...,None]],axis=-1)


def preview(path, rgba, size=1100):
    image=Image.fromarray(rgba)
    image.thumbnail((size,size),Image.Resampling.NEAREST)
    image.save(path)


def rgba_cog(path, rgba, affine, crs):
    with tempfile.TemporaryDirectory(prefix='terrapulse-rgb-') as temporary:
        source=Path(temporary)/'rgb.tif'
        with rasterio.open(source,'w',driver='GTiff',width=rgba.shape[1],height=rgba.shape[0],count=4,dtype='uint8',transform=affine,crs=crs) as ds:
            ds.write(np.moveaxis(rgba,-1,0));ds.colorinterp=(ColorInterp.red,ColorInterp.green,ColorInterp.blue,ColorInterp.alpha)
            for i,name in enumerate(['R: HH dB fixed stretch','G: HV dB fixed stretch','B: HH-HV dB fixed stretch','A: paired-valid support'],1):ds.set_band_description(i,name)
        copy_raster(source,path,driver='COG',BLOCKSIZE=256,COMPRESS='DEFLATE',OVERVIEW_RESAMPLING='NEAREST')


def css_gradient(palette):
    stops=[]
    for t in np.linspace(0,1,17):
        values=palette_rgba(np.asarray([t]),[0,1],palette)[0,:3]
        stops.append('rgb('+','.join(str(x) for x in values)+') '+str(t*100)+'%')
    return 'linear-gradient(90deg, '+', '.join(stops)+')'
