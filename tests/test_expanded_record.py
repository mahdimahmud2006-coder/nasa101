from pathlib import Path
import numpy as np
import pytest
import rasterio
from affine import Affine
from src.compute.expanded_record import gunw_validity, profile, probe, REFERENCE, CASES, gunw_header
from src.compute.evidence_common import ROOT, load


def test_source_subswaths_water_anomalies_and_invalid_coherence():
    masks=np.array([11,111,10,1,0,11 | (1<<8),11 | (1<<16),11 | (1<<24),2**32-1],dtype='uint32')
    assert gunw_validity(np.full(9,.5),masks).tolist()==[True,True,False,False,False,False,False,True,False]
    assert gunw_validity(np.array([0.,1.,np.nan,-.1,1.1]),np.full(5,11,dtype='uint32')).tolist()==[True,True,False,False,False]


def test_reference_is_august_19_even_with_earlier_dates_and_missing_support():
    obs=[{'timestamp':'2026-07-26T00:00:00Z','observation_id':'early'},
         {'timestamp':REFERENCE,'observation_id':'reference'},{'timestamp':'2026-08-31T00:00:00Z','observation_id':'after'}]
    stacks={'hh':np.array([[[1.,10.]],[[3.,20.]],[[8.,np.nan]]]),'hv':np.array([[[2.,1.]],[[4.,2.]],[[5.,3.]]])}
    p=profile(stacks,np.ones((1,2),bool),obs,1,'fixed',.0001)
    assert p['common_valid_pixels']==1
    assert [r['hh_reference_delta_db'] for r in p['observations']]==[-2.,0.,5.]
    assert p['observations'][0]['hh_successive_delta_db'] is None
    assert p['observations'][2]['cpr_reference_delta_db']==-4.
    empty=profile(stacks,np.zeros((1,2),bool),obs,1,'empty',.0001)
    assert all(r['hh_mean_db'] is None for r in empty['observations'])


@pytest.mark.parametrize('case,row,col',[('../nepal_surface',0,0),('jamuna_river',0,0),('nepal_surface',-1,0),('nepal_surface',2400,0)])
def test_probe_rejects_unknown_cases_and_outside_grid(case,row,col):
    with pytest.raises(ValueError):probe(case,row,col)


def test_supplied_gunw_source_identities_match_accepted_gcove_dates():
    m=load(ROOT/'web/public/cases/nepal_surface/expanded-v1/manifest.json')
    accepted={o['timestamp'] for o in m['observations']}
    for p in (ROOT/'database/extra datasets').glob('*GUNW*.h5'):
        header=gunw_header(p,accepted)
        assert header['identification']['trackNumber']==98
        assert all('_4005_DHDH_A_' in x[0] for x in header['source_slc_granules'])
        with pytest.raises(ValueError):gunw_header(p,set())


def test_expanded_neighborhood_reads_actual_cog_values_and_clips_edges():
    for case in CASES:
        result=probe(case,0,0);p=result['profile'];m=load(ROOT/f'web/public/cases/{case}/expanded-v1/manifest.json')
        assert result['window']==[0,0,6,6] and len(p['observations'])==10
        hh=[];hv=[]
        for obs in m['observations']:
            for pol,values in [('hh',hh),('hv',hv)]:
                with rasterio.open(ROOT/'web/public'/obs['rasters'][pol].lstrip('/')) as ds:
                    values.append(ds.read(1,window=rasterio.windows.Window(0,0,6,6)))
        valid=np.isfinite(hh).all(axis=0)&np.isfinite(hv).all(axis=0)
        assert p['common_valid_pixels']==int(valid.sum())
        if valid.any():assert p['observations'][-1]['hh_mean_db']==pytest.approx(np.asarray(hh)[-1][valid].astype('float64').mean())


def test_api_serves_expanded_point_and_rejects_unsupported_case():
    import io,json
    from types import SimpleNamespace
    from src.api.app import Handler
    class Connection:
        def __init__(self,path):
            self.input=io.BytesIO(f'GET {path} HTTP/1.0\r\nHost: localhost\r\n\r\n'.encode());self.output=bytearray()
        def makefile(self,*a,**k):return self.input
        def sendall(self,b):self.output.extend(b)
    for path,expected in [('/api/cases/nepal_surface/expanded-probe?row=1200&col=1200',200),
                          ('/api/cases/nepal_surface/expanded-probe?row=99999&col=0',422),
                          ('/api/cases/jamuna_river/expanded-probe?row=0&col=0',422)]:
        c=Connection(path);Handler(c,('127.0.0.1',1),SimpleNamespace(server_name='localhost',server_port=8000))
        head,body=bytes(c.output).split(b'\r\n\r\n',1);assert int(head.split()[1])==expected
        if expected==200:assert len(json.loads(body)['profile']['observations'])==10
