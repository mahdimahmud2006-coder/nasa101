import {atlasElement,atlasNode} from './atlas-dom.mjs';
import {atlasDiscoveryCatalog} from './atlas-discovery-catalog.mjs';

const atlasDiscoveryProducts={
  Bangladesh:{
    title:'Surface water from Sentinel-1',name:'OPERA DSWx-S1',
    collection:'C2949811996-POCLOUD',layer:'OPERA_L3_Dynamic_Surface_Water_Extent-Sentinel-1',
    guide:'https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1',
    question:'Does mapped open water line up with the dark radar features? River stage and acquisition time can shift the apparent edge.'
  },
  Nepal:{
    title:'Vegetation disturbance from Landsat and Sentinel-2',name:'OPERA DIST-ALERT-HLS',
    collection:'C2746980408-LPCLOUD',layer:'OPERA_L3_DIST-ALERT-HLS_Color_Index',
    guide:'https://www.jpl.nasa.gov/go/opera/products/dist-product-suite/',
    question:'Does mapped vegetation disturbance overlap the change you see in radar? Use it to guide a field or event check.'
  }
};

const atlasDiscoveryHour=60*60*1000;
const atlasDiscoveryUtc=value=>value.replace(/\.\d+Z$/,'Z').replace('T',' ').replace('Z',' UTC');
function atlasDiscoveryCmr(params){
  return 'https://cmr.earthdata.nasa.gov/search/granules.json?'+new URLSearchParams(params);
}

export function atlasDiscoverySelection(c,current,pair){
  const product=atlasDiscoveryProducts[c.country],cached=atlasDiscoveryCatalog.cases[c.case];
  if(!product||!cached)return null;
  const {windowHours,checkedUtc}=atlasDiscoveryCatalog;
  const bounds=c.grid.bounds_wgs84.map((n,i)=>(Math[i<2?'floor':'ceil'](n*1e5)/1e5).toFixed(5)).join(',');
  function endpoint(label,anchor){
    const hit=cached.matches[anchor];
    const date=Date.parse(anchor),margin=windowHours*atlasDiscoveryHour;
    const range=[date-margin,date+margin].map(t=>new Date(t).toISOString()).join(',');
    const search=atlasDiscoveryCmr({collection_concept_id:product.collection,bounding_box:bounds,temporal:range,page_size:20});
    if(!hit)return {label,anchor,search};
    const [concept,utc,visible]=hit,offset=(Date.parse(utc)-date)/atlasDiscoveryHour;
    return {label,anchor,search,utc,offset,visible,record:atlasDiscoveryCmr({concept_id:concept})};
  }
  const endpoints=[endpoint(pair?'Pair end':'Selected visit',current)];
  const anchor=pair?pair.dates[0]:c.reference;
  if(anchor!==current)endpoints.push(endpoint(pair?'Pair start':'Fixed reference',anchor));
  if(!pair&&endpoints[0].visible&&endpoints[1]&&!endpoints[1].visible){
    const index=c.observations.findIndex(o=>o.timestamp===current);
    const previous=c.observations[index-1]?.timestamp;
    if(previous&&previous!==anchor&&cached.matches[previous]?.[2]){
      endpoints.push(endpoint('Previous visit',previous));
    }
  }
  const [first,second]=endpoints.filter(e=>e.visible);
  let worldview;
  const twoDates=second&&second.utc.slice(0,10)!==first.utc.slice(0,10);
  let browseLabel;
  if(first){
    const layers=product.layer+',BlueMarble_NextGeneration';
    const params={p:'geographic',v:bounds,l:layers,t:first.utc.slice(0,10)};
    if(twoDates)Object.assign(params,{l1:layers,t1:second.utc.slice(0,10),ca:'true',cm:'swipe',cv:'50'});
    worldview='https://worldview.earthdata.nasa.gov/?'+new URLSearchParams(params);
    browseLabel=twoDates
      ?(second.label==='Previous visit'?'Compare with previous visit':'Compare both dates')+' in NASA Worldview'
      :'View '+first.label.toLowerCase()+' in NASA Worldview';
  }
  return {product,endpoints,worldview,windowHours,checkedUtc,browseLabel};
}

export function renderAtlasDiscovery(c,current,pair){
  const el=atlasElement,box=atlasNode('discovery');
  const view=atlasDiscoverySelection(c,current,pair);
  box.hidden=!view;
  if(!view)return;
  const key=[c.case,current,pair?.dates[0]].join('/');
  if(box.dataset.selection===key)return;
  box.dataset.selection=key;
  const link=(label,url)=>{
    const a=el('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;
  };
  const {product,endpoints,worldview,windowHours,checkedUtc,browseLabel}=view;
  const content=atlasNode('discovery-content');
  const list=el('ul');
  for(const e of endpoints){
    const item=el('li');
    const timing=e.utc&&(e.offset===0?'same catalog time as radar':
      Math.abs(e.offset).toFixed(1)+' h '+(e.offset<0?'before':'after')+' radar');
    item.append(el('strong',e.label+' · '+atlasDiscoveryUtc(e.anchor)),
      el('span',e.utc?'Catalog candidate · '+atlasDiscoveryUtc(e.utc)+' · '+timing:
        'No candidate at the study center within '+windowHours+' hours in the saved search.'),
      link(e.utc?'NASA record (JSON)':'Search the full study area (JSON)',e.record??e.search));
    if(e.utc&&!e.visible)item.append(el('span',e.visible===false?'Browse map was blank near the study center.':'Browse map coverage could not be checked.'));
    list.append(item);
  }
  content.replaceChildren(el('p',product.title+' · '+product.name+' · 30 m'),el('p',product.question),list,
    ...(worldview?[link(browseLabel,worldview)]:[]),
    el('p','Catalog checked '+checkedUtc.slice(0,10)+'. Worldview shows daily browse maps. Check pixel coverage and quality before interpreting a match.'),
    link('NASA product guide',product.guide));
}
