"""Summarize historical ESA WorldCover labels on the selected native radar support."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from rasterio.windows import Window

DOI = '10.5281/zenodo.7254221'
LABELS = {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}


def atlas_landcover_path(root, case):
    return Path(root)/'data/context/atlas-worldcover'/f'{case}.tif'


def landcover_summary(path, grid, support, window: Window | None = None):
    from src.compute.atlas_spatial import read_atlas_plane

    if not path.is_file():
        return None
    receipt = json.loads(path.with_suffix('.json').read_text())
    if receipt['sha256']!=sha256(path.read_bytes()).hexdigest() or receipt['doi']!=DOI:
        raise ValueError('WorldCover crop does not match its source receipt')
    plane = read_atlas_plane(path.parent, path.parent, path.name, grid, window).filled(0)
    if plane.shape != support.shape:
        raise ValueError('Land cover does not align with the radar footprint')
    classes = plane[support]
    counts = np.bincount(classes, minlength=101)
    known = int(sum(counts[code] for code in LABELS))
    if np.count_nonzero(classes) != known:
        raise ValueError('Unexpected ESA WorldCover code')
    return {'year': 2021, 'version': 'v200', 'doi': DOI, 'source':receipt['source'], 'cropSha256':receipt['sha256'],
            'validCells': known, 'pairedCells': int(classes.size),
            'croplandCells': int(counts[40]), 'builtUpCells': int(counts[50]),
            'radarCellAreaM2': grid['pixel_area_km2']*1e6}
