// Local, deterministic structure audit. Does not transmit or print conversation text.
const fs = require('node:fs');
const path = require('node:path');
const root = 'D:/skillsgen-industry_track';
const mainPath = root + '/research/datasets/evomind/matched_066/private/evomind_conversations.json';
const annotationsPath = root + '/research/datasets/evomind/accepted_071/private/accepted_annotations.json';
const data = JSON.parse(fs.readFileSync(mainPath, 'utf8'));
const annotations = JSON.parse(fs.readFileSync(annotationsPath, 'utf8'));
const count = (obj, key, n=1) => obj[key] = (obj[key] || 0) + n;
const stats = {sources:{conversations:mainPath,annotations:annotationsPath}, conversations:Object.keys(data).length,sessionKeys:{},groupFields:{user:{},assistant:{}},roles:{},groupCounts:{},originalCounts:{},annotation:{sessions:Object.keys(annotations.labels).length,items:0,roles:{},decisions:{},basis:{},invalidTargets:0,invalidGroups:0}, rawPayload:{nonNullByRole:{},keys:{},filesGroupsByRole:{},fileItemsByRole:{},fileKeys:{},structuredSkillFields:[]}, timestamp:{userDatedGroups:0,assistantDatedGroups:0,userOccurrenceCounts:0,assistantOccurrenceCounts:0},sourceOrder:{}, otherArrayLengths:{},uniqueOwners:0};
const owners = new Set(); const rpPaths = new Set(); const seenFileIdentifiers = new Set();
const fileReferences=[];const artifactSignals=[];const skillPathSignals=[];
stats.files={sessions:{user:0,assistant:0},groups:{user:0,assistant:0},occurrences:{user:0,assistant:0},fileMetadataEntries:{user:0,assistant:0},uniquePathOrNameByRole:{user:0,assistant:0}};
stats.toolActivity={occurrencesByRole:{},groupsByRole:{},sessions:0,names:{},fieldCounts:{},states:{},withToolCallId:0,withStartedAt:0,skillPathGroupCounts:{}};
stats.artifactText={aiGroupsWithFileExtension:0,aiGroupsWithLocationAndFileExtension:0,sessionsWithLocation:0,locationReferences:0};
stats.platformPrefixes={};stats.finalOverlay={baseEdges:0,finalEdges:0,changedSessions:0,usersWithReplies:0,usersWithoutReplies:0,aiWithUsers:0,aiWithoutUsers:0,multiUserAssistantGroups:0,baseMethods:{}};
const prefixPatterns={persona:/^【个人助手设定】/, timestamp:/^\[[A-Z][a-z]{2} \d{4}-\d{2}-\d{2} \d{2}:\d{2} GMT\+8\]/,skillWrapper:/^请使用技能「[^」]+」协助当前任务。/,chineseReply:/^请使用中文回复，除非用户明确使用其他语言。/,knowledgeFile:/^以下内容来自用户当前选中的知识库文件/,knowledgeGraph:/^以下内容来自用户当前选择的知识图谱节点/,promptGuard:/^\[PromptGuard\]/,runtimeContext:/^\[OpenClaw runtime context\]/};
const inputFileIds=new Set(),outputFileIds=new Set(),toolSessions=new Set(),artifactSessions=new Set();
const extension=/\.(?:docx?|pdf|pptx?|xlsx?|csv|txt|md|html|png|jpe?g|zip|py|json|m4a|mp3|mp4|wav)(?:$|[?#\s)])/i;
for (const [sid,s] of Object.entries(data)) {
  owners.add(s.owner_id);
  for(const k of Object.keys(s)) count(stats.sessionKeys,k);
  count(stats.sourceOrder,s.source_order_diagnostics?.status || 'NO_STATUS');
  for(const [k,v] of Object.entries(s.original_counts || {})) count(stats.originalCounts,k,Number(v)||0);
  for(const [k,v] of Object.entries(s)) if(Array.isArray(v)&&!['user_requests','assistant_contents','associations'].includes(k)) count(stats.otherArrayLengths,k,v.length);
  for(const [role,groups] of [['user',s.user_requests || []],['assistant',s.assistant_contents || []]]) {
    let sessionHasFiles=false;
    count(stats.groupCounts,role,groups.length);
    for(const g of groups) {
      for(const k of Object.keys(g)) count(stats.groupFields[role],k);
      if(role==='user')for(const [k,re]of Object.entries(prefixPatterns))if(re.test(g.content||''))count(stats.platformPrefixes,k);
      let dated = false, files=[], groupHasTool=false;
      for(const o of g.occurrences || []) {
        count(stats.roles,o.role);
        if(o.user_created_at || (typeof o.raw_record?.createdAt==='string')) dated=true;
        count(stats.timestamp,role+'OccurrenceCounts');
        const rp = o.raw_record?.rawPayload;
        if(rp != null) {
          count(stats.rawPayload.nonNullByRole,role);
          for(const k of Object.keys(rp)) {count(stats.rawPayload.keys,k);if(/skill/i.test(k))rpPaths.add('rawPayload.'+k);}
          if(Array.isArray(rp.files)&&rp.files.length) {
            files.push(...rp.files);count(stats.files.occurrences,role);count(stats.files.fileMetadataEntries,role,rp.files.length);
            for(const f of rp.files)fileReferences.push({session_id:sid,owner_id:s.owner_id,role,group_id:g.group_id,message_id:o.id,source_line:o.source_line,file:f});
          }
          if(rp.toolActivity) {
            groupHasTool=true;toolSessions.add(sid);count(stats.toolActivity.occurrencesByRole,role);
            for(const t of Array.isArray(rp.toolActivity)?rp.toolActivity:[rp.toolActivity]) {
              for(const k of Object.keys(t))count(stats.toolActivity.fieldCounts,k);
              count(stats.toolActivity.names,t.name||'UNKNOWN');count(stats.toolActivity.states,t.status||'UNKNOWN');
              if(t.toolCallId)stats.toolActivity.withToolCallId++;if(t.startedAt)stats.toolActivity.withStartedAt++;
            }
          }
        }
      }
      if(dated) count(stats.timestamp,role+'DatedGroups');
      if(files.length) {
        sessionHasFiles=true;count(stats.files.groups,role);
        count(stats.rawPayload.filesGroupsByRole,role);
        count(stats.rawPayload.fileItemsByRole,role,files.length);
        for(const f of files) {if(typeof f==='object'&&f)for(const k of Object.keys(f))count(stats.rawPayload.fileKeys,k);seenFileIdentifiers.add(JSON.stringify(f));(role==='user'?inputFileIds:outputFileIds).add(f.path||f.name||JSON.stringify(f));}
      }
      if(groupHasTool)count(stats.toolActivity.groupsByRole,role);
      const skillPaths=[...new Set((g.content||'').match(/\/(?:[^\s`"'<>]*\/)?skills\/[^\s`"'<>]+/g)||[])];
      if(skillPaths.length){count(stats.toolActivity.skillPathGroupCounts,role);skillPathSignals.push({session_id:sid,role,group_id:g.group_id,paths:skillPaths});}
      if(role==='assistant'&&extension.test(g.content||'')) {
        stats.artifactText.aiGroupsWithFileExtension++;
        const locations=[];
        for(const m of (g.content||'').matchAll(/\[[^\]]*\]\(([^)]+)\)/g))if(extension.test(m[1]))locations.push(m[1]);
        for(const m of (g.content||'').matchAll(/(?:sandbox:|\/(?:root|mnt|tmp|app|workspace|data)\/|https?:\/\/)[^\s`"'<>]+/g))if(extension.test(m[0]))locations.push(m[0].replace(/[。，；,;]+$/g,''));
        const unique=[...new Set(locations)];if(unique.length){stats.artifactText.aiGroupsWithLocationAndFileExtension++;stats.artifactText.locationReferences+=unique.length;artifactSessions.add(sid);artifactSignals.push({session_id:sid,group_id:g.group_id,message_ids:(g.occurrences||[]).map(o=>o.id),locations:unique,kind:'text_reference_only_not_existence_or_delivery_proof'});}
      }
    }
    if(sessionHasFiles)count(stats.files.sessions,role);
  }
  const ug = new Set((s.user_requests || []).map(g=>g.group_id));
  const ag = new Set((s.assistant_contents || []).map(g=>g.group_id));
  const baseEdges=new Set();for(const link of s.associations||[]){count(stats.finalOverlay.baseMethods,link.method||'UNKNOWN');for(const uid of link.user_group_ids||[])baseEdges.add(uid+'|'+link.assistant_group_id);}
  const finalEdges=new Set(baseEdges);const labels=annotations.labels[sid]||{};
  // Labels override all incident links of that labeled node, then explicit links are inserted.
  for(const [key,label]of Object.entries(labels)){const[role,gid]=key.split(':');for(const edge of [...finalEdges]){const[u,a]=edge.split('|');if((role==='user'?u:a)===gid)finalEdges.delete(edge);}}
  for(const [key,label]of Object.entries(labels)){const[role,gid]=key.split(':');if(label.decision==='matched')for(const target of label.targets||[])finalEdges.add(role==='user'?gid+'|'+target:target+'|'+gid);}
  stats.finalOverlay.baseEdges+=baseEdges.size;stats.finalOverlay.finalEdges+=finalEdges.size;
  if(baseEdges.size!==finalEdges.size||[...baseEdges].some(e=>!finalEdges.has(e)))stats.finalOverlay.changedSessions++;
  const touchedUsers=new Set(),touchedAi=new Map();for(const edge of finalEdges){const[u,a]=edge.split('|');touchedUsers.add(u);touchedAi.set(a,(touchedAi.get(a)||0)+1);}
  stats.finalOverlay.usersWithReplies+=touchedUsers.size;stats.finalOverlay.usersWithoutReplies+=ug.size-touchedUsers.size;stats.finalOverlay.aiWithUsers+=touchedAi.size;stats.finalOverlay.aiWithoutUsers+=ag.size-touchedAi.size;stats.finalOverlay.multiUserAssistantGroups+=[...touchedAi.values()].filter(n=>n>1).length;
  for(const [key,label] of Object.entries(annotations.labels[sid] || {})) {
    stats.annotation.items++;const [role,gid]=key.split(':'); count(stats.annotation.roles,role);count(stats.annotation.decisions,label.decision);count(stats.annotation.basis,label.basis);
    if(!(role==='user'?ug:ag).has(gid))stats.annotation.invalidGroups++;
    for(const target of label.targets || [])if(!(role==='user'?ag:ug).has(target))stats.annotation.invalidTargets++;
  }
}
stats.uniqueOwners=owners.size;stats.rawPayload.structuredSkillFields=[...rpPaths];stats.rawPayload.uniqueFileMetadataObjects=seenFileIdentifiers.size;
stats.files.uniquePathOrNameByRole.user=inputFileIds.size;stats.files.uniquePathOrNameByRole.assistant=outputFileIds.size;stats.toolActivity.sessions=toolSessions.size;stats.artifactText.sessionsWithLocation=artifactSessions.size;
fs.mkdirSync(__dirname,{recursive:true});fs.writeFileSync(path.join(__dirname,'inventory_stats.json'),JSON.stringify(stats,null,2));
fs.mkdirSync(path.join(__dirname,'private'),{recursive:true});
fs.writeFileSync(path.join(__dirname,'private/file_metadata_references.json'),JSON.stringify(fileReferences,null,2));
fs.writeFileSync(path.join(__dirname,'private/assistant_artifact_text_references.json'),JSON.stringify(artifactSignals,null,2));
fs.writeFileSync(path.join(__dirname,'private/skill_text_path_references.json'),JSON.stringify(skillPathSignals,null,2));
console.log(JSON.stringify(stats,null,2));
