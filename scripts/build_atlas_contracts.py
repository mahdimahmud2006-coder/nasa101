"""Build the atlas identity catalog from the accepted scientific manifests."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_contract import binding, digest, grid_identity
from src.compute.atlas_admission import active_manifests, admitted_pairs, require_admitted
from scripts.atlas_context_metadata import context_metadata, radar_metadata, terrain_metadata
from scripts.atlas_pair_metadata import coherence_palette, pair_metadata
from scripts.audit_atlas_validation import audit
from src.compute.atlas_review import HH_DARK_DB, HV_DARK_DB, review_location
from src.compute.atlas_explanations import MIN_NATIVE_RULE_SUPPORT


def acquisition_gaps(path, manifest, observations, case_id):
    if 'instrument_gap' in manifest:
        gap = manifest['instrument_gap']
        return [{'start':gap['start'],'end':gap['end'],'nominalDate':gap['unobservable_nominal_date'],'source':gap['source']}]
    calendar = json.loads((path.parent.parent/'calendar.json').read_text())
    observed = [slot['observed_timestamp'] for slot in calendar['slots'] if slot['status']=='observed']
    if case_id not in calendar['case_ids'] or observed != [o['utc'] for o in observations]:
        raise ValueError('Atlas calendar does not match the accepted observation sequence')
    return [{'start':gap['start'],'end':gap['end'],'nominalDate':slot['date'],'source':gap['source_url']}
            for gap in calendar['instrument_gaps'] for slot in calendar['slots']
            if slot['status']=='instrument_gap' and gap['start']<=slot['nominal_timestamp']<=gap['end']]


def build_catalog(root=ROOT, raster_output=None):
    public = root/'web/public'
    r = json.loads((root/'web/atlas-record.json').read_text())
    paths=active_manifests(root)
    require_admitted(root,paths)
    if r.keys()!=paths.keys():
        raise ValueError('Saved record is not the active case set')
    rule_table = json.loads((root/'rules/explanations.yaml').read_text())
    imerg = json.loads((root/'reports/development/part-03-imerg-catalog.json').read_text())
    hand_audit = json.loads((root/'reports/development/part-09-hand-audit.json').read_text())
    phase = json.loads((root/'reports/development/part-12-los-feasibility.json').read_text())
    validation = json.loads((root/'reports/development/part-13-validation-status.json').read_text())
    if validation != audit(root):
        raise ValueError('Independent validation receipt is stale')
    palette = coherence_palette(root)
    templates = [{k:rule[k] for k in ('id','title','required','limitation')} for rule in rule_table['hypotheses']]
    out = {}
    for case_id,c in r.items():
        path = (public/c['manifest_path']).resolve()
        if not path.is_relative_to((public/'cases').resolve()) or path!=paths[case_id].resolve():
            raise ValueError('Manifest outside accepted case directory')
        m = json.loads(path.read_text())
        m['interferometry'] = admitted_pairs(root,path,m)
        bind = binding(case_id,path)
        if c['manifest_sha256']!=bind['manifestSha256'] or c['grid']!=m['grid']:
            raise ValueError('Atlas record does not match source manifest')
        observations = [{'id':o['observation_id'],'utc':o['timestamp'],'sourceId':o['source_granule_id']} for o in m['observations']]
        if observations!=[{'id':o['observation_id'],'utc':o['timestamp'],'sourceId':o['source_granule_id']} for o in c['observations']]:
            raise ValueError('Atlas observation identities are stale')
        by_time = {o['utc']:o['id'] for o in observations}
        if len(by_time)!=len(observations) or len(set(by_time.values()))!=len(observations) or list(by_time)!=sorted(by_time):
            raise ValueError('Duplicate observation identity')
        sources=[(path,{'profile':p}) for p in m['profiles']]
        if c['country']=='Bangladesh':
            sources=[]
            for product in ('evidence-v2','references-v1'):
                source=path.parent.parent/product/'manifest.json'
                document=json.loads(source.read_text())
                if document.get('radar_manifest_sha256',document.get('source_manifest_sha256'))!=bind['manifestSha256']:
                    raise ValueError('Stale profile source manifest')
                sources.extend((source,p) for p in document['profiles'])
        if len(sources)!=len(c['profiles']):
            raise ValueError('Profile catalog is stale')
        quality, dualpol, masks, reviews, derived, landcover = radar_metadata(public/'cases',path,m,sources,rule_table)
        phase_case = phase['cases'][case_id]
        if phase_case['manifestSha256'] != bind['manifestSha256']:
            raise ValueError('Phase receipt belongs to a different case record')
        pairs, comparisons = pair_metadata(case_id,m,public/'cases',path.parent,by_time,masks,phase_case,palette,raster_output)
        if [(x['startUtc'],x['endUtc'],x['sourceId']) for x in pairs]!=[(x['dates'][0],x['dates'][1],x['source']) for x in c['pairs']]:
            raise ValueError('Atlas pair identity mismatch')
        footprints=[]
        for ordinal,((source,evidence),visible) in enumerate(zip(sources,c['profiles'])):
            profile,mask=evidence['profile'],evidence.get('footprint_raster')
            if profile['label']!=visible['label'] or profile['common_valid_pixels']!=visible['valid_pixels']:
                raise ValueError('Profile source mismatch')
            source_id=hashlib.sha256(source.read_bytes()).hexdigest()
            footprints.append({'id':'saved:'+digest([case_id,bind['gridId'],source_id,ordinal,mask]),
                'ordinal':ordinal,'label':visible['label'],'gridId':bind['gridId'],'maskSource':mask,
                'profileManifestSha256':source_id,'sampleRule':'Frozen native footprint; common-valid pixels across recorded visits',
                'footprintPixels':profile['footprint_pixels'],'dualpol':dualpol[ordinal],
                'opticalFootprintId':evidence.get('reference_footprint_id')})
            if reviews:
                footprints[-1]['review'] = reviews[ordinal]
            location = reviews[ordinal]['location'] if reviews else review_location(
                masks[ordinal], Affine(*m['grid']['affine']), m['grid']['crs'])
            footprints[-1]['fieldLocation'] = [location['longitude'], location['latitude']] if location else None
            if landcover[ordinal]:
                footprints[-1]['historicalLandCover'] = landcover[ordinal]
            explanation_rows=evidence.get('explanations', derived[ordinal])
            if explanation_rows:
                if [(v['observation_id'],v['timestamp']) for v in explanation_rows]!=[(o['id'],o['utc']) for o in observations]:
                    raise ValueError('Hypothesis evidence is bound to different acquisitions')
                if any(v['model_version']!=rule_table['model_version'] for v in explanation_rows):
                    raise ValueError('Hypothesis evidence uses a different rule version')
                keys=('id','status','supporting_signatures','contradicting_signatures','unmet_signatures','missing_inputs')
                footprints[-1]['explanationEvidence']={
                    v['observation_id']:[{k:h[k] for k in keys} for h in v['hypotheses']] for v in explanation_rows}
        ctx=c.get('context',{})
        out[case_id]={'schemaVersion':1,**bind,'evidenceVersion':digest(c),'grid':grid_identity(case_id,m['grid']),
            'referenceId':by_time[c['reference']],'observations':observations,'pairs':pairs,'footprints':footprints,
            'coherenceComparisons':comparisons,
            'claimReview':{k:validation[k] for k in ('protocolSha256','validatedClaims','heldOutLabels','status')} |
                          {'descriptiveReferenceRows':validation['cases'][case_id]['descriptiveReferenceRows'],
                           'matchedRows':validation['cases'][case_id]['matchedRows'],
                           'damageProxy':{'status':'unavailable','reason':'A dated event, a clean pre-event pair, stable controls and independent held-out damage labels are required.'},
                           'displacement':{'status':phase['status'],'reason':phase['benchmark'],
                                           'requiredChecks':phase['requiredChecks']}},
            'reviewRule':{'version':'footprint-radar-dark-v1','hhMaxDb':HH_DARK_DB,'hvMaxDb':HV_DARK_DB} if reviews else None,
            'acquisitionGaps':acquisition_gaps(path,m,observations,case_id),
            'environment':context_metadata(root,case_id,path,observations,c,imerg),
            'quality':{'gcov':quality,'terrain':terrain_metadata(public/'cases',path,case_id,observations,hand_audit['cases'][case_id]),
                       'gunw':{p['pair_id']:{**p['statistics']['20'],'sourceMask':p['rasters']['mask20'],
                                           'validMask':p['rasters']['coherence_valid20'],
                                           'coherenceRaster':p['rasters']['coherence20'],
                                           'coherenceRaster80':p['rasters']['coherence80']} for p in m['interferometry']}},
            'hypotheses':{'version':rule_table['model_version'],'templates':templates,
                          'nativeMinPairedFraction':MIN_NATIVE_RULE_SUPPORT},
            'context':{'thermal':[{'id':x['source'],'utc':x['timestamp']} for x in ctx.get('thermal',[])],
                       'scenarios':[{'id':x['id'],'observationId':by_time[t]} for t,a in ctx.get('scenarios',{}).items() for x in a],
                       'rain':[{'id':'power:'+by_time[t],'observationId':by_time[t],'provider':'NASA POWER'} for t in ctx.get('rain',{})],
                       'terrainManifestSha256':c['terrain']['source_manifest_sha256']},
            'capabilities':{'layers':['hh','hv','fraction']+(['coherence'] if pairs else []),
                            'portableFootprints':['saved'],'localFootprints':['saved','point','polygon'],
                            'lenses':{'jamuna_river':['river','surface'],'tanguar_wetland':['wetland','surface']}.get(case_id,['surface'])}}
        if c['country']=='Bangladesh' and pairs:
            out[case_id]['previousIntensityEvidenceVersion'] = digest({**c, 'pairs': [], 'pair_comparison': None})
    return out


def write_catalog(root=ROOT,check=False):
    target = root/'web/atlas-contract-records.json'
    raster_output = None if check else root/'output/atlas/coherence'
    expected = json.dumps(build_catalog(root,raster_output),indent=2,allow_nan=False)+'\n'
    if check:
        if target.read_text()!=expected:
            raise ValueError('Atlas identity catalog is stale: rebuild it from the accepted record')
    else:
        target.write_text(expected)
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    print(write_catalog(check=parser.parse_args().check))
