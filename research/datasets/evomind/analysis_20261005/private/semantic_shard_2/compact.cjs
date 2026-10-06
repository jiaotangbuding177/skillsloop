const fs=require('node:fs'),p=require('node:path');
for(let i=1;i<=9;i++){
const name='batch_'+String(i).padStart(2,'0');const batch=JSON.parse(fs.readFileSync(p.join(__dirname,name+'.json'),'utf8'));
const out=batch.map((s,n)=>{let seen=new Set();const rows=s.requests.filter(r=>{if(seen.has(r.text))return false;seen.add(r.text);return true;}).map(r=>r.u+(r.cut?' [CUT]':'')+': '+r.text.replace(/\n/g,' ⏎ '));return String(n+1)+'. '+s.session_id+' | '+rows.join(' || ')}).join('\n');
fs.writeFileSync(p.join(__dirname,name+'.compact.txt'),out);
}
