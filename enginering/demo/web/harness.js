const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let actor=localStorage.getItem('skilldemo-actor')||'alice';
let route=location.pathname==='/skills'?'skills':'chat';
let session=localStorage.getItem(`skilldemo-session-${actor}`)||`${actor}-${crypto.randomUUID().slice(0,8)}`;
let selected=new Set(new URLSearchParams(location.search).getAll('skill'));
let state=null,busy=false;

async function api(path,body){
  const res=await fetch('/api/'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify({actor,...body}):undefined});
  const value=await res.json();if(!res.ok)throw new Error(value.error||`请求失败：${res.status}`);return value;
}
function notice(text){$('notice').textContent=text||'';}
function badge(text,cls=''){return `<span class="tag ${cls}">${esc(text)}</span>`;}
function fileLinks(turn){return (turn.artifacts||[]).map(f=>`<a href="/api/artifact?actor=${encodeURIComponent(actor)}&run=${encodeURIComponent(turn.runId)}&path=${encodeURIComponent(f.path)}" download="${esc(f.path.split('/').pop())}">下载 ${esc(f.path)}</a>`).join(' · ');}
function receipt(turn){
  const rows=turn.skillEvidence?.skills||[];
  return rows.length?`<div class="receipt">技能读取：${rows.map(s=>`${esc(s.id)} v${esc(s.version)} · ${esc(s.status)}`).join('；')}</div>`:'';
}
function renderSkills(){
  const cards=(state.skills||[]).map(s=>`<article class="skill-card"><div class="row">${badge(s.owner.startsWith('org:')?'组织已审核':'个人技能',s.owner.startsWith('org:')?'org':'')}${badge('v'+s.version)}</div><h3>${esc(s.title)}</h3><p>${esc(s.description||'打开技能查看使用范围与步骤。')}</p><p><code>${esc(s.id)}</code></p><div class="row"><button data-action="inspect-skill" data-id="${esc(s.id)}">查看内容</button><button class="primary" data-action="use-skill" data-id="${esc(s.id)}">用这个技能对话</button><a href="/api/skill-package?actor=${encodeURIComponent(actor)}&id=${encodeURIComponent(s.id)}" download="${esc(s.id)}.skill">下载</a></div></article>`).join('');
  const ready=(state.readyCandidates||[]).map(c=>`<article class="skill-card"><div class="row">${badge('待个人采纳','pending')}${badge(c.action)}</div><h3>${esc(c.title)}</h3><p>技能已封装，采纳后加入个人库并可在对话中选用。</p><div class="row"><button data-action="inspect-candidate" data-id="${esc(c.id)}">查看候选</button><button class="primary" data-action="accept" data-id="${esc(c.id)}">纳入个人库</button></div></article>`).join('');
  return `<div class="panel"><h2>我的 Skills</h2><p class="intro muted">这里列出你可使用的个人技能和已审核组织技能。选择一个技能开始新任务，Agent 会读取所选版本；执行记录会保存读取回执和反馈。</p></div>${ready?`<div class="panel"><h2>待采纳 · ${state.readyCandidates.length}</h2><p class="muted">由会话提炼的候选不会自动进入个人库，先查看内容再决定。</p><div class="skill-grid">${ready}</div></div>`:''}<div class="skill-grid">${cards||'<div class="empty">技能库暂时为空。研究台生成候选后，你可以在这里查看并选择采纳。</div>'}</div>`;
}
function renderChat(){
  const turns=(state.turns||[]).filter(t=>t.session===session);
  const sessions=[...new Set((state.turns||[]).map(t=>t.session))];
  selected=new Set([...selected].filter(id=>state.skills.some(s=>s.id===id)));
  const messages=turns.map(t=>`<div class="bubble user"><small>你</small>${esc(t.user)}</div><div class="bubble"><small>Agent · ${esc(t.status)}</small>${esc(t.assistant||t.error||'执行中…')}${fileLinks(t)?`<div>${fileLinks(t)}</div>`:''}${receipt(t)}</div>`).join('')||'<div class="empty">给 Agent 一项具体任务。你可以先从右侧选用 Skills，任务完成后直接在对话中提出修订。</div>';
  const options=state.skills.map(s=>`<label class="skill-option"><input type="checkbox" name="selected-skill" value="${esc(s.id)}" ${selected.has(s.id)?'checked':''}><span><b>${esc(s.title)}</b><br><small class="muted">${esc(s.owner.startsWith('org:')?'组织':'个人')} · v${s.version}</small></span></label>`).join('')||'<p class="muted">技能库暂无可选技能。<a href="/skills">查看候选</a></p>';
  return `<div class="layout"><div class="panel"><div class="row spread"><div><h2>对话</h2><p class="muted">新任务和后续反馈都在同一会话中完成。</p></div><button data-action="new-session">新建任务</button></div><label class="muted" for="session-picker">当前会话</label> <select id="session-picker" class="session-select"><option value="${esc(session)}">${esc(session)}</option>${sessions.filter(s=>s!==session).map(s=>`<option value="${esc(s)}">${esc(s)}</option>`).join('')}</select><div id="messages" class="messages">${messages}</div><form id="chat-form" class="compose"><label for="message" class="muted">给 Agent 的消息</label><textarea id="message" required placeholder="例如：请按选中的技能审阅这份协议，并说明修改理由……"></textarea><div class="row spread"><small class="muted">选用具体版本后，读取回执会显示在回复下方。</small><button class="primary" type="submit">发送</button></div></form></div><div class="panel sidebar-card"><h3>本次选用的 Skills</h3><p class="muted">可以多选。未选技能时，Agent 正常处理任务，新的方法仍可能沉淀为候选。</p><div class="skill-options">${options}</div><p><a href="/skills">管理我的 Skills →</a></p></div></div>`;
}
function render(){
  $('actor').value=actor;$('page-title').textContent=route==='skills'?'我的 Skills':'对话';
  $('mode').textContent=state.mode==='openclaw'?'OpenClaw · 真实模型':'合成回放';
  document.querySelectorAll('[data-route]').forEach(a=>a.classList.toggle('active',a.dataset.route===route));
  $('content').innerHTML=route==='skills'?renderSkills():renderChat();
  if(route==='chat')$('messages').scrollTop=$('messages').scrollHeight;
}
async function refresh(){state=await api('harness/state?actor='+encodeURIComponent(actor));render();}
function showDetail(title,body){$('detail-title').textContent=title;$('detail-content').textContent=body;$('detail').showModal();}
async function act(action,id){
  if(busy)return;
  if(action==='new-session'){session=`${actor}-${crypto.randomUUID().slice(0,8)}`;selected.clear();localStorage.setItem(`skilldemo-session-${actor}`,session);render();return;}
  if(action==='use-skill'){session=`${actor}-${crypto.randomUUID().slice(0,8)}`;selected=new Set([id]);localStorage.setItem(`skilldemo-session-${actor}`,session);location.href='/chat?skill='+encodeURIComponent(id);return;}
  if(action==='inspect-skill'||action==='inspect-candidate'){
    const item=await api(`harness/${action==='inspect-skill'?'skill':'candidate'}?actor=${encodeURIComponent(actor)}&id=${encodeURIComponent(id)}`);
    showDetail(item.title||id,(item.files||[]).map(f=>`# ${f.path}\n\n${f.content}`).join('\n\n')+'\n\n验证记录：'+JSON.stringify(item.validation||'技能库版本',null,2));return;
  }
  if(action==='accept'){
    busy=true;notice('正在纳入个人库…');try{const skill=await api('accept',{id});selected.add(skill.id);await refresh();notice('已加入个人库，可以选用该技能开始对话。');}catch(e){notice(e.message);}finally{busy=false;}return;
  }
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(b)act(b.dataset.action,b.dataset.id).catch(err=>notice(err.message));});
document.addEventListener('change',e=>{if(e.target.name==='selected-skill'){e.target.checked?selected.add(e.target.value):selected.delete(e.target.value);}if(e.target.id==='session-picker'){session=e.target.value;localStorage.setItem(`skilldemo-session-${actor}`,session);render();}});
document.addEventListener('submit',async e=>{
  if(e.target.id!=='chat-form')return;e.preventDefault();if(busy)return;
  const message=$('message').value.trim();if(!message)return;
  busy=true;notice('Agent 正在处理，请等待本次执行记录…');
  try{await api('chat',{session,message,skills:[...selected],requestId:crypto.randomUUID()});await refresh();notice('本次对话已保存。');}
  catch(err){notice(err.message);}finally{busy=false;}
});
$('actor').addEventListener('change',async e=>{actor=e.target.value;localStorage.setItem('skilldemo-actor',actor);session=localStorage.getItem(`skilldemo-session-${actor}`)||`${actor}-${crypto.randomUUID().slice(0,8)}`;selected.clear();try{await refresh();notice('');}catch(err){notice(err.message);}});
$('detail-close').onclick=()=>$('detail').close();
refresh().catch(err=>notice(err.message));
setInterval(()=>{if(!busy&&route==='skills'&&!$('detail').open)refresh().catch(()=>{});},5000);
