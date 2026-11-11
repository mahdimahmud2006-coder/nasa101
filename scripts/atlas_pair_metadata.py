"""Build display and export evidence from admitted native coherence products."""
from base64 import b64encode
from io import BytesIO

import numpy as np
from affine import Affine
from PIL import Image

from src.compute.atlas_contract import grid_identity
from src.compute.coherence_change import (coherence_delta, coherence_footprint, coherence_plane,
                                          coherence_summary, comparison_policy)
from src.compute.context_v2 import utc
from src.export.dualpol_render import css_gradient, load_palettes, palette_rgba


def pair_metadata(case, manifest, public, folder, by_time, footprints, phase, palette, output=None):
    pairs, planes = [], []
    for pair in sorted(manifest.get('interferometry', []), key=lambda p: p['timestamps']):
        identity = pair['identification']
        first, last = pair['timestamps']
        duration = int((utc(last) - utc(first)).total_seconds())
        grid = pair['grids']['20']
        raw = phase['pairs'][pair['pair_id']]
        if (not 0 < duration or duration != 86400*raw['temporalBaselineDays']
                or raw['sourceId'] != identity['granuleId'] or raw['frequencyHz'] != 1239e6
                or grid['native_spacing_m'] != 20
                or len(pair['source_slc_granules']) != 2 or any(len(v) != 1 for v in pair['source_slc_granules'])):
            raise ValueError('Coherence pair metadata does not match the accepted source')
        plane = coherence_plane(public, folder, pair)
        planes.append(plane)
        pairs.append({
            'id': pair['pair_id'], 'firstId': by_time[first], 'secondId': by_time[last],
            'startUtc': first, 'endUtc': last, 'sourceId': identity['granuleId'],
            'grid': grid_identity(case, grid), 'channel': 'HH', 'frequency': 'A', 'postingM': 20,
            'track': identity['trackNumber'], 'frame': identity['frameNumber'],
            'passDirection': identity['orbitPassDirection'], 'lookDirection': identity['lookDirection'],
            'productVersion': identity['productVersion'], 'release': identity['compositeReleaseId'],
            **({'sourceUrl': pair['source_url'], 'sourceSha256': pair['source_sha256']} if 'source_url' in pair else {}),
            'sourceSlc': [v[0] for v in pair['source_slc_granules']], 'intervalSeconds': duration,
            'baselineSampleM': raw['sampledPerpendicularBaselineM'], 'baselineSample': raw['baselineSample'],
            'baselineRangeM': raw['baselineRangeM'], 'baselineSampleCount': raw['baselineSampleCount'],
            'coverage': pair['statistics']['20'],
            'footprints': [coherence_summary(plane, coherence_footprint(f, manifest['grid'], grid)) for f in footprints],
        })
    if len({p['id'] for p in pairs}) != len(pairs) or len({p['secondId'] for p in pairs}) != len(pairs):
        raise ValueError('This atlas requires distinct pair identities and end visits')
    comparisons = []
    for i, (earlier, later) in enumerate(zip(pairs, pairs[1:])):
        if not comparison_policy(earlier, later):
            continue
        delta = coherence_delta(planes[i], planes[i+1])
        grid = earlier['grid']
        comparison = {
            'earlierId': earlier['id'], 'laterId': later['id'], 'gridId': grid['id'],
            'direction': 'later minus earlier', 'displayLimits': [-.5, .5],
            'gridPolicy': 'Identical native GUNW grids, joint valid mask. Only footprint membership is sampled at GUNW pixel centers.',
            'crop': coherence_summary(delta, np.ones(delta.shape, bool)),
            'footprints': [coherence_summary(delta, coherence_footprint(f, manifest['grid'], grid)) for f in footprints],
            'image': pair_delta_preview(delta, palette, max_edge=280 if case in ('jamuna_river','tanguar_wetland') else 460),
            'paletteCss': css_gradient(palette),
        }
        if output is not None:
            from src.compute.expanded_record import cog

            output.mkdir(parents=True, exist_ok=True)
            stem = f"{case}-{earlier['id']}-{later['id']}"
            cog(output/f'{stem}-delta.tif', delta, Affine(*grid['affine']), grid['crs'],
                'Descriptive signed coherence delta, later minus earlier; joint valid mask', np.nan)
            cog(output/f'{stem}-valid.tif', np.isfinite(delta).astype('uint8'), Affine(*grid['affine']),
                grid['crs'], 'Joint valid coherence support; 1 = valid, 0 = outside support', 0, True)
        comparisons.append(comparison)
    return pairs, comparisons


def pair_delta_preview(delta, palette, max_edge=460):
    height, width = delta.shape
    scale = min(1, max_edge/max(height, width))
    def centers(length):
        count = max(1, round(length*scale))
        return ((np.arange(count)+.5)*length/count).astype(int)
    rows, cols = centers(height), centers(width)
    image = Image.fromarray(palette_rgba(delta[np.ix_(rows, cols)], [-.5, .5], palette))
    buf = BytesIO()
    image.save(buf, format='WEBP', lossless=True)
    return 'data:image/webp;base64,' + b64encode(buf.getvalue()).decode()


def coherence_palette(root):
    return load_palettes(root/'data/palettes/v1')['vik']
