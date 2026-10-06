// No model or network calls: verify actual process-tree settlement and argv fidelity.
import assert from 'node:assert/strict';
import { t as createChildAdapter } from '../.runtime/node_modules/openclaw/dist/child-hDIQtCC4.mjs';
import { getProcessSupervisor } from '../.runtime/node_modules/openclaw/dist/supervisor-BWJG83X0.mjs';
import { o as getShellConfig } from '../.runtime/node_modules/openclaw/dist/shell-utils-CygSnidg.mjs';
const cases=[
 {name:'quoted argv',code:'process.stdout.write(process.argv[1]);',args:['中文 "quote" & percent% $x'],expected:'中文 "quote" & percent% $x',exit:0},
 {name:'nonzero exit',code:'process.exit(7)',args:[],expected:'',exit:7},
 {name:'nested process',code:"require('node:child_process').spawnSync(process.execPath,['-e','process.stdout.write(\"nested\")'],{stdio:'inherit'});",args:[],expected:'nested',exit:0}
];
for (const c of cases) {
 const {adapter,ready}=await createChildAdapter({argv:[process.execPath,'-e',c.code,...c.args],ownProcessTree:true,stdinMode:'pipe-closed',env:process.env,cwd:process.cwd()});
 let out='';adapter.onStdout(s=>out+=s);adapter.onStderr(s=>process.stderr.write(s));
 await ready;const result=await adapter.wait();assert.equal(typeof adapter.waitForExtinction,'function');await adapter.waitForExtinction();
 assert.equal(result.code,c.exit);assert.equal(out,c.expected);
 console.log(JSON.stringify({case:c.name,exitCode:result.code,extinction:'settled'}));adapter.dispose();
}
const supervisor=getProcessSupervisor();
const shell=getShellConfig();
for (let i=0;i<4;i++) {
 const scope='windows-check-'+i;const cleanup=supervisor.acquireScopeCleanup(scope,{processTree:'owned-only'});
 const command=i%2?'Write-Output "shell-ok"':'exit 7';
 const run=await supervisor.spawn({mode:'child',scopeKey:scope,argv:[shell.shell,...shell.args,command],env:process.env,cwd:process.cwd(),stdinMode:'pipe-closed'});
 const result=await run.wait();await cleanup();assert.equal(result.exitCode,i%2?0:7,JSON.stringify(result));
 console.log(JSON.stringify({case:'supervised shell '+i,exitCode:result.exitCode,extinction:'settled'}));
}
