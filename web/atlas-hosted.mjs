/** Read only the case and preview assets named in the checked release catalog. */
export function atlasHostedCase(hash,entries){
  if(typeof hash!=='string'||hash.length>24000)return null;
  const args=new URLSearchParams(hash.replace(/^#/,''));
  try{
    const id=args.get('atlas')==='2'?JSON.parse(args.get('view'))?.caseId:args.get('atlas')==='1'?args.get('case'):null;
    return id&&Object.hasOwn(entries,id)?id:null;
  }catch{return null;}
}

export function atlasHostedLoader(config,fetcher=(...args)=>fetch(...args)){
  const records={},catalog={},pending=new Map(),terrainPending=new Map();
  async function read(path){
    const response=await fetcher(path,{credentials:'omit'});
    if(!response.ok)throw Error('Saved evidence is unavailable. Try again or open the offline edition.');
    return response.json();
  }
  function ensure(id){
    if(!Object.hasOwn(config.cases,id))return Promise.reject(Error('Unknown study window.'));
    if(records[id])return Promise.resolve();
    if(!pending.has(id)){
      const item=config.cases[id];
      const request=read(item.data).then(({record,identity})=>{
        if(record.case!==id||identity.caseId!==id||record.manifest_sha256!==item.manifestSha256||
          identity.manifestSha256!==item.manifestSha256||identity.evidenceVersion!==item.evidenceVersion){
          throw Error('Saved evidence does not match this release.');
        }
        records[id]=record;catalog[id]=identity;
      }).finally(()=>pending.delete(id));
      pending.set(id,request);
    }
    return pending.get(id);
  }
  function terrain(id){
    const mesh=records[id].terrain;
    if(mesh.elevation_m)return Promise.resolve();
    if(!terrainPending.has(id)){
      const request=read(config.cases[id].terrain).then(values=>{
        if(!Array.isArray(values)||values.length!==mesh.size**2||
          !values.every(v=>v===null||Number.isFinite(v))||!values.some(Number.isFinite))throw Error('Terrain preview is invalid.');
        mesh.elevation_m=values;
      }).finally(()=>terrainPending.delete(id));
      terrainPending.set(id,request);
    }
    return terrainPending.get(id);
  }
  return {records,catalog,entries:config.cases,defaultCase:config.defaultCase,entryPreview:config.entryPreview,ensure,terrain};
}
