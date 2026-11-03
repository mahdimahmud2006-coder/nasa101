"""Reconcile frozen inputs and every published HLS reference comparison."""
import json
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom,reproject,Resampling
from shapely.geometry import shape
from src.compute.evidence_common import ROOT,load,sha
from src.compute.reference_design import utc

def validate():
    freeze=load(ROOT/'reference/freeze_manifest.json'); commit=load(ROOT/'reference/FREEZE_COMMIT.json')
    assert all(sha(ROOT/p)==h for p,h in freeze['sha256'].items())
    source=ROOT/'data/references/v1/hls-v2'; original=load(source/'results.json')
    sources=load(source/'sources.json')['items']
    assert all(sha(ROOT/s['path'])==s['sha256'] and utc(s['retrieved_at'])>utc(commit['recorded_at']) for s in sources)
    features={f['properties']['id']:f for f in load(ROOT/'reference/frozen_footprints.geojson')['features']}
    assert len(features)==12
    counts={'assessable_comparisons':0,'unavailable_comparisons':0}
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        public=ROOT/f'web/public/cases/{case}/references-v1'; bundle=load(public/'manifest.json')
        assert bundle['design_sha256']==sha(ROOT/'reference/design.json')
        assert bundle['source_results_sha256']==sha(source/'results.json')
        assert bundle['source_manifest_sha256']==sha(source/'sources.json')
        assert bundle['rules_sha256']==sha(ROOT/'rules/explanations.yaml')
        assert len(bundle['profiles'])==3
        m=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json')
        assert bundle['radar_manifest_sha256']==sha(ROOT/f'web/public/cases/{case}/investigation/manifest.json')
        observations={o['observation_id']:o for o in m['observations']}
        catalog=load(ROOT/f'data/references/v1/catalogs/{case}_hls.response.json')['features']
        assert len(bundle['results'])==len(observations)*3
        for row in bundle['results']:
            footprint=features[row['footprint_id']];obs=observations[row['observation_id']]
            eligible=[f for f in catalog if shape(f['geometry']).covers(shape(footprint['geometry'])) and abs((utc(f['properties']['datetime'])-utc(obs['timestamp'])).total_seconds())<=5*86400]
            chosen=min(eligible,key=lambda f:(abs((utc(f['properties']['datetime'])-utc(obs['timestamp'])).total_seconds()),f['properties'].get('eo:cloud_cover',100),f['id'])) if eligible else None
            assert row.get('reference_id')==(chosen['id'] if chosen else None)
            if 'overlap' not in row:
                assert row['reference_status']=='none';counts['unavailable_comparisons']+=1;continue
            prefix=row['footprint_id']+'_'+row['observation_id'];arrays={}
            for band in ['Fmask','B04','B03','B02']:
                with rasterio.open(source/f'{prefix}_{band}.tif') as ds:
                    arrays[band]=ds.read(1);transform=ds.transform;crs=ds.crs
            flags=arrays['Fmask'];roi=rasterize([(transform_geom('EPSG:4326',crs,footprint['geometry']),1)],out_shape=flags.shape,transform=transform,fill=0,dtype='uint8').astype(bool)
            valid=roi&(flags!=255)&((flags.astype('uint16')%32)==0)
            for band in ['B04','B03','B02']:valid&=(arrays[band]!=-9999)
            channels={}
            for pol in ['hh','hv']:
                values=np.full(flags.shape,np.nan,dtype='float32')
                with rasterio.open(ROOT/f'web/public/cases/{case}/investigation'/obs['rasters'][pol]) as ds:
                    reproject(rasterio.band(ds,1),values,src_transform=ds.transform,src_crs=ds.crs,src_nodata=np.nan,dst_transform=transform,dst_crs=crs,dst_nodata=np.nan,resampling=Resampling.nearest)
                channels[pol]=values;valid&=np.isfinite(values)
            assert int(valid.sum())==row['clear_assessable_pixels']
            area=abs(transform.a*transform.e)/1e6;overlap=row['overlap']
            assert np.isclose(overlap['assessable_area_km2'],valid.sum()*area)
            if valid.any():
                water=(flags//32)%2==1;dark=(channels['hh']<=-17)&(channels['hv']<=-24)
                for key,mask in [('reference_water_area_km2',water),('intersection_area_km2',water&dark),('radar_dark_area_km2',dark)]:
                    assert np.isclose(overlap[key],np.count_nonzero(mask&valid)*area)
                assert row['reference_status']=='date-matched, descriptive';counts['assessable_comparisons']+=1
            else:
                assert row['reference_status']=='none' and overlap['reference_water_area_km2'] is None;counts['unavailable_comparisons']+=1
            assert sha(public/row['thumbnail'].split('/')[-1])==row['thumbnail_sha256']
            assert not {'precision','recall','IoU','accuracy'}&overlap.keys()
    assert sum(counts.values())==len(original['results'])
    return {'status':'FROZEN_DESCRIPTIVE_REFERENCES_PASS',**counts,'full_tiles_downloaded':0}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
