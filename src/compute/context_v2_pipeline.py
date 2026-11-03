"""Add independent case terrain, exact rain request columns and frozen H1 diagnostics."""
import math,shutil,tempfile
from pathlib import Path
import numpy as np,h5py,rasterio
from affine import Affine
from scipy.interpolate import RegularGridInterpolator
from rasterio.warp import Resampling,reproject
from pyproj import Proj,Transformer
import pyarrow as pa,pyarrow.parquet as pq
from src.compute.evidence_common import ROOT,load,save,sha
from src.compute.context_v2 import rain_window,geometry_candidates,stable_targets
from src.compute.environment import terrain_derivatives,flow_metrics
from src.compute.timeseries_pipeline import cog
from src.export.dualpol_render import load_palettes,palette_rgba,preview

def field(array,affine,crs,shape,target,method=Resampling.bilinear):
    out=np.full(shape,np.nan,dtype='float32');reproject(array,out,src_transform=affine,src_crs=crs,src_nodata=np.nan,dst_transform=target,dst_crs=crs,dst_nodata=np.nan,resampling=method);return out

def run():
    cases=load(ROOT/'config.dualpol.json')['source_cases'];version='context-v2';sources=load(ROOT/'data/context/context-v2/terrain/sources.json');rain=load(ROOT/'data/context/context-v2/rain_availability.json');palettes=load_palettes(ROOT/'data/palettes/v1');parent=ROOT/'web/public/cases'
    if any((parent/c/version).exists() for c in cases):raise FileExistsError('Context version already exists')
    summaries={}
    with tempfile.TemporaryDirectory(prefix='.context-v2-',dir=parent) as temporary:
        stage=Path(temporary)
        for case in cases:
            m=load(parent/case/'investigation/manifest.json');g=m['grid'];native=Affine(*g['affine']);resolution=30;shape=tuple(math.ceil(v/3) for v in g['shape']);transform=native*Affine.scale(3);halo=70;bigshape=tuple(v+2*halo for v in shape);bigtransform=transform*Affine.translation(-halo,-halo);dem=np.full(bigshape,np.nan,dtype='float32');used=[]
            for item in sources['items']:
                if item['case_id']!=case:continue
                path=ROOT/item['file'];assert sha(path)==item['sha256'];used.append(item)
                with rasterio.open(path) as ds:
                    out=np.full(bigshape,np.nan,dtype='float32');reproject(ds.read(1,masked=True).astype('float32').filled(np.nan),out,src_transform=ds.transform,src_crs=ds.crs,src_nodata=np.nan,dst_transform=bigtransform,dst_crs=g['crs'],dst_nodata=np.nan,resampling=Resampling.bilinear);dem[np.isfinite(out)]=out[np.isfinite(out)]
            # A tiny source-edge margin can remain nodata; no synthetic elevation fill.
            terrain=terrain_derivatives(dem,resolution,510);flow,flowmeta=flow_metrics(dem,resolution,terrain['slope']);crop=np.s_[halo:halo+shape[0],halo:halo+shape[1]];arrays={k:v[crop].copy() for k,v in {**terrain,**flow}.items()}
            directory=stage/case;directory.mkdir();layers={}
            limits={'slope':[0,60],'aspect':[0,360],'relative_elevation':[-30,30]}
            for name in ['dem','slope','aspect','relative_elevation','flow_accumulation','twi','drainage_distance']:
                values=arrays[name];finite=values[np.isfinite(values)];scale=limits.get(name,[float(np.percentile(finite,2)),float(np.percentile(finite,98))])
                if scale[1]<=scale[0]:scale[1]=scale[0]+1
                cog(directory/(name+'.tif'),values,transform,g['crs'],name+'; NASADEM 30 m context, EGM96 geoid')
                preview(directory/(name+'.png'),palette_rgba(values,scale,palettes['cividis']))
                layers[name]={'raster':name+'.tif','preview':name+'.png','limits':scale,'valid_fraction':float(np.isfinite(values).mean())}
            original=parent/case/'investigation';first=m['observations'][0];path=ROOT/('aug19.h5' if case.startswith('nepal') else 'database/bangladesh-shared/'+first['source_file'])
            yy,xx=np.meshgrid(np.arange(shape[0]),np.arange(shape[1]),indexing='ij');x=transform.c+(xx+.5)*30;y=transform.f-(yy+.5)*30
            with h5py.File(path) as h5:
                rg=h5['science/LSAR/GCOV/metadata/radarGrid'];xs=rg['xCoordinates'][()];ys=rg['yCoordinates'][()];height_index=int(np.argmin(np.abs(rg['heightAboveEllipsoid'][()])));fields={}
                for name in ['incidenceAngle','losUnitVectorX','losUnitVectorY']:
                    data=rg[name][height_index,:,:];fields[name]=RegularGridInterpolator((ys[::-1],xs),data[::-1,:],bounds_error=False,fill_value=np.nan)(np.stack([y,x],axis=-1))
            lon,lat=Transformer.from_crs(g['crs'],'EPSG:4326',always_xy=True).transform(x,y);convergence=Proj(g['crs']).get_factors(lon,lat).meridian_convergence
            bits=geometry_candidates(arrays['dem'],30,fields['incidenceAngle'],fields['losUnitVectorX'],fields['losUnitVectorY'],convergence)
            cog(directory/'geometry_candidates.tif',bits,transform,g['crs'],'Conservative screening: 1 steep, 2 range-slope layover-like, 4 backfacing-shadow-like; 255 unavailable',255,True)
            warning=np.where(bits!=255,(bits>0).astype('float32'),np.nan);preview(directory/'geometry_candidates.png',palette_rgba(warning,[0,1],palettes['cividis']));layers['geometry_candidates']={'raster':'geometry_candidates.tif','preview':'geometry_candidates.png','limits':[0,1]}
            with rasterio.open(original/first['rasters']['hh']) as ds:hh0=ds.read(1)
            with rasterio.open(original/first['rasters']['hv']) as ds:hv0=ds.read(1)
            z=field(arrays['dem'],transform,g['crs'],tuple(g['shape']),native);slope=field(arrays['slope'],transform,g['crs'],tuple(g['shape']),native)
            selected,selection=stable_targets(hh0,hv0,z,slope)
            cog(directory/'stable_targets.tif',selected.astype('uint8'),native,g['crs'],'Putative stable controls selected from first date and terrain only',255,True)
            selection.update(mask_sha256=sha(directory/'stable_targets.tif'),first_source_granule_id=first['source_granule_id']);save(directory/'stable_target_selection.json',selection)
            # Selection is now written/frozen before later-date control statistics.
            stack={p:[] for p in ['hh','hv']}
            for obs in m['observations']:
                for pol in stack:
                    with rasterio.open(original/obs['rasters'][pol]) as ds:stack[pol].append(ds.read(1))
            stack={k:np.stack(v) for k,v in stack.items()};common=selected&np.isfinite(stack['hh']).all(0)&np.isfinite(stack['hv']).all(0);controls=[];rainrows=[];hist=[]
            for i,obs in enumerate(m['observations']):
                control={'timestamp':obs['timestamp'],'observation_id':obs['observation_id'],'common_control_pixels':int(common.sum())}
                for pol in stack:
                    values=stack[pol][i][common];control[pol+'_median_db']=float(np.median(values)) if len(values) else None
                    bins=np.arange(-60,31,1);vals=stack[pol][i][np.isfinite(stack[pol][i])];hist.append({'timestamp':obs['timestamp'],'channel':pol,'bins_db':bins.tolist(),'counts':np.histogram(vals,bins)[0].tolist(),'valid_pixels':len(vals),'below_above':[int((vals<bins[0]).sum()),int((vals>bins[-1]).sum())],'scope':'all canonical crop pixels, filtered log-power; not a full raw scene'})
                controls.append(control)
                windows={f'{h}h':rain_window(obs['timestamp'],hours=h) for h in [24,72,168]}
                windows['since_previous']=rain_window(obs['timestamp'],start=m['observations'][i-1]['timestamp']) if i else None
                row={'observation_id':obs['observation_id'],'timestamp':obs['timestamp'],'windows':windows,'status':'unavailable','reason':rain['cases'][case]['reason'],'native_resolution_degrees':.1,'imerg_24h_mm':None,'imerg_72h_mm':None,'imerg_168h_mm':None,'imerg_since_previous_mm':None};rainrows.append(row)
            for row in controls:
                for pol in ['hh','hv']:row[pol+'_baseline_shift_db']=row[pol+'_median_db']-controls[0][pol+'_median_db'] if row[pol+'_median_db'] is not None and controls[0][pol+'_median_db'] is not None else None
            save(directory/'h1_controls.json',{'selection':selection,'controls':controls,'interpretation':'Putative controls can still change physically. A common scene offset is a measurement/processing hypothesis, not established calibration error.'});save(directory/'crop_histograms.json',hist)
            pq.write_table(pa.Table.from_pylist([{k:v for k,v in r.items() if k!='windows'} for r in rainrows]),directory/'context.parquet');save(directory/'rain.json',{'dataset':rain['dataset'],'observations':rainrows,'availability':rain['cases'][case]})
            result={'schema_version':1,'case_id':case,'status':'implemented','grid':{'shape':list(shape),'affine':list(transform)[:6],'crs':g['crs'],'resolution_m':30},'layers':layers,'terrain_summary':{'median_slope_degrees':float(np.nanmedian(arrays['slope'])),'fraction_slope_ge_10':float(np.nanmean(arrays['slope']>=10)),'fraction_geometry_candidates':float(np.mean(bits[bits!=255]>0))},'radiometric_controls':controls,'stable_target_selection':selection,'rain':rainrows,'terrain_sources':used,'hydrology':flowmeta,'incidence_source':{'file':str(path.relative_to(ROOT)),'dataset':'/science/LSAR/GCOV/metadata/radarGrid/incidenceAngle','height_plane_ellipsoid_m':0,'native_metadata_spacing_m':500,'los_components':'ENU, target to sensor; rotated to UTM using local convergence'},'limitations':['Separate crop-specific NASADEM context; not Nepal data reused geographically for Bangladesh.','30 m context grid can extend up to 20 m beyond original crop due to ceil sizing; terrain is not radar detail.','Steep/layover-shadow screening uses local range slope and incidence at 0 m ellipsoid; not full ray tracing, visibility correction or a validated mask.','NASADEM EGM96 height and incidence ellipsoid reference differ; the fixed 0 m metadata plane is an approximation.','Hydrology is buffer-limited model routing, not observed drainage or inundation depth.','Scientific IMERG is unavailable from the recorded queries; no previous GIS zeros or POWER values substituted.']}
            save(directory/'manifest.json',result);summaries[case]=result['terrain_summary'];print(case,summaries[case],flush=True)
        for case in cases:shutil.move(str(stage/case),str(parent/case/version))
    save(ROOT/'data/context/context-v2/build_summary.json',{'cases':summaries,'version':version})
if __name__=='__main__':run()
