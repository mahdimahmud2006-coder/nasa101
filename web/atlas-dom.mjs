export const atlasNode=key=>document.getElementById('at-'+key);
export const atlasElement=(tag,text='')=>{const e=document.createElement(tag);e.textContent=text;return e;};
const optionContents=new WeakMap();
export function atlasOptions(target,rows,current){
  const contents=JSON.stringify(rows);
  if(optionContents.get(target)!==contents){
    target.replaceChildren(...rows.map(([k,v])=>{const a=atlasElement('option',v);a.value=k;return a;}));
    optionContents.set(target,contents);
  }
  target.value=String(current);
}
