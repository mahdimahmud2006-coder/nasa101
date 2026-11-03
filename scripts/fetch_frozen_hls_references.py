"""Small frozen-footprint optical/QA windows, selected before reading reference values."""
import sys,json,math
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from rasterio.warp import transform_geom,reproject,Resampling
from shapely.geometry import shape,mapping,box
from PIL import Image
from src.compute.evidence_common import load,save,sha
from src.compute.reference_design import choose_reference,hls_quality,descriptive_overlap

def run():
    freeze=load(ROOT/'reference/freeze_manifest.json');assert all(sha(ROOT/p)==h for p,h in freeze['sha256'].items());assert (ROOT/'reference/FREEZE_COMMIT.json').exists()
    output=ROOT/'data/references/v1/hls-v2';output.mkdir(parents=True,exist_ok=True)
    if (output/'results.json').exists():raise FileExistsError('Reference result snapshot exists')
    tokens={};features=load(ROOT/'reference/frozen_footprints.geojson')['features'];allresults=[];requests=[]
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        m=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json');catalog=load(ROOT/f'data/references/v1/catalogs/{case}_hls.response.json')['features'];footprints=[f for f in features if f['properties']['case_id']==case]
        for footprint in footprints:
            bbox=shape(footprint['geometry']).bounds
            candidates=[{'id':f['id'],'timestamp':f['properties']['datetime'],'cloud_cover':f['properties'].get('eo:cloud_cover',100),'feature':f} for f in catalog if shape(f['geometry']).covers(shape(footprint['geometry']))]
            for i,obs in enumerate(m['observations']):
                chosen=choose_reference(candidates,obs['timestamp'],5*86400);row={'case_id':case,'footprint_id':footprint['properties']['id'],'footprint_role':footprint['properties']['role'],'observation_id':obs['observation_id'],'radar_timestamp':obs['timestamp'],'freeze_commit':load(ROOT/'reference/FREEZE_COMMIT.json')['commit'],'reference_status':'none'}
                if not chosen:row.update(status='unavailable',reason='no fully covering HLS item within frozen 5-day tolerance');allresults.append(row);continue
                item=chosen['feature'];prefix=footprint['properties']['id']+'_'+obs['observation_id'];arrays={};profile=None;sourceurls={}
                try:
                    for band in ['B04','B03','B02','Fmask']:
                        url=item['assets'][band]['href'];sourceurls[band]=url
                        from urllib.parse import urlsplit
                        parsed=urlsplit(url)
                        if not parsed.hostname.endswith('.blob.core.windows.net'):raise ValueError('Unapproved HLS host')
                        account=parsed.hostname.split('.')[0];container=parsed.path.strip('/').split('/')[0];key=(account,container)
                        if key not in tokens:tokens[key]=json.load(urlopen('https://planetarycomputer.microsoft.com/api/sas/v1/token/'+account+'/'+container,timeout=30))['token']
                        token=tokens[key]
                        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
                            with rasterio.open(url+'?'+token) as ds:
                                geom=transform_geom('EPSG:4326',ds.crs,footprint['geometry']);bounds=shape(geom).bounds;window=from_bounds(*bounds,ds.transform).round_offsets().round_lengths()
                                if window.width*window.height>2500:raise ValueError('Reference chip exceeds small-window budget')
                                data=ds.read(1,window=window);p=ds.profile.copy();p.update(driver='GTiff',width=data.shape[1],height=data.shape[0],transform=ds.window_transform(window),compress='deflate');path=output/f'{prefix}_{band}.tif'
                                with rasterio.open(path,'w',**p) as out:out.write(data,1)
                                arrays[band]=data;profile=p;requests.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'size_bytes':path.stat().st_size,'url':url,'query':{'method':'HTTP range/native window','bounds_wgs84':bbox,'band':band},'retrieved_at':datetime.now(timezone.utc).isoformat(),'provider':'Microsoft Planetary Computer (USA)','upstream':'NASA HLS; NASA/USGS Landsat or ESA Sentinel-2','license':'NASA/LP DAAC Earth science data policy, https://lpdaac.usgs.gov/data/data-citation-and-policies/','catalog_license_field':'proprietary (non-SPDX policy link retained; not asserted CC0)'})
                    roi=rasterize([(transform_geom('EPSG:4326',profile['crs'],footprint['geometry']),1)],out_shape=arrays['Fmask'].shape,transform=profile['transform'],fill=0,dtype='uint8').astype(bool)
                    clear,water=hls_quality(arrays['Fmask']);valid=clear&roi
                    for b in ['B04','B03','B02']:valid&=(arrays[b]!=-9999)
                    # Reference data do not alter the frozen radar threshold or footprint.
                    projected={}
                    for pol in ['hh','hv']:
                        out=np.full(valid.shape,np.nan,dtype='float32')
                        with rasterio.open(ROOT/f'web/public/cases/{case}/investigation'/obs['rasters'][pol]) as ds:reproject(rasterio.band(ds,1),out,src_transform=ds.transform,src_crs=ds.crs,src_nodata=np.nan,dst_transform=profile['transform'],dst_crs=profile['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
                        projected[pol]=out
                    valid&=np.isfinite(projected['hh'])&np.isfinite(projected['hv']);dark=(projected['hh']<=-17)&(projected['hv']<=-24);overlap=descriptive_overlap(dark,water,valid,abs(profile['transform'].a*profile['transform'].e)/1e6)
                    rgb=np.stack([np.rint(np.clip(arrays[b].astype('float32')*.0001/0.3,0,1)*255).astype('uint8') for b in ['B04','B03','B02']],axis=-1);rgb[~valid]=0;rgba=np.dstack([rgb,valid.astype('uint8')*255]);thumb=output/f'{prefix}.png';Image.fromarray(rgba).save(thumb)
                    row.update(reference_status='date-matched, descriptive',status=overlap['status'],reference_id=chosen['id'],reference_timestamp=chosen['timestamp'],delta_seconds=abs((datetime.fromisoformat(chosen['timestamp'].replace('Z','+00:00'))-datetime.fromisoformat(obs['timestamp'].replace('Z','+00:00'))).total_seconds()),cloud_metadata_percent=chosen['cloud_cover'],clear_assessable_pixels=int(valid.sum()),reference_pixels=int(roi.sum()),overlap=overlap,thumbnail=str(thumb.relative_to(ROOT)),sources=sourceurls,reference_definition='HLS Fmask water bit on clear optical pixels; independent optical algorithmic context, NOT OPERA DSWx or validated ground truth.',sensor_difference='HLS optical vs NISAR L-band; cloudy/snow/shadow/adjacent-cloud/cirrus cells excluded. Coverage gaps retained.')
                except Exception as e:row.update(status='unavailable',reason='selected reference native subset failed',error=str(e),reference_id=chosen['id'])
                allresults.append(row);print(case,obs['observation_id'],footprint['properties']['role'],row['status'],row.get('clear_assessable_pixels'),flush=True)
    save(output/'sources.json',{'items':requests,'full_tiles_downloaded':0});save(output/'results.json',{'schema_version':1,'design_sha256':sha(ROOT/'reference/design.json'),'freeze_commit':load(ROOT/'reference/FREEZE_COMMIT.json')['commit'],'results':allresults,'metrics_prohibited':load(ROOT/'reference/design.json')['metrics_prohibited']})
if __name__=='__main__':run()
