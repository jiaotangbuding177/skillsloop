# Windows-side supervisor for the 268 telecom learning chain (v2: file-existence check).
$ErrorActionPreference = "SilentlyContinue"
$logFile = "D:\skillloop\research\experiments\268_tau2_telecom_autoskill\reports\supervisor_268_learn.log"
$manifest = "/mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill/frozen_skills_manifest.json"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
}

function Learn-Done {
    wsl.exe -d Ubuntu -- test -f $manifest | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Chain-Alive {
    $out = wsl.exe -d Ubuntu -- bash -c "pgrep -fc 'run_learn_chai[n]|autoskill_build_trajector[y]' || true"
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n -ge 1
}

Log "268 learn supervisor v2 started"
while ($true) {
    Start-Sleep -Seconds 150
    if (Learn-Done) {
        Log "learning chain done (manifest present) - supervisor exiting"
        break
    }
    if (Chain-Alive) {
        Log "chain alive"
        continue
    }
    Log "chain missing and not frozen - relaunching learn chain"
    wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill && setsid nohup bash scripts/run_learn_chain.sh > /var/tmp/skillsloop268_learn_chain.log 2>&1 < /dev/null & sleep 2; echo relaunched" | Out-Null
}
