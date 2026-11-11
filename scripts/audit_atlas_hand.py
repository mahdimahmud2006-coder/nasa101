"""Audit candidate HAND support on accepted crop DEMs without publishing a HAND layer."""
import json
from hashlib import sha256
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.compute.atlas_admission import active_manifests, require_admitted
from src.compute.atlas_spatial import read_atlas_plane
from src.compute.environment import flow_metrics


def audit():
    manifests = active_manifests(ROOT)
    require_admitted(ROOT,manifests)
    cases = {}
    for case, path in manifests.items():
        folder = path.parent.parent/'context-v2'
        source = (folder/'manifest.json').read_bytes()
        context = json.loads(source)
        grid = context['grid']
        dem, slope = [read_atlas_plane(ROOT/'web/public/cases',folder,context['layers'][name]['raster'],grid).filled(float('nan'))
                      for name in ('dem','slope')]
        _, receipt = flow_metrics(dem,grid['resolution_m'],slope,hand_thresholds=(500_000,1_000_000,2_000_000))
        cases[case] = {'grid':grid,'contextManifestSha256':sha256(source).hexdigest(),
                       'verticalDatum':'EGM96 orthometric metres','published':False,**receipt}
    return {'schemaVersion':1,'scope':'Crop-only sensitivity audit. Boundaries and DEM voids are open outlets.',
            'routing':'Priority-flood conditioning, D8 descent with deterministic flat routing, no breach. Heights use the original DEM.',
            'gate':'Independent drainage comparison and buffer sensitivity are required before publishing a HAND layer.',
            'cases':cases}


if __name__=='__main__':
    print(json.dumps(audit(),indent=2))
