"""Stream every pixel of the six shared Bangladesh source scenes for H1 histograms."""
import sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import h5py,numpy as np
from src.compute.evidence_common import load,save

def run():
    target=ROOT/'data/context/context-v2/h1_source_histograms.json'
    if target.exists():raise FileExistsError(target)
    bins=np.arange(-60,31,1,dtype='float64');records=[]
    for o in load(ROOT/'web/public/cases/jamuna_river/investigation/manifest.json')['observations']:
        path=ROOT/'database/bangladesh-shared'/o['source_file'];before=path.stat();result={p:np.zeros(len(bins)-1,dtype='int64') for p in ['hh','hv']};counts={p:0 for p in result};tails={p:[0,0] for p in result}
        with h5py.File(path) as f:
            g=f['science/LSAR/GCOV/grids/frequencyA'];height,width=g['HHHH'].shape
            for row in range(0,height,512):
                sl=np.s_[row:min(height,row+512),:];mask=g['mask'][sl];looks=g['numberOfLooks'][sl];quality=(mask>0)&(mask<255)&np.isfinite(looks)&(looks>0)
                for pol,term in [('hh','HHHH'),('hv','HVHV')]:
                    a=g[term][sl];good=quality&np.isfinite(a)&(a>0);values=10*np.log10(a[good]);counts[pol]+=len(values);result[pol]+=np.histogram(values,bins)[0];tails[pol][0]+=int((values<bins[0]).sum());tails[pol][1]+=int((values>bins[-1]).sum())
        after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        records.append({'source_granule_id':o['source_granule_id'],'timestamp':o['timestamp'],'shape':[height,width],'pixels_total':height*width,'valid_pixels':counts,'histogram_counts':{k:v.tolist() for k,v in result.items()},'tails_below_above':tails,'source_size_bytes':before.st_size,'source_stat_stable':True})
        print('H1 full source histogram',o['timestamp'],flush=True)
    save(target,{'schema_version':1,'bins_db':bins.tolist(),'records':records,'definition':'Every native pixel of the full six Bangladesh GCOV source scenes, raw log-power; source mask >0 and <255, positive finite power and positive finite looks. Distinct from crop-filtered histograms.','scope':'Radiometric diagnostic only; distributions do not identify physical cause.'})
if __name__=='__main__':run()
