const fs=require('node:fs'),p=require('node:path');
const name='batch_'+String(process.argv[2]).padStart(2,'0'),batch=JSON.parse(fs.readFileSync(p.join(__dirname,name+'.json'),'utf8'));const indices=process.argv.slice(3).map(Number);
const lines=[];for(const i of indices){const s=batch[i-1];const raw=JSON.parse(fs.readFileSync('D:/skillsgen-industry_track/research/datasets/evomind/matched_066/private/conversations/'+s.session_id+'.json','utf8'));
lines.push('### '+i+' '+s.session_id);for(const r of raw.user_requests){let text=r.content;const at=text.lastIndexOf('用户原始问题:');if(at>=0)text=text.slice(at+'用户原始问题:'.length);lines.push(r.group_id+': '+text.replace(/\n/g,' ⏎ '));}}
fs.writeFileSync(p.join(__dirname,'expanded_'+process.argv[2]+'_'+indices.join('-')+'.txt'),lines.join('\n'));
