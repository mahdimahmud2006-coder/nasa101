/** Presentation policies for the additive record. No observations are synthesized. */
export const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const number=v=>v===null||v===undefined?'Unavailable':Number(v).toLocaleString('en-US',{maximumFractionDigits:3});
export const isCoherence=layer=>layer==='coherence20'||layer==='coherence80';
export function pairForVisit(manifest,index){return manifest.interferometry.find(p=>p.timestamps[1]===manifest.observations[index]?.timestamp)||null;}
export function sourceFor(manifest,index,layer){
 if(isCoherence(layer))return pairForVisit(manifest,index)?.layers[layer]||null;
 return manifest.observations[index]?.layers[layer]||null;
}
export function playbackIndices(manifest,layer){return manifest.observations.map((_,i)=>i).filter(i=>Boolean(sourceFor(manifest,i,layer)));}
export function readExpandedView(hash){
 const p=new URLSearchParams(hash.replace(/^#/,''));
 return {case:['nepal_surface','nepal_impact_corridor'].includes(p.get('case'))?p.get('case'):'nepal_surface',date:p.get('date'),layer:p.get('layer'),point:p.get('point'),footprint:p.get('footprint')==='1'?1:0};
}
export function traceSVG(profile,manifest,index){
 const rows=profile?.observations||[];if(!rows.length)return '<p>No fixed-footprint measurements available.</p>';
 const w=1200,h=310,left=70,right=30,top=30,bottom=62,dates=rows.map(r=>Date.parse(r.timestamp));
 const values=rows.flatMap(r=>[r.hh_reference_delta_db,r.hv_reference_delta_db]).filter(v=>Number.isFinite(v));
 if(!values.length)return '<p>No pixels remain valid across every visit. Missing measurements stay unavailable.</p>';
 const min=Math.min(-1,...values),max=Math.max(1,...values),pad=(max-min)*.12,low=min-pad,high=max+pad;
 const x=t=>left+(t-dates[0])/(dates.at(-1)-dates[0]||1)*(w-left-right),y=v=>top+(high-v)/(high-low)*(h-top-bottom);
 const gap=manifest.instrument_gap;
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Recorded HH and HV changes from August 19 on a fixed common-valid footprint; positions use elapsed time"><title>Measured HH and HV changes at recorded acquisitions</title>`;
 for(let i=0;i<=4;i++){const v=low+(high-low)*i/4;svg+=`<path d="M${left},${y(v)} H${w-right}" stroke="#304854"/><text x="${left-12}" y="${y(v)+5}" fill="#b8cdd3" text-anchor="end" font-size="14">${v.toFixed(1)}</text>`;}
 svg+=`<text x="15" y="25" fill="#b8cdd3" font-size="14">dB</text><path d="M${x(Date.parse(manifest.reference_timestamp))},${top} V${h-bottom}" stroke="#d5b47c" stroke-dasharray="4 5"/><path d="M${x(dates[index])},${top} V${h-bottom}" stroke="#e5eff1" opacity=".6"/>`;
 for(const [pol,color] of [['hh','#6de5d0'],['hv','#d5a7fd']]){
  rows.forEach((r,i)=>{const v=r[pol+'_reference_delta_db'];if(!Number.isFinite(v))return;
   const prior=rows[i-1]?.[pol+'_reference_delta_db'];
   if(i&&Number.isFinite(prior)){const crosses=dates[i-1]<Date.parse(gap.end)&&dates[i]>Date.parse(gap.start);if(!crosses)svg+=`<path d="M${x(dates[i-1])},${y(prior)} L${x(dates[i])},${y(v)}" fill="none" stroke="${color}" stroke-width="2.5"/>`;}
   svg+=`<circle cx="${x(dates[i])}" cy="${y(v)}" r="${i===index?6:4}" fill="${color}"><title>${pol.toUpperCase()} ${escape(r.timestamp)}: ${number(v)} dB</title></circle>`;
  });
 }
 rows.forEach((r,i)=>{svg+=`<text x="${x(dates[i])}" y="${h-bottom+28}" fill="#b8cdd3" font-size="13" text-anchor="middle">${escape(r.timestamp.slice(5,10))}</text>`;});
 return svg+`<text x="${left}" y="${h-8}" fill="#6de5d0" font-size="15">HH</text><text x="${left+60}" y="${h-8}" fill="#d5a7fd" font-size="15">HV</text><text x="${w-right}" y="${h-8}" fill="#b8cdd3" font-size="14" text-anchor="end">2026 · observed endpoints only · reference August 19</text></svg>`;
}
