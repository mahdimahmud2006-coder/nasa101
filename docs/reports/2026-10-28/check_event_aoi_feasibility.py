from pathlib import Path
import json
import h5py,numpy as np
from affine import Affine
from pyproj import Transformer
from shapely.geometry import box
from shapely import wkt
from shapely.ops import transform
from src.compute.validation_context import official_extent
mapped,digest,rings=official_extent('data/context/unosat_20260826_flood_extent.zip')
audit=json.loads(Path('data/derived/nepal_case_01/timeseries/source_audit.json').read_text())
to_geo=Transformer.from_crs('EPSG:32645','EPSG:4326',always_xy=True).transform
parts=list(mapped.geoms) if hasattr(mapped,'geoms') else [mapped]
points=[p.representative_point() for p in parts]
center=mapped.centroid;window=box(center.x-12000,center.y-12000,center.x+12000,center.y+12000)
report={'source_archive_sha256':digest,'original_ring_count':rings,'geometry_parts':len(parts),'mapped_geometry_area_km2':mapped.area/1e6,
 'independent_geometry_centroid_wgs84':list(to_geo(center.x,center.y)),'illustrative_24km_window_overlap_km2':mapped.intersection(window).area/1e6,
 'interpretation':'Read-only geographic/point-validity feasibility, not a completed event-centered case or accuracy validation. Mapping represents preliminary mudflow/rockflow impacts, not flood-water extent. Point samples do not certify all-pixel coverage.','observations':[]}
for name in ['aug19.h5','aug31.h5','sept12.h5']:
 o=next(r for r in audit['records'] if r['source_file']==name);x,y=o['origin_center'];dx,dy=o['spacing'];inv=~Affine(dx,0,x-dx/2,0,dy,y-dy/2)
 project=Transformer.from_crs('EPSG:4326',o['crs'],always_xy=True).transform
 footprint=transform(project,wkt.loads(o['footprint_wkt']))
 valid=0;within=0
 with h5py.File(name,'r') as f:
  for p in points:
   col,row=inv*(p.x,p.y);row,col=int(np.floor(row)),int(np.floor(col))
   if not 0<=row<o['shape'][0] or not 0<=col<o['shape'][1]:continue
   within+=1;grid=o['grid_path'];power=float(f[o['layer_path']][row,col]);mask=int(f[grid+'/mask'][row,col]);looks=float(f[grid+'/numberOfLooks'][row,col])
   valid+=bool(np.isfinite(power) and power>0 and 0<mask<255 and np.isfinite(looks) and looks>0)
 report['observations'].append({'source_file':name,'source_footprint_intersection_km2':footprint.intersection(mapped).area/1e6,'sampled_points_within_grid':within,'sampled_points_positive_quality_valid':valid})
Path('docs/reports/2026-10-28/event_aoi_feasibility.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps(report,indent=2))
