"""Frozen reference matching and descriptive overlaps; never accuracy metrics."""
from datetime import datetime,timezone
import numpy as np

def utc(t):return datetime.fromisoformat(t.replace('Z','+00:00')).astimezone(timezone.utc)
def choose_reference(candidates,timestamp,tolerance_seconds):
    candidates=[c for c in candidates if abs((utc(c['timestamp'])-utc(timestamp)).total_seconds())<=tolerance_seconds]
    return min(candidates,key=lambda c:(abs((utc(c['timestamp'])-utc(timestamp)).total_seconds()),c.get('cloud_cover',100),c['id'])) if candidates else None

def hls_quality(flags):
    flags=np.asarray(flags);return (flags!=255)&((flags&31)==0), (flags&32)!=0

def descriptive_overlap(radar_dark,reference_water,valid,pixel_area_km2):
    valid=np.asarray(valid,bool);r=np.asarray(radar_dark,bool);w=np.asarray(reference_water,bool)
    if r.shape!=w.shape or r.shape!=valid.shape:raise ValueError('Matched grid required')
    if not valid.any():return {'status':'unavailable','assessable_area_km2':0.,'reference_water_area_km2':None,'intersection_area_km2':None}
    return {'status':'date-matched, descriptive','assessable_area_km2':int(valid.sum())*pixel_area_km2,'reference_water_area_km2':int((w&valid).sum())*pixel_area_km2,'radar_dark_area_km2':int((r&valid).sum())*pixel_area_km2,'intersection_area_km2':int((r&w&valid).sum())*pixel_area_km2,'interpretation':'Pixel-center, nearest-grid descriptive overlap. No precision/recall/IoU or calibrated water truth.'}
