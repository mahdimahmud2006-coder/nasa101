import json
import pytest
from src.compute.active_records import case_directory,registry_path

def test_explicit_record_versions_and_historical_default(tmp_path):
    assert case_directory('jamuna_river',tmp_path)==tmp_path/'web/public/cases/jamuna_river'
    (tmp_path/'config.records.json').write_text(json.dumps({'investigation_registry':'investigations-bangladesh-v2.json','cases':{'jamuna_river':'bangladesh-v2'}}))
    assert case_directory('jamuna_river',tmp_path)==tmp_path/'web/public/cases/jamuna_river/bangladesh-v2'
    assert case_directory('nepal_surface',tmp_path)==tmp_path/'web/public/cases/nepal_surface'
    assert registry_path(tmp_path).name=='investigations-bangladesh-v2.json'

@pytest.mark.parametrize('bad',['../escape','/etc/passwd','v2/extra',2])
def test_invalid_record_version_rejected(tmp_path,bad):
    (tmp_path/'config.records.json').write_text(json.dumps({'cases':{'jamuna_river':bad}}))
    with pytest.raises(ValueError):case_directory('jamuna_river',tmp_path)

def test_context_cannot_silently_attach_by_position_after_inserting_dates(tmp_path):
    import numpy as np,rasterio
    from affine import Affine
    from rasterio.windows import Window
    from src.compute.investigation_dna import evaluate_window
    base=tmp_path/'web/public/cases/sample';(base/'investigation').mkdir(parents=True);(base/'context-v2').mkdir()
    obs=[]
    for i in range(2):
        o={'timestamp':f'2026-06-{18+i:02d}T00:00:00Z','observation_id':str(i),'rasters':{}}
        for p in ['hh','hv']:
            name=f'{p}_{i}.tif';o['rasters'][p]=name
            with rasterio.open(base/'investigation'/name,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:32646',transform=Affine(10,0,500000,0,-10,3000000)) as ds:ds.write(np.full((2,2),-i,dtype='float32'),1)
        obs.append(o)
    (base/'investigation/manifest.json').write_text(json.dumps({'observations':obs,'grid':{'pixel_area_km2':.0001}}))
    (base/'context-v2/manifest.json').write_text(json.dumps({'rain':[{'timestamp':'2026-07-24T00:00:00Z'}],'radiometric_controls':[]}))
    with pytest.raises(ValueError,match='binding is stale'):evaluate_window('sample',np.ones((2,2),bool),Window(0,0,2,2),'test','synthetic',tmp_path)
