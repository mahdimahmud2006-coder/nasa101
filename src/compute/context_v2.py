"""Exact UTC rain windows and conservative terrain/geometry screening."""
from datetime import datetime,timezone,timedelta
import numpy as np

def utc(t):
    value=datetime.fromisoformat(t.replace('Z','+00:00'))
    if value.tzinfo is None:raise ValueError('Explicit timezone required')
    return value.astimezone(timezone.utc)
def iso(t):return t.isoformat().replace('+00:00','Z')
def rain_window(end,start=None,hours=None):
    end=utc(end);start=utc(start) if start else end-timedelta(hours=hours)
    if end<=start:raise ValueError('Rain window must have positive duration')
    return {'start_inclusive_utc':iso(start),'end_exclusive_utc':iso(end),'duration_seconds':(end-start).total_seconds(),'definition':'Exact UTC half-open window; partial half-hour bins are duration-weighted assuming constant mean rate inside each bin.'}
def integrate_rain(times,rates,window,bin_seconds=1800):
    times=np.asarray(times,dtype='int64');values=np.asarray(rates,dtype='float64')
    if len(times)!=len(values) or np.any(np.diff(times)<=0):raise ValueError('Unique increasing bin starts required')
    start,end=utc(window['start_inclusive_utc']).timestamp(),utc(window['end_exclusive_utc']).timestamp()
    expected=np.arange(int(start//bin_seconds)*bin_seconds,int(np.ceil(end/bin_seconds))*bin_seconds,bin_seconds)
    chosen=(times<end)&(times+bin_seconds>start);ts=times[chosen]
    if not np.array_equal(ts,expected):return {'total_mm':None,'status':'unavailable','reason':'missing half-hour bins','expected_bins':len(expected),'observed_bins':len(ts)}
    data=values[chosen];weight=(np.minimum(ts+bin_seconds,end)-np.maximum(ts,start))/3600
    if not np.isfinite(data).all() or (data<0).any():return {'total_mm':None,'status':'unavailable','reason':'missing/fill precipitation values'}
    return {'total_mm':float(np.sum(data*weight)),'status':'measured','bins':len(ts),'units':'mm'}
def geometry_candidates(dem,resolution,incidence,east,north,convergence_degrees=0):
    # Rotate true ENU LOS into projected grid axes using meridian convergence.
    angle=np.radians(convergence_degrees);ux=east*np.cos(angle)-north*np.sin(angle);uy=east*np.sin(angle)+north*np.cos(angle)
    row,gx=np.gradient(dem.astype('float64'),resolution);gy=-row;length=np.hypot(ux,uy)
    valid=np.isfinite(dem)&np.isfinite(incidence)&np.isfinite(ux)&np.isfinite(uy)&(incidence>0)&(incidence<90)&(length>0)
    toward=np.degrees(np.arctan(np.divide(gx*ux+gy*uy,length,out=np.full_like(gx,np.nan),where=length>0)))
    bits=np.zeros(dem.shape,dtype='uint8');slope=np.degrees(np.arctan(np.hypot(gx,gy)))
    bits[valid&(slope>=30)]|=1
    bits[valid&(toward<=-incidence)]|=2
    bits[valid&(toward>=90-incidence)]|=4
    bits[~valid]=255
    return bits

def stable_targets(first_hh,first_hv,elevation,slope):
    valid=np.isfinite(first_hh)&np.isfinite(first_hv)&np.isfinite(elevation)&np.isfinite(slope)
    if not valid.any():return np.zeros(valid.shape,bool),{'status':'unavailable','reason':'no first-date/DEM common support'}
    hcut=float(np.percentile(first_hh[valid],85));zcut=float(np.percentile(elevation[valid],50))
    selected=valid&(first_hh>=hcut)&(elevation>=zcut)&(slope<10)
    return selected,{'status':'implemented','hh_first_percentile':85,'hh_cutoff_db':hcut,'elevation_first_percentile':50,'elevation_cutoff_m':zcut,'maximum_slope_degrees':10,'selected_pixels':int(selected.sum()),'selection':'First date and DEM only; fixed before examining later-date control statistics. Putative stable bright/high targets, not independently validated built-up or stable ground.'}
