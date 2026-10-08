$ErrorActionPreference = 'Stop'
$rwRoot = Split-Path $PSScriptRoot -Parent
$rwRevision = '284341f8fc3d6680dd57ca5414fed92a0fe33b95'
$rwIndex = Invoke-RestMethod -Uri ('https://huggingface.co/api/datasets/Qwen/RecreationBench/revision/' + $rwRevision)
$rwGroups = $rwIndex.siblings | Where-Object {$_.rfilename.StartsWith('web/')} | Group-Object {$_.rfilename.Split('/')[1]} | Sort-Object Count,Name
$rwTask = $rwGroups[0].Name
$rwFiles = @()
foreach ($rwEntry in $rwGroups[0].Group) {
    $rwName = $rwEntry.rfilename
    $rwNameHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($rwName))).ToLowerInvariant()
    $rwPath = Join-Path $rwRoot ('download_staging/' + $rwNameHash)
    [IO.Directory]::CreateDirectory((Split-Path $rwPath -Parent)) | Out-Null
    if (-not (Test-Path -LiteralPath $rwPath)) {
        $rwEncodedName = [Uri]::EscapeDataString($rwName).Replace('%2F','/')
        $rwUrl = 'https://huggingface.co/datasets/Qwen/RecreationBench/resolve/' + $rwRevision + '/' + $rwEncodedName
        for ($rwTry = 1; $rwTry -le 4; $rwTry++) {
            try {
                Invoke-WebRequest -Uri $rwUrl -OutFile ($rwPath + '.partial') -TimeoutSec 120
                Move-Item -LiteralPath ($rwPath + '.partial') -Destination $rwPath
                break
            } catch { if ($rwTry -eq 4) {throw}; Start-Sleep -Seconds 2 }
        }
    }
    $rwFiles += @{path=$rwName;staged_file=$rwNameHash;bytes=(Get-Item -LiteralPath $rwPath).Length;sha256=(Get-FileHash -LiteralPath $rwPath -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$rwReport = @{repo='Qwen/RecreationBench';revision=$rwRevision;split='test';role='infrastructure_canary_excluded_from_reported_test';task_id=$rwTask;selection='minimum file count, lexical tie-break';files=$rwFiles;complete=($rwFiles.Count -eq $rwGroups[0].Count)}
[IO.Directory]::CreateDirectory((Join-Path $rwRoot 'reports')) | Out-Null
[IO.File]::WriteAllText((Join-Path $rwRoot 'reports/dataset_manifest.json'), ($rwReport | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
@{task_id=$rwTask;downloaded_files=$rwFiles.Count} | ConvertTo-Json -Compress
