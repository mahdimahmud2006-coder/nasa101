"""Product-aware, date-strict screening. Catalog candidates are not accepted data."""
import re
from src.compute.reference_design import utc

def screen_candidate(properties,series,product):
    p=properties;gid=p['sceneName'];reasons=[]
    observed={utc(o['timestamp']) for o in series['observations']}
    stamps=re.findall(r'\d{8}T\d{6}',gid)
    from datetime import datetime,timezone
    starts=[datetime.strptime(t,'%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc) for t in stamps[::2]]
    expected=2 if product=='GUNW' else 1
    if len(starts)!=expected or not all(t in observed for t in starts):reasons.append('one or more acquisition endpoints are not in the loaded series')
    if p.get('pathNumber')!=series['track'] or p.get('frameNumber')!=series['frame']:reasons.append('track/frame differs')
    if p.get('flightDirection')!='ASCENDING':reasons.append('flight direction differs')
    if p.get('crid')!=series['release']:reasons.append('release differs')
    if p.get('productionConfiguration')!='PR':reasons.append('production configuration differs')
    if p.get('collectionName')!=f'NISAR_L2_{product}_PROVISIONAL_V1':reasons.append('collection differs')
    if product=='GSLC':
        if '4005_DHDH_A' not in gid or p.get('rangeBandwidth')!=['40+5']:reasons.append('catalog source mode/bandwidth differs')
    elif p.get('rangeBandwidth')!=['40'] or p.get('mainBandPolarization')!=['HH']:
        reasons.append('derived frequency-A HH bandwidth/polarization differs or unverified')
    files=p.get('bytes') or {};size=files.get(gid+'.h5',{}).get('bytes')
    return {'granule_id':gid,'product':product,'acquisition_starts':[t.isoformat().replace('+00:00','Z') for t in starts],
            'catalog_eligible':not reasons,'rejection_reasons':reasons,'size_bytes':size,'size_gib':size/2**30 if size else None,
            'url':p.get('url'),'source_acquisition_compatibility':'unverified until source identifiers/mode/bandwidth/release are checked in the product header',
            'output_mode_note':'GUNW is an HH frequency-A derived product. Its 4000_SH label is not by itself evidence of incompatible dual-pol source acquisitions.' if product=='GUNW' else 'GSLC catalog mode matches only provisionally; header inspection remains required.',
            'subset_feasibility':'not verified','accepted':False}

def gate_verdict(records,probe):
    return {'schema_version':2,'gate_open':False,'claim_status':'planned','coherence':None,'los_displacement_cm':None,
            'status':'PENDING_AUTHENTICATED_HEADER_AND_SUBSET_VERIFICATION',
            'reason':'Catalog candidates exist, but no source-compatible science subset has been accepted. This is not a claim of product absence.',
            'checks_remaining':['Earthdata access and ASF data-access agreement','Header verification of source acquisitions, release, mode and bandwidth','Crop-sized coherence/quality subset with measured output size','Numerical coherence/mask validation; reference point and corrections before any LOS displacement'],
            'access_probe':probe,'records':records,'large_downloads':0,
            'official_sources':['https://nisar-docs.asf.alaska.edu/gunw/','https://nisar-docs.asf.alaska.edu/access-overview/','https://nisar-docs.asf.alaska.edu/harmony/','https://nisar-docs.asf.alaska.edu/vertex/']}
