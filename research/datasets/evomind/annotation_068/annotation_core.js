(function(root){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  const key=(role,id)=>role+':'+id;
  const nodes=(s,role)=>role==='user'?s.users:s.assistants;
  function validateLabel(s,role,id,label){
    if(!['user','assistant'].includes(role)||!nodes(s,role).some(n=>n.id===id))throw Error('标注对象不属于本会话');
    if(!['matched','none','uncertain'].includes(label.decision))throw Error('未知标注状态');
    if(!Array.isArray(label.targets)||new Set(label.targets).size!==label.targets.length)throw Error('候选编号重复或格式错误');
    const valid=new Set(nodes(s,role==='user'?'assistant':'user').map(n=>n.id));
    if(label.targets.some(x=>!valid.has(x)))throw Error('匹配目标不属于本会话');
    if(label.decision==='matched'&&!label.targets.length)throw Error('请至少选择一条对应内容，或选择“无匹配”');
    if(label.decision!=='matched'&&label.targets.length)throw Error('无匹配／暂不能判断不能同时勾选匹配');
    if(typeof label.note!=='string'||label.note.length>10000)throw Error('备注格式不正确或过长');
  }
  function validateSession(s,labels){
    for(const [k,l] of Object.entries(labels||{})){
      const at=k.indexOf(':'),role=k.slice(0,at),id=k.slice(at+1);validateLabel(s,role,id,l);
      if(l.decision==='uncertain')continue;
      for(const other of nodes(s,role==='user'?'assistant':'user')){
        const opposite=labels[key(other.role,other.id)];if(!opposite||opposite.decision==='uncertain')continue;
        if(l.targets.includes(other.id)!==opposite.targets.includes(id))throw Error('与另一侧的人工标注冲突。请先撤销或修改另一侧标注，再确认本项。');
      }
    }
  }
  function empty(fingerprint){return {schema:'evomind-human-links-v1',dataset:fingerprint,labels:{},drafts:{},history:[]};}
  function apply(state,s,role,id,label){
    validateLabel(s,role,id,label);const copy=clone(state.labels[s.id]||{});copy[key(role,id)]=clone(label);validateSession(s,copy);
    return copy;
  }
  function validateImport(doc,data){
    if(!doc||doc.schema!=='evomind-human-links-v1'||doc.dataset!==data.fingerprint)throw Error('文件版本或来源数据指纹不一致，未导入');
    if(!doc.labels||typeof doc.labels!=='object'||Array.isArray(doc.labels))throw Error('标注文件结构不正确');
    const sessions=new Map(data.sessions.map(s=>[s.id,s]));
    for(const [sid,labels] of Object.entries(doc.labels)){if(!sessions.has(sid))throw Error('导入包含当前505条以外的会话');validateSession(sessions.get(sid),labels);}
    for(const [sid,drafts] of Object.entries(doc.drafts||{})){
      if(!sessions.has(sid))throw Error('草稿包含当前范围外的会话');
      for(const [k,l] of Object.entries(drafts)){const at=k.indexOf(':'),copy=clone(l);if(copy.decision==='matched'&&Array.isArray(copy.targets)&&copy.targets.length===0)copy.decision='uncertain';validateLabel(sessions.get(sid),k.slice(0,at),k.slice(at+1),copy);}
    }
    return doc;
  }
  function equivalent(a,b){return a.decision===b.decision&&a.note===b.note&&JSON.stringify([...a.targets].sort())===JSON.stringify([...b.targets].sort());}
  function merge(state,doc,data){
    validateImport(doc,data);const result=clone(state);
    for(const [sid,labels] of Object.entries(doc.labels)){
      const dest=result.labels[sid]||(result.labels[sid]={});
      for(const [k,l] of Object.entries(labels)){if(dest[k]&&!equivalent(dest[k],l))throw Error('导入与本地已有标注不同：'+sid+'。本次未覆盖任何本地标注。');dest[k]=clone(l);}
      validateSession(data.sessions.find(s=>s.id===sid),dest);
    }
    for(const [sid,drafts] of Object.entries(doc.drafts||{})){const dest=result.drafts[sid]||(result.drafts[sid]={});for(const [k,l] of Object.entries(drafts)){if(dest[k]&&!equivalent(dest[k],l))throw Error('导入草稿与本地草稿不同，未覆盖任何标注');dest[k]=clone(l);}}
    const history=[...(result.history||[]),...(Array.isArray(doc.history)?doc.history:[])];result.history=[...new Map(history.map(x=>[JSON.stringify(x),x])).values()];
    return result;
  }
  function progress(s,state){
    let reviewed=0,resolved=0;for(const t of s.issues){const l=(state.labels[s.id]||{})[key(t.role,t.id)];if(l){reviewed++;if(l.decision!=='uncertain')resolved++;}}
    return {total:s.issues.length,reviewed,resolved,done:resolved===s.issues.length};
  }
  const api={clone,key,nodes,empty,validateLabel,validateSession,apply,validateImport,merge,progress};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AnnotationCore=api;
})(typeof globalThis!=='undefined'?globalThis:this);
