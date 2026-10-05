"""Pinned Windows process ownership fix, using OpenClaw's own Job Object relay.

The stock child adapter ignores ownProcessTree on Windows. The supervisor then
correctly rejects its missing extinction receipt, even after successful exec.
This routes owned, noninteractive commands through the bundled Windows Job
anchor. No cleanup checks or error results are suppressed.
"""
import hashlib
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
NAME='child-hDIQtCC4.mjs'
ORIGINAL='86bb08df3cfb80f79017076946e0fbf451979cfbc4a08dd980058365484c1e1f'
MARKER='// SkillsLoop Windows owned-process adapter (OpenClaw 2026.9.5)'
NEEDLE='\t\tconst stdinMode = params.stdinMode ?? (params.input !== void 0 ? "pipe-closed" : "inherit");'
INSERT=r'''
        // SkillsLoop Windows owned-process adapter (OpenClaw 2026.9.5)
        if (process.platform === "win32" && params.ownProcessTree === true && params.ownedWorker === void 0) {
            if (params.input !== void 0 || params.secretInput !== void 0 || params.stdinMode === "pipe-open")
                throw new Error("Owned Windows exec supports noninteractive commands only");
            const launch = {
                command: preparedSpawn.command,
                args: preparedSpawn.args,
                argv0: preparedSpawn.argv0,
                windowsVerbatimArguments: invocation.windowsVerbatimArguments === true
            };
            // Encode data before crossing cmd.exe. Model-authored argv never becomes shell syntax here.
            const code = "const p=" + JSON.stringify(launch) + ";const r=require('node:child_process').spawnSync(p.command,p.args,{stdio:'inherit',windowsHide:true,argv0:p.argv0,windowsVerbatimArguments:p.windowsVerbatimArguments});if(r.error){process.stderr.write(String(r.error));process.exit(1)}process.exit(r.status??1);";
            const encoded = Buffer.from(code, "utf8").toString("base64");
            const shellCommand = `"${process.execPath}" -e "eval(Buffer.from('${encoded}','base64').toString('utf8'))"`;
            return await createServiceChildRelayAdapter({
                assertCurrent: params.assertCurrent, beforeSpawn: params.beforeSpawn,
                command: process.execPath, args: [], windowsShellCommand: shellCommand,
                cwd: params.cwd, env: preparedSpawn.env, stdinMode: "pipe-closed",
                oomScoreWrapperSelected: false, abortSignal: params.abortSignal,
                onSpawnCleanup: params.onSpawnCleanup, stderrDestination: params.stderrDestination
            });
        }
'''
CANCEL='if (state === "active") loseIdentity(toErrorObject(error, "service child cancellation failed").message);'
CANCEL_FIXED='''if (state === "active") {
                    // A root result may race the Windows anchor's final closing receipt.
                    // EPIPE alone is not success: require receipt + anchor exit, bounded by the cleanup deadline.
                    if (useWindowsJobAnchor && rootResult && extractErrorCode(error) === "EPIPE") beginCleanupDeadline();
                    else loseIdentity(toErrorObject(error, "service child cancellation failed").message);
                }'''

def apply():
    path=ROOT/'.runtime/node_modules/openclaw/dist'/NAME
    content=path.read_text(encoding='utf-8')
    backup=ROOT/'.runtime/patch-backups'/NAME;backup.parent.mkdir(parents=True,exist_ok=True)
    if MARKER not in content:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ORIGINAL:
            raise RuntimeError('Unknown OpenClaw child adapter; do not patch another version')
        shutil.copyfile(path,backup)
    if hashlib.sha256(backup.read_bytes()).hexdigest()!=ORIGINAL:raise RuntimeError('Invalid original backup')
    original=backup.read_text(encoding='utf-8')
    if original.count(NEEDLE)!=1 or original.count(CANCEL)!=1:raise RuntimeError('Patch locations are not unique')
    first=original.replace(NEEDLE,INSERT+'\n'+NEEDLE)
    expected=first.replace(CANCEL,CANCEL_FIXED)
    if content==expected:return 'already applied'
    if content not in (original,first):raise RuntimeError('Unexpected local changes to OpenClaw adapter')
    path.write_text(expected,encoding='utf-8')
    return 'applied Windows Job ownership adapter'

if __name__=='__main__':print(apply())
