"""Cache four small WorldCover crops from the official 2021 v200 tile service."""
import json
import sys
from hashlib import sha256
from pathlib import Path

import rasterio
import numpy as np
from affine import Affine
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_landcover import DOI, LABELS, atlas_landcover_path

TILES = {'jamuna_river': 'N24E087', 'tanguar_wetland': 'N24E090',
         'nepal_surface': 'N27E084', 'nepal_impact_corridor': 'N27E084'}
BASE = 'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'


def main():
    records = json.loads((ROOT/'web/atlas-record.json').read_text())
    for case,tile in TILES.items():
        grid = records[case]['grid']
        height, width = grid['shape']
        url = BASE+f'ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
        target = atlas_landcover_path(ROOT, case)
        receipt = target.with_suffix('.json')
        if target.is_file() and receipt.is_file() and json.loads(receipt.read_text())['sha256']==sha256(target.read_bytes()).hexdigest():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix('.part.tif')
        transform = Affine(*grid['affine'])
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_TIMEOUT='30'):
            with rasterio.open(url) as dataset:
                if dataset.crs.to_epsg()!=4326 or dataset.count!=1 or dataset.dtypes[0]!='uint8':
                    raise ValueError('Unexpected WorldCover source grid')
                with WarpedVRT(dataset, crs=grid['crs'], transform=transform, width=width, height=height,
                               nodata=0, resampling=Resampling.nearest) as crop:
                    values = crop.read(1)
        observed = set(np.unique(values))
        if not observed <= LABELS | {0} or observed == {0}:
            raise ValueError('WorldCover window has no recognized labels')
        with rasterio.open(partial,'w',driver='GTiff',width=width,height=height,count=1,dtype='uint8',
                           crs=grid['crs'],transform=transform,nodata=0,compress='deflate',tiled=True) as output:
            output.write(values,1)
        partial.replace(target)
        receipt.write_text(json.dumps({'source':url,'doi':DOI,'year':2021,'crs':grid['crs'],
            'sha256':sha256(target.read_bytes()).hexdigest()},indent=2)+'\n')
        print(case, target.stat().st_size, flush=True)


if __name__ == '__main__':
    main()
