import {atlasScenarioParameters} from './atlas-state.mjs';

function atlasScenarioRequest(s,o,model){
  const anchor=model?.anchors[o.observation_id];
  const parameters=s.scenarioRun&&atlasScenarioParameters(s.scenarioRun);
  return parameters&&anchor?{...parameters,observation_id:anchor,historical_sensitivity:false}:null;
}

async function atlasRequestScenario(fetcher,model,request,signal){
  const response=await fetcher('/api/cases/nepal_case_01/scenario/flood',{method:'POST',signal,
    headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
  const value=await response.json();
  if(!response.ok)throw Error(value.error||'Scenario calculation unavailable.');
  if(value.case_id!=='nepal_case_01'||value.model_version!==model.modelVersion||
    value.inputs_sha256!==model.inputsSha256||Object.keys(request).some(k=>value.parameters?.[k]!==request[k])||
    !/^flood-[a-f0-9]{20}$/.test(value.scenario_id)||
    value.preview_url!=='/cases/nepal_case_01/flood/scenarios/'+value.scenario_id+'/scenario.png'){
    throw Error('Scenario response does not match the selected date, settings or accepted inputs.');
  }
  return value;
}

export function createAtlasScenarios({portable,changed,fetcher=(...args)=>fetch(...args)}){
  let key='',controller=null,result=null,status='';
  const requestKey=(s,o,model,request)=>request?JSON.stringify([s.case,o.observation_id,model.modelVersion,model.inputsSha256,request]):'';
  function select(s,o,model){
    const request=atlasScenarioRequest(s,o,model),next=requestKey(s,o,model,request);
    if(next===key)return {result,status};
    controller?.abort();
    key=next;result=null;status='';
    if(!request)return {result,status};
    if(portable){
      status='This custom scenario needs the local runtime. Saved scenarios are available below.';
      return {result,status};
    }
    status='Running the dated Kathmandu scenario…';
    const pending=new AbortController();
    controller=pending;
    atlasRequestScenario(fetcher,model,request,pending.signal).then(value=>{
      if(!pending.signal.aborted){result=value;status='';changed();}
    }).catch(error=>{
      if(!pending.signal.aborted){status=error.message;changed();}
    });
    return {result,status};
  }
  return {select,get:()=>result,retry:()=>{key='';},
    async replay(s,o,model){
      const request=atlasScenarioRequest(s,o,model);
      if(portable||!request)throw Error('The dated scenario inputs are unavailable in this edition.');
      return atlasRequestScenario(fetcher,model,request);
    },
    restore(s,o,model,value){
      controller?.abort();
      key=requestKey(s,o,model,atlasScenarioRequest(s,o,model));result=value;status='';
    }};
}
