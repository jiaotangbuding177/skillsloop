# Windows-side supervisor for the 267 airline learning chain (canonicalize -> build -> freeze).
$ErrorActionPreference = "SilentlyContinue"
$logFile = "D:\skillloop\research\experiments\267_tau2_airline_autoskill\reports\supervisor_267_learn.log"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
}

function Learn-Done {
    $out = wsl.exe -d Ubuntu -- bash -c "f=/mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/frozen_skills_manifest.json; if [ -f \$f ] && grep -q 'SKILL.md' /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/autoskill_state/skillbank_trajectory/Users/tau_airline_pool_v1/*/SKILL.md 2>/dev/null; then echo DONE; else echo PENDING; fi"
    return (($out | Select-Object -Last 1) -eq "DONE")
}

function Chain-Alive {
    $out = wsl.exe -d Ubuntu -- bash -c "pgrep -fc 'run_learn_chai[n]|autoskill_build_trajector[y]' || true"
    $n = 0
    [int]::TryParse(($out | Select-Object -Last 1), [ref]$n) | Out-Null
    return $n -ge 1
}

Log "learn-chain supervisor started"
while ($true) {
    Start-Sleep -Seconds 150
    if (Learn-Done) {
        Log "learning chain done (frozen library present) - supervisor exiting"
        break
    }
    if (Chain-Alive) {
        Log "chain alive"
        continue
    }
    Log "chain missing and not frozen - relaunching learn chain"
    wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill && setsid nohup bash scripts/run_learn_chain.sh > /var/tmp/skillsloop267_learn_chain.log 2>&1 < /dev/null & sleep 2; echo relaunched" | Out-Null
}
