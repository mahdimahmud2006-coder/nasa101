/** Shared URL state contains observed identifiers only. No storage, network or interpolation. */
export const viewKeys=['case','date','footprint','mode','overlay'];
const cases=['nepal_surface','nepal_impact_corridor','jamuna_river','tanguar_wetland'];
export function readView(hash=''){
 const p=new URLSearchParams(hash.replace(/^#/,'')),v={};
 if(cases.includes(p.get('case')))v.case=p.get('case');
 if(/^\d{4}-\d{2}-\d{2}(?:T[\d:.]+Z)?$/.test(p.get('date')||''))v.date=p.get('date');
 const f=p.get('footprint')||'';
 if(f.length<=12000&&/^(?:saved:\d+|point:\d+,\d+|polygon:\[|zone:[\w-]+|region:\d+)/.test(f))v.footprint=f;
 if(['surface','river','wetland'].includes(p.get('mode')))v.mode=p.get('mode');
 if(/^[a-z][a-z0-9_-]{0,50}$/.test(p.get('overlay')||''))v.overlay=p.get('overlay');
 return v;
}
export function viewHash(view){const p=new URLSearchParams();for(const k of viewKeys)if(view[k])p.set(k,String(view[k]));return '#'+p.toString();}
export function writeView(view,win=globalThis.window){
 if(!win?.history?.replaceState)return;
 const hash=viewHash(view);if(win.location.hash!==hash)win.history.replaceState(null,'',hash);
 win.dispatchEvent?.(new Event('terrapulse:view'));
}
export function workspaceHref(path,view){
 const legacy=path!=='/investigations.html';
 const selected=legacy?{...view,case:'nepal_surface',mode:'surface',footprint:view.case==='nepal_surface'?view.footprint:undefined,date:view.case==='nepal_surface'?view.date:undefined,overlay:undefined}:view;
 return path+viewHash(selected);
}
export function legacyChoice(view,observations,defaultIndex=observations.length-1){
 const index=view.date?observations.findIndex(o=>(o.timestamp||o.acquisition_start)===view.date||(o.timestamp||o.acquisition_start)?.slice(0,10)===view.date):-1;
 const unsupported=view.case&&view.case!=='nepal_surface';
 return {index:unsupported?defaultIndex:index>=0?index:defaultIndex,note:unsupported?'Nepal · Kathmandu. The requested study area belongs to a different workspace; choose Bangladesh or Nepal above.':view.date&&index<0?'Requested date is not loaded here; displaying an available Nepal observation.':'Nepal · Kathmandu environmental analysis. Open Surface & coherence for the full radar record, or Evidence dossiers to inspect footprints.'};
}
