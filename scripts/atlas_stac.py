"""Build STAC 1.1 records for the Atlas previews and the local raster catalog."""
import json
from pathlib import Path

from affine import Affine
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.geometry.polygon import orient

VERSION = '1.1.0'


def spatial_extent(grid):
    height, width = grid['shape']
    transform = Affine(*grid['affine'])
    to_wgs84 = Transformer.from_crs(grid['crs'], 4326, always_xy=True)
    points = [to_wgs84.transform(*(transform*p), errcheck=True)
              for p in [(0, 0), (width, 0), (width, height), (0, height)]]
    outline = orient(Polygon(points), sign=1)
    return mapping(outline), list(outline.bounds)


def catalog_documents(records, identities, *, native=False):
    root = {'stac_version': VERSION, 'type': 'Catalog', 'id': 'terrapulse',
            'description': 'TerraPulse study-window derivatives from provisional NASA–ISRO NISAR and NASADEM.',
            'links': [{'rel': 'root', 'href': './catalog.json', 'type': 'application/json'}]}
    items = {}

    def add(case, key, grid, dates, granule_ids, assets):
        item_id = f'{case}-{key}'
        geometry, bbox = spatial_extent(grid)
        time = {'datetime': dates[0]} if len(dates) == 1 else {
            'datetime': None, 'start_datetime': dates[0], 'end_datetime': dates[1]}
        items[f'items/{item_id}.json'] = {
            'stac_version': VERSION, 'type': 'Feature', 'id': item_id,
            'geometry': geometry, 'bbox': bbox,
            'properties': {**time, 'title': records[case]['title'],
                           'terrapulse:source_ids': granule_ids,
                           'terrapulse:manifest_sha256': identities[case]['manifestSha256']},
            'links': [{'rel': rel, 'href': '../catalog.json', 'type': 'application/json'}
                      for rel in ('root', 'parent')], 'assets': assets}
        root['links'].append({'rel': 'item', 'href': f'./items/{item_id}.json', 'type': 'application/geo+json'})

    def asset(url, kind):
        if native:
            path = Path(url)
            if path.parts[:2] != ('/', 'cases') or '..' in path.parts or path.suffix != '.tif':
                raise ValueError('Unexpected native catalog asset')
            return {'href': '../..'+url, 'type': 'image/tiff; application=geotiff; profile=cloud-optimized',
                    'roles': ['data']}
        if not url.startswith('./') or not url.endswith('.webp') or '..' in Path(url).parts:
            raise ValueError('Unexpected public catalog asset')
        return {'href': '../../'+url[2:], 'type': 'image/webp', 'roles': ['thumbnail'], 'title': kind}

    for case, record in records.items():
        meta = identities[case]
        for visit in record['observations']:
            oid = visit['observation_id']
            layers = {band: meta['quality']['gcov'][oid][band]['raster'] for band in ('hh','hv')} if native else visit['images']
            add(case, oid, meta['grid'], [visit['timestamp']], [visit['source_granule_id']],
                {band: asset(url, band.upper()+' preview') for band,url in layers.items()})
        for pair, frame in zip(meta['pairs'], record['pairs'], strict=True):
            layers = {name: meta['quality']['gunw'][pair['id']][name] for name in
                      ('coherenceRaster','coherenceRaster80','sourceMask','validMask')} if native else {'coherence':frame['image']}
            add(case, pair['id'], pair['grid'], frame['dates'], [pair['sourceId']],
                {name: asset(url, 'HH coherence preview') for name,url in layers.items()})
        if native:
            terrain = meta['quality']['terrain']
            add(case, 'nasadem', terrain['grid'], ['2000-02-11T00:00:00Z','2000-02-22T23:59:59Z'],
                ['10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001'],
                {name: asset(layer['raster'], name) for name,layer in terrain['layers'].items()})
    return {'catalog.json':root, **items}


if __name__ == '__main__':
    from package_atlas import ROOT

    web = ROOT/'web'
    record = json.loads((web/'atlas-record.json').read_text())
    identities = json.loads((web/'atlas-contract-records.json').read_text())
    output = ROOT/'output/atlas/native-stac'
    documents = catalog_documents(record, identities, native=True)
    for name, doc in documents.items():
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, allow_nan=False)+'\n')
    print(f'{output}/catalog.json · {len(documents)-1} items')
