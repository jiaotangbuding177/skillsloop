param([string]$Workspace = 'D:\skillloop')
$ErrorActionPreference = 'Stop'
$outputRoot = Join-Path $Workspace 'research/monitoring/recreationbench'
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Save-Json($Path, $Value) {
    $serialized = ConvertTo-Json -InputObject $Value -Depth 20
    [System.IO.File]::WriteAllText($Path, $serialized, $utf8)
}
$monitorErrors = @()
$watched = @()
$actors = @()
$experimentRoot = Join-Path $Workspace 'research/experiments'
$collections = @(Get-ChildItem -LiteralPath $experimentRoot -Directory | Where-Object { $_.Name -match '^\d+_rw_.*collection$' } | Sort-Object Name)
foreach ($collection in $collections) {
    $reports = Join-Path $collection.FullName 'reports'
    $admission = Join-Path $collection.FullName 'admission'
    $runs = Join-Path $collection.FullName 'runs'
    $files = @()
    if (Test-Path -LiteralPath $reports) {
        $files += @(Get-ChildItem -LiteralPath $reports -File | Where-Object { $_.Name -match 'status.*\.json$|health.*\.json$' })
        $active = Join-Path $reports 'active'
        if (Test-Path -LiteralPath $active) { $files += @(Get-ChildItem -LiteralPath $active -File -Filter '*.json') }
    }
    if (Test-Path -LiteralPath $admission) { $files += @(Get-ChildItem -LiteralPath $admission -Recurse -File -Filter '*status.json') }
    if (Test-Path -LiteralPath $runs) { $files += @(Get-ChildItem -LiteralPath $runs -Recurse -File -Filter 'scores.json') }
    foreach ($file in @($files | Sort-Object FullName -Unique)) {
        try {
            $data = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
            $watched += [ordered]@{ path=$file.FullName; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash; state=$data.state; final_score=$data.scores.final_score; runtime_accepted=$data.runtime_accepted }
            if ($file.Directory.Name -eq 'active' -and $data.pid -and $data.start_ticks -and $data.boot_id) {
                $actors += [ordered]@{ task=$data.task; round=$data.round; attempt=$data.attempt; pid=$data.pid; start_ticks=$data.start_ticks; boot_id=$data.boot_id; container=$data.container; state=$data.state }
            }
        } catch { $monitorErrors += [ordered]@{path=$file.FullName;error=$_.Exception.Message} }
    }
}
# Metadata-only WSL inspection. Never resumes, terminates or calls an actor/model.
$processChecks = @()
try {
    $actorJson = ConvertTo-Json -InputObject @($actors) -Depth 8 -Compress
    $probeInfo = New-Object System.Diagnostics.ProcessStartInfo
    $probeInfo.FileName = 'wsl.exe'
    $probeInfo.Arguments = '--exec python3 /mnt/d/skillloop/research/monitoring/recreationbench/probe_processes.py'
    $probeInfo.UseShellExecute = $false
    $probeInfo.CreateNoWindow = $true
    $probeInfo.RedirectStandardInput = $true
    $probeInfo.RedirectStandardOutput = $true
    $probeInfo.RedirectStandardError = $true
    $probeProcess = [System.Diagnostics.Process]::Start($probeInfo)
    $probeProcess.StandardInput.Write($actorJson)
    $probeProcess.StandardInput.Close()
    $probeOutputTask = $probeProcess.StandardOutput.ReadToEndAsync()
    $probeErrorTask = $probeProcess.StandardError.ReadToEndAsync()
    if (-not $probeProcess.WaitForExit(90000)) { $probeProcess.Kill(); throw 'WSL metadata probe exceeded 90 seconds' }
    if ($probeProcess.ExitCode -ne 0) { throw 'WSL process/container probe failed' }
    $probeOutput = $probeOutputTask.Result
    $processChecks = @($probeOutput | ConvertFrom-Json | ForEach-Object { $_ })
} catch { $monitorErrors += [ordered]@{path='WSL metadata probe';error=$_.Exception.Message} }
$state = [ordered]@{ collections=@($collections.Name); watched_files=$watched; actors=$actors; process_checks=$processChecks; errors=$monitorErrors }
$stateText = ConvertTo-Json -InputObject $state -Depth 20 -Compress
$stateHash = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($utf8.GetBytes($stateText))).Replace('-','').ToLowerInvariant()
$previousPath = Join-Path $outputRoot 'latest.json'
$previous = if (Test-Path -LiteralPath $previousPath) { Get-Content -LiteralPath $previousPath -Raw | ConvertFrom-Json } else { $null }
$changed = $null -ne $previous -and $previous.state_sha256 -ne $stateHash
$now = Get-Date
$snapshot = [ordered]@{ checked_at=$now.ToString('o'); state_sha256=$stateHash; changed_since_previous=$changed; baseline_run=($null -eq $previous); scope='read-only local progress; no model, scoring, restart or protocol changes'; state=$state }
Save-Json (Join-Path $outputRoot ('snapshot_' + $now.ToString('yyyyMMdd_HHmmss') + '.json')) $snapshot
Save-Json $previousPath $snapshot
if ($changed -or $monitorErrors.Count -gt 0) {
    $event = [ordered]@{checked_at=$snapshot.checked_at;state_sha256=$stateHash;changed=$changed;errors=$monitorErrors;latest=$previousPath}
    [System.IO.File]::AppendAllText((Join-Path $outputRoot 'changes.jsonl'), ((ConvertTo-Json -InputObject $event -Depth 8 -Compress) + [Environment]::NewLine), $utf8)
}
[pscustomobject]@{checked_at=$snapshot.checked_at;changed=$changed;watched_files=$watched.Count;actors=$actors.Count;probe_errors=$monitorErrors.Count;latest=$previousPath} | ConvertTo-Json -Compress
if ($monitorErrors.Count -gt 0) { exit 1 }
