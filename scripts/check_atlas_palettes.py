"""Deterministic luminance and simulated color-vision checks on pinned swatches."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PALETTES = ROOT/'data/palettes/v1'
TABLE_SHA256 = {
    'cividis': 'ba3f731045fd4b4f9d5db9d68a2955136bd63eed2fe8eb61b6f35ddb0adcaecd',
    'vik': '200071b30c639c159791495358e51b9a99734c3119412582aeb1d6e1ac58720d',
}
# Machado, Oliveira and Fernandes (2009), doi:10.1109/TVCG.2009.113.
# Severity 100 linear-sRGB matrices from the authors' supplemental table.
VISION = {
    'normal': np.eye(3),
    'grayscale': np.tile([.2126, .7152, .0722], (3, 1)),
    'protan': [[.152286, 1.052583, -.204868], [.114503, .786281, .099216], [-.003882, -.048116, 1.051998]],
    'deutan': [[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.011820, .042940, .968881]],
    'tritan': [[1.255528, -.076749, -.178779], [-.078411, .930809, .147602], [.004733, .691367, .303900]],
}


def linear(rgb):
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def hex_color(rgb):
    srgb = np.where(rgb <= .0031308, 12.92*rgb, 1.055*rgb**(1/2.4)-.055)
    return '#'+''.join(f'{x:02x}' for x in np.rint(srgb*255).astype(int))


def check():
    provenance = json.loads((PALETTES/'provenance.json').read_text())
    for name, meta in provenance.items():
        if name != 'origin':
            assert hashlib.sha256((PALETTES/name).read_bytes()).hexdigest() == meta['sha256']
    report = {}
    for name, digest in TABLE_SHA256.items():
        raw = (PALETTES/(name+'.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        table = np.asarray(json.loads(raw))
        assert table.shape == (256, 3) and np.all((0 <= table) & (table <= 1))
        # Interpolate a symmetric 9-stop legend, with zero at position 0.5 for vik.
        t = np.linspace(0, 255, 9)
        stops = linear(np.column_stack([np.interp(t, np.arange(256), table[:, k]) for k in range(3)]))
        rows = {}
        for condition, matrix in VISION.items():
            colors = np.clip(stops @ np.asarray(matrix).T, 0, 1)
            luminance = colors @ [.2126, .7152, .0722]
            direction = np.ones(8) if name == 'cividis' else [1, 1, 1, 1, -1, -1, -1, -1]
            assert np.all(np.diff(luminance)*direction > 0), (name, condition, luminance.tolist())
            rows[condition] = {'swatches': [hex_color(rgb) for rgb in colors],
                               'relative_luminance': luminance.round(4).tolist()}
        report[name] = {'sha256': digest, 'center': '0 dB' if name == 'vik' else None, 'simulation': rows}
    return report


def render_swatches(report, destination):
    from PIL import Image, ImageDraw

    image = Image.new('RGB', (890, 490), '#142832')
    draw = ImageDraw.Draw(image)
    for index, (palette, details) in enumerate(report.items()):
        top = 14+index*237
        title = 'Cividis / low to high' if palette == 'cividis' else 'Vik / negative to positive'
        draw.text((20, top), title, fill='#eff7f8', font_size=19)
        for j, (vision, row) in enumerate(details['simulation'].items()):
            y = top+33+j*32
            draw.text((20, y+4), vision.capitalize(), fill='#cde4e7', font_size=14)
            for k, hex_rgb in enumerate(row['swatches']):
                x = 115+81*k
                draw.rectangle((x, y, x+80, y+23), fill=hex_rgb)
        for x, label in [(115, 'Low'), (768, 'High')] if palette == 'cividis' else [(115, 'Negative'), (440, '0 dB'), (768, 'Positive')]:
            draw.text((x, top+194), label, fill='#eff7f8', font_size=15)
    image.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swatches', type=Path, help='Optional PNG output of the simulated legend stops')
    options = parser.parse_args()
    report = check()
    if options.swatches:
        render_swatches(report, options.swatches)
    print(json.dumps(report, indent=2))
