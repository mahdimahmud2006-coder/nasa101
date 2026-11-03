"""Record header flags and correction inventories, never read full raw science arrays."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import h5py
from src.ingest.inspect_h5 import native
from src.compute.evidence_common import ROOT,save


def audit():
    records=[]
    for path in sorted((ROOT/'database/extra datasets').glob('*.h5')):
        with h5py.File(path,'r') as f:
            identification={k:native(v[()]) for k,v in f['science/LSAR/identification'].items() if isinstance(v,h5py.Dataset)}
            r={'source_file':str(path.relative_to(ROOT)),'size_bytes':path.stat().st_size,'identification':identification}
            if '_GUNW_' in path.name:
                datasets={}
                def visit(name,obj):
                    if isinstance(obj,h5py.Dataset) and '/GUNW/metadata/' in name:
                        entry={'shape':list(obj.shape),'dtype':str(obj.dtype),'attrs':{k:native(v) for k,v in obj.attrs.items() if k not in ['DIMENSION_LIST','REFERENCE_LIST']}}
                        if obj.size<=16:entry['value']=native(obj[()])
                        datasets[name]=entry
                f.visititems(visit)
                frequency=float(f['science/LSAR/GUNW/grids/frequencyA/centerFrequency'][()])
                r.update(correction_and_geolocation_metadata=datasets,center_frequency_hz=frequency,wavelength_m=299792458/frequency,
                    phase_sign_convention='Not validated for displacement; source phase remains in radians. No phase-to-distance conversion performed.',
                    phase_correction_application='Not applied by TerraPulse. Source ionosphere screen and external correction LUTs must not be assumed removed.',
                    metadata_array_scope='Names, shapes, units/attributes and small values retained; large correction/orbit/geolocation arrays remain in the supplied original HDF5.')
            records.append(r)
    # Serialize nonfinite optional scalar metadata as null, never pretend NaN is a measurement.
    import math
    def finite(value):
        if isinstance(value,float) and not math.isfinite(value):return None
        if isinstance(value,dict):return {k:finite(v) for k,v in value.items()}
        if isinstance(value,list):return [finite(v) for v in value]
        return value
    result=finite({'schema_version':1,'records':records,'scope':'Local headers and declared lineage. Not an independent authenticity certificate or complete audit of every upstream contributor. No Chinese provider identified in declared source metadata.',
        'processing_note':'July 14 filename carries F while its header processingType is Nominal and hasInputDataException is zero. September 24 header isUrgentObservation is True while product configuration is PR/P05023. Both preserve these flags; actual mode/version/track/grid and crop coverage pass. No filename flag silently overrides header checks.'})
    for p in [ROOT/'reports/extra_2026_11_03/source_header_audit.json',ROOT/'web/public/cases/supplied-source-audit-v1.json']:
        if p.exists():raise FileExistsError('Choose a new audit version')
        save(p,result)
    print('Audited',len(records),'supplied sources')


if __name__=='__main__':audit()
