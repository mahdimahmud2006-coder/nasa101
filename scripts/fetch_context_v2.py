#!/usr/bin/env python3
"""Fetch small native NASADEM windows from the approved Microsoft US distributor."""
import json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from src.compute.evidence_common import load,save,sha

def run():
    dest=ROOT/'data/context/context-v2/terrain';dest.mkdir(parents=True,exist_ok=True)
    manifest=dest/'sources.json'
    if manifest.exists():raise FileExistsError('Terrain snapshot already exists')
    token=json.load(urlopen('https://planetarycomputer.microsoft.com/api/sas/v1/token/nasademeuwest/nasadem-cog',timeout=30))['token']
    items=[]
    for case in ['nepal_surface','nepal_impact_corridor','jamuna_river','tanguar_wetland']:
        m=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json');g=m['grid'];a=g['affine'];h,w=g['shape'];buffer=2100
        bounds=transform_bounds(g['crs'],'EPSG:4326',a[2]-buffer,a[5]+a[4]*h-buffer,a[2]+a[0]*w+buffer,a[5]+buffer,densify_pts=21)
        for lat in range(math.floor(bounds[1]),math.floor(bounds[3])+1):
            for lon in range(math.floor(bounds[0]),math.floor(bounds[2])+1):
                tile=f'NASADEM_HGT_n{lat:02d}e{lon:03d}';url=f'https://nasademeuwest.blob.core.windows.net/nasadem-cog/v001/{tile}.tif'
                clip=[max(bounds[0],lon),max(bounds[1],lat),min(bounds[2],lon+1),min(bounds[3],lat+1)]
                if clip[0]>=clip[2] or clip[1]>=clip[3]:continue
                local=ROOT/f'data/context/environment/{tile}.tif';path=dest/f'{case}_{tile}.tif'
                # Signed URL is used only in memory. Tokens never enter saved provenance.
                with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
                    with rasterio.open(local if local.exists() else url+'?'+token) as ds:
                        window=from_bounds(*clip,ds.transform).round_offsets().round_lengths()
                        arr=ds.read(1,window=window);profile=ds.profile.copy();profile.update(driver='GTiff',width=arr.shape[1],height=arr.shape[0],transform=ds.window_transform(window),compress='deflate')
                        with rasterio.open(path,'w',**profile) as out:out.write(arr,1)
                item={'case_id':case,'file':str(path.relative_to(ROOT)),'sha256':sha(path),'size_bytes':path.stat().st_size,'provider':'Microsoft Planetary Computer (USA)','upstream':'NASA/JPL/USGS NASADEM (USA)','dataset':'NASADEM HGT v001','license':'NASA Earth science open data; source collection license applies','url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'query':{'method':'HTTP range/native raster window','bounds_wgs84':clip,'tile':tile},'source_reused_local':local.exists(),'vertical_reference':'EGM96 geoid, meters','native_resolution':'1 arc-second'}
                items.append(item);print(case,tile,path.stat().st_size,flush=True)
    save(manifest,{'schema_version':1,'items':items,'raw_full_tiles_downloaded':0,'note':'Native source windows only; no signed URLs or credentials saved.'})
if __name__=='__main__':run()
