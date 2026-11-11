"""Validate the native GeoTIFF downloads linked by the Atlas quality inspector."""
from collections import Counter
import json
from pathlib import PurePosixPath

from package_atlas_static import COG_VALIDATOR, ROOT, verify_cogs


def atlas_quality_rasters(quality):
    for visit in quality['gcov'].values():
        for channel in ('hh', 'hv'):
            yield 'GCOV HH/HV', visit[channel]['raster']
    for layer in quality['terrain']['layers'].values():
        yield 'Terrain', layer['raster']
    for pair in quality['gunw'].values():
        for field in ('sourceMask', 'validMask', 'coherenceRaster', 'coherenceRaster80'):
            yield 'GUNW coherence and masks', pair[field]


def main():
    public = (ROOT/'web/public').resolve()
    catalog = json.loads((ROOT/'web/atlas-contract-records.json').read_text())
    inventory = {}
    for case, record in catalog.items():
        for kind, url in atlas_quality_rasters(record['quality']):
            path = PurePosixPath(url)
            if path.parts[:3] != ('/', 'cases', case) or '..' in path.parts:
                raise ValueError(f'Unexpected Atlas raster path in {case}: {url}')
            name = path.relative_to('/').as_posix()
            raster = public/name
            if not raster.is_file() or not raster.resolve().is_relative_to(public/'cases'/case):
                raise ValueError(f'Atlas raster is missing or outside its study window: {name}')
            inventory[name] = {'role': 'COG', 'kind': kind}
    if not inventory:
        raise ValueError('The Atlas quality inspector lists no native rasters.')

    result = verify_cogs(public, inventory)
    counts = Counter(item['kind'] for item in inventory.values())
    print(json.dumps({'validator': 'rio-cogeo '+COG_VALIDATOR, 'strict': True,
                      'uniqueDownloads': len(inventory), 'byKind': dict(counts), **result}, indent=2))
    return int(result['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
