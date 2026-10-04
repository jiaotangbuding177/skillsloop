# Windows-side supervisor for experiment 267 airline collection.
# Survives WSL restarts; relaunches the in-WSL resilient collect loop whenever
# it is missing and the collection is not yet complete.
$ErrorActionPreference = "SilentlyContinue"
$root = "D:\skillloop\research\experiments\267_tau2_airline_autoskill"
$logFile = "D:\skillloop\research\experiments\267_tau2_airline_autoskill\reports\supervisor_267.log"
$target = 26
$resultJson = "runs/collect/evolution.json"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
}

function Get-Completed {
    $out = wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill && if [ -f $resultJson ]; then ./runtime_py/bin/python -c 'import json;d=json.load(open(\"$resultJson\"));print(len([s for s in d.get(\"simulations\",[]) if (s.get(\"reward_info\") or {}).get(\"reward\") is not None]))' 2>/dev/null || echo 0; else echo 0; fi"
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n
}

function Loop-Alive {
    $out = wsl.exe -d Ubuntu -- bash -c "pgrep -fc 'run_collect_loo[p]' || true"
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n -ge 1
}

Log "supervisor started (target=$target)"
while ($true) {
    Start-Sleep -Seconds 90
    $done = Get-Completed
    if ($done -ge $target) {
        Log "collection complete ($done/$target) - supervisor exiting"
        break
    }
    if (Loop-Alive) {
        Log "loop alive, completed $done/$target"
        continue
    }
    Log "loop missing (completed $done/$target) - relaunching"
    wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill && setsid nohup bash scripts/run_collect_loop.sh > /var/tmp/skillsloop267_collect_loop.log 2>&1 < /dev/null & sleep 2; echo relaunched" | Out-Null
}
