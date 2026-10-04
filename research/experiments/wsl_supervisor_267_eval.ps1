# Windows-side supervisor for the 267 airline paired evaluation (B0+B1, target 80 each).
$ErrorActionPreference = "SilentlyContinue"
$logFile = "D:\skillloop\research\experiments\267_tau2_airline_autoskill\reports\supervisor_267_eval.log"
$target = 80

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
}

function Completed($json) {
    $out = wsl.exe -d Ubuntu -- bash /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/scripts/completed_count.sh $json
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n
}

function Loop-Alive {
    $out = wsl.exe -d Ubuntu -- bash -c "pgrep -fc 'run_eval_loo[p]' || true"
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n -ge 1
}

Log "eval supervisor started (target=$target per group)"
while ($true) {
    Start-Sleep -Seconds 120
    $b0 = Completed "runs/test/no_skill.json"
    $b1 = Completed "runs/test/autoskill_library.json"
    if ($b0 -ge $target -and $b1 -ge $target) {
        Log "eval complete B0=$b0 B1=$b1 - supervisor exiting"
        break
    }
    if (Loop-Alive) {
        Log "eval loop alive, B0=$b0 B1=$b1"
        continue
    }
    Log "eval loop missing (B0=$b0 B1=$b1) - relaunching"
    wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill && setsid nohup bash scripts/run_eval_loop.sh > /var/tmp/skillsloop267_eval_loop.log 2>&1 < /dev/null & sleep 2; echo relaunched" | Out-Null
}
