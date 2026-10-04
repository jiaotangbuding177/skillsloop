# Windows-side supervisor for experiment 268 telecom collection (target 70).
# v2: completion count comes from a WSL-side helper script (no inline escaping).
$ErrorActionPreference = "SilentlyContinue"
$logFile = "D:\skillloop\research\experiments\268_tau2_telecom_autoskill\reports\supervisor_268.log"
$target = 70
$resultJson = "runs/collect/evolution.json"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
}

function Get-Completed {
    $out = wsl.exe -d Ubuntu -- bash /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill/scripts/completed_count.sh $resultJson
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

Log "supervisor v2 started (target=$target)"
while ($true) {
    Start-Sleep -Seconds 120
    $done = Get-Completed
    if ($done -ge $target) {
        Log "collect complete ($done/$target) - supervisor exiting"
        break
    }
    if (Loop-Alive) {
        Log "loop alive, completed $done/$target"
        continue
    }
    Log "loop missing (completed $done/$target) - relaunching"
    wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill && setsid nohup bash scripts/run_collect_loop.sh > /var/tmp/skillsloop268_collect_loop.log 2>&1 < /dev/null & sleep 2; echo relaunched" | Out-Null
}
