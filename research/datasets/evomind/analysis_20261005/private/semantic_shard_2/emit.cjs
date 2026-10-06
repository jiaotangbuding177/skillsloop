// Serialize explicitly reviewed per-row decisions; no text-based classification.
const fs=require('node:fs'),p=require('node:path');const b=String(process.argv[2]).padStart(2,'0');
const input=JSON.parse(fs.readFileSync(p.join(__dirname,'batch_'+b+'.json'),'utf8'));
const reviewed=JSON.parse(fs.readFileSync(p.join(__dirname,'decisions_'+b+'.json'),'utf8'));
if(input.length!==reviewed.length)throw Error('Wrong row count');
const result=input.map((s,i)=>{const[primary,secondary,confidence,evidence_user,reason,review_basis]=reviewed[i];const valid=new Set(s.requests.map(r=>r.u));if(!valid.has(evidence_user))throw Error('Invalid evidence '+i);return{session_id:s.session_id,primary,secondary:secondary?secondary.split(','):[],confidence,evidence_user:[evidence_user],reason,review_basis:review_basis||'digest'};});
fs.writeFileSync(p.join(__dirname,'result_'+b+'.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({batch:b,n:result.length,counts:result.reduce((a,x)=>(a[x.primary]=(a[x.primary]||0)+1,a),{}),low:result.filter(x=>x.confidence==='low').length}));
