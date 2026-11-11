import {readView,workspaceHref} from './investigation-state.mjs';
/** Geographic navigation only. Source case identifiers and measurements are unchanged. */
export const bangladeshCases=['jamuna_river','tanguar_wetland'];
export function countryForCase(id){return bangladeshCases.includes(id)?'bangladesh':'nepal';}
export function casesForFocus(cases,mode,country='nepal'){
 return cases.filter(c=>mode==='surface'?countryForCase(c.case_id)===country:c.module===mode);
}
export function investigationContext(search='',view={}){
 const p=new URLSearchParams(search),mode=view.mode||p.get('mode')||'surface';
 const country=view.case?countryForCase(view.case):['river','wetland'].includes(mode)?'bangladesh':p.get('country')==='bangladesh'?'bangladesh':'nepal';
 return {country,mode:['surface','river','wetland'].includes(mode)?mode:'surface'};
}
export function focusCopy(country,mode){
 if(country==='bangladesh')return mode==='river'
  ?{title:'River Memory',eyebrow:'BANGLADESH / JAMUNA RIVER',description:'Follow radar-dark signatures along the Jamuna. Compare where they appear, recede and persist across observed visits.'}
  :mode==='wetland'?{title:'Wetland Pulse',eyebrow:'BANGLADESH / TANGUAR HAOR',description:'Follow the changing radar response of a wetland landscape. Explore dark and bright signatures alongside terrain and optical context.'}
  :{title:'Surface change',eyebrow:'BANGLADESH / JAMUNA & TANGUAR',description:'Inspect any footprint in the two Bangladesh study areas. Compare both radar channels, trace persistent differences and examine possible explanations.'};
 return {title:'Surface investigations',eyebrow:'NEPAL / KATHMANDU & RASUWA–NUWAKOT',description:'Follow a disturbance from its first alert to later observations. Investigate persistence and compare the mapped impact corridor.'};
}
export function navigationContext(path,search='',hash=''){
 const p=new URLSearchParams(hash.replace(/^#/,'')),view={case:p.get('case'),mode:p.get('mode')};
 const root=path==='/'||path==='/index.html',guide=path==='/guide.html';
 const query=new URLSearchParams(search),lab=query.get('lab'),requestedCountry=query.get('country')||hash.slice(1);
 const simulations=root&&(query.get('view')==='simulations'||['surge','bank','slope','orbit','radar'].includes(lab));
 const landingCountry=root&&!simulations&&['bangladesh','nepal'].includes(requestedCountry)?requestedCountry:null;
 const home=root&&!simulations&&!landingCountry;
 const {country,mode}=investigationContext(search,view);
 const group=root?landingCountry:guide?null:path==='/investigations.html'?country:'nepal';
 const bd=[['River Memory','/investigations.html?country=bangladesh&mode=river','river'],['Wetland Pulse','/investigations.html?country=bangladesh&mode=wetland','wetland'],['Surface change','/investigations.html?country=bangladesh&mode=surface','surface']];
 const np=[['Surface & coherence','/expanded.html','/expanded.html'],['Evidence dossiers','/investigations.html?country=nepal&mode=surface','/investigations.html'],['Terrain & thermal','/studio.html','/studio.html'],['Change DNA & slopes','/change-lab.html','/change-lab.html'],['Timeline','/timeseries.html','/timeseries.html'],['Radar comparison','/comparison.html','/comparison.html']];
 const shared=readView(hash);
 return {home,guide,simulations,group,links:(group==='bangladesh'?bd:group==='nepal'?np:[]).map(([label,href,key])=>({label,href:group==='nepal'&&shared.case?.startsWith('nepal_')&&key!=='/expanded.html'?workspaceHref(key,shared):href,active:!root&&(group==='bangladesh'?mode===key:path===key)}))};
}
