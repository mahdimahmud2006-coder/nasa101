"""Add fixed-footprint DNA and competing explanations for all four existing cases."""
from pathlib import Path
import shutil,tempfile
import numpy as np,rasterio
from rasterio.windows import Window
from rasterio.features import rasterize
from affine import Affine
from scipy.ndimage import label
import pyarrow as pa,pyarrow.parquet as pq
from src.compute.evidence_common import ROOT,load,save,sha
from src.compute.investigation_dna import evaluate_window
from src.compute.timeseries_pipeline import cog

def run():
    cases=load(ROOT/'config.dualpol.json')['source_cases'];parent=ROOT/'web/public/cases';version='evidence-v2'
    if any((parent/c/version).exists() for c in cases):raise FileExistsError('DNA version already exists')
    configs={c['case_id']:c for c in load(ROOT/'config.investigations.json')['cases']}
    with tempfile.TemporaryDirectory(prefix='.evidence-v2-',dir=parent) as temporary:
        for case in cases:
            base=parent/case/'investigation';m=load(base/'manifest.json');shape=tuple(m['grid']['shape']);a=Affine(*m['grid']['affine']);masks=[]
            if case=='nepal_surface':
                with rasterio.open(ROOT/configs[case]['legacy_zone_raster']) as ds:mask=ds.read(1)>0
                masks.append((m['profiles'][0]['label'],mask,m['profiles'][0]['selection']))
            elif m.get('reference'):
                masks.append((m['profiles'][0]['label'],rasterize([(m['reference']['geometry_pixel'],1)],out_shape=shape,transform=Affine.identity(),dtype='uint8').astype(bool),m['profiles'][0]['selection']))
            else:
                masks.append((m['profiles'][0]['label'],np.ones(shape,bool),m['profiles'][0]['selection']))
                first,last=m['observations'][0],m['observations'][-1];channels={}
                for name,obs in [('first',first),('last',last)]:
                    for pol in ['hh','hv']:
                        with rasterio.open(base/obs['rasters'][pol]) as ds:channels[name+'_'+pol]=ds.read(1)
                valid=np.logical_and.reduce([np.isfinite(v) for v in channels.values()]);dark=lambda t:(channels[t+'_hh']<=-17)&(channels[t+'_hv']<=-24)
                labels,count=label(valid&(dark('first')!=dark('last')),structure=np.ones((3,3)));sizes=np.bincount(labels.ravel());order=sorted(range(1,count+1),key=lambda k:(-sizes[k],k))[:3]
                for i,key in enumerate(order):
                    if sizes[key]>=25:masks.append((f'Exploratory transition footprint {i+1}',labels==key,'Retrospectively selected among largest first/last dark-signature transition components; uncalibrated thresholds, selection-biased, not independent reference.'))
            dest=Path(temporary)/case;dest.mkdir();records=[]
            for i,(title,mask,selection) in enumerate(masks):
                rr,cc=np.where(mask);top,left=int(rr.min()),int(cc.min());bottom,right=int(rr.max()+1),int(cc.max()+1);window=Window(left,top,right-left,bottom-top);cropped=mask[top:bottom,left:right]
                result=evaluate_window(case,cropped,window,title,selection);result['profile']['saved_evidence_index']=i
                path=dest/f'footprint_{i}.tif';cog(path,cropped.astype('uint8'),a*Affine.translation(left,top),m['grid']['crs'],'Fixed native pixel-center footprint; retrospective selection as documented',255,True);result['footprint_raster']={'file':path.name,'sha256':sha(path)};records.append(result)
            save(dest/'manifest.json',{'schema_version':2,'case_id':case,'status':'implemented','profiles':records,'rules_version':load(ROOT/'rules/explanations.yaml')['model_version'],'rules_sha256':sha(ROOT/'rules/explanations.yaml'),'source_manifest_sha256':sha(base/'manifest.json'),'limitations':['No validated historical event matches or empirical probabilities.','Coherence remains null until a compatible interferometric result is accepted.']})
            pq.write_table(pa.Table.from_pylist([{'footprint_index':i,'label':r['profile']['label'],'k':r['dna']['persistence']['k'],'n':r['dna']['persistence']['n'],'persistence_fraction':r['dna']['persistence']['fraction'],'recovery_fraction':r['dna']['recovery_fraction'],'recovery_right_censored':r['dna']['recovery_right_censored'],'coherence':None,**v} for i,r in enumerate(records) for v in r['profile']['observations']]),dest/'change_dna_v2.parquet')
            print(case,len(records),'DNA footprints',flush=True)
        for case in cases:shutil.move(str(Path(temporary)/case),str(parent/case/version))
if __name__=='__main__':run()
