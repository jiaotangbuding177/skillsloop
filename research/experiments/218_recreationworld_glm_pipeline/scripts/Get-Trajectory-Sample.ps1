# Fetch one complete official AgentNet episode without downloading its huge image zips.
# This is schema research, not accepted multimodal learning input.
$ErrorActionPreference='Stop'
$rwRoot=Split-Path $PSScriptRoot -Parent
$rwDest=Join-Path $rwRoot 'external/AgentNet'
[IO.Directory]::CreateDirectory($rwDest)|Out-Null
$rwRev='d76ee50a63fad81cfdbe576416757d7c2091ed50'
foreach($rwName in @('README.md','LICENSE.txt')) {
    Invoke-WebRequest -Uri ('https://huggingface.co/datasets/xlangai/AgentNet/resolve/'+$rwRev+'/'+$rwName) -OutFile (Join-Path $rwDest $rwName) -TimeoutSec 90
}
$rwClient=[Net.Http.HttpClient]::new()
$rwClient.Timeout=[TimeSpan]::FromSeconds(90)
$rwResponse=$rwClient.GetAsync(('https://huggingface.co/datasets/xlangai/AgentNet/resolve/'+$rwRev+'/agentnet_ubuntu_5k.jsonl'),[Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
$rwResponse.EnsureSuccessStatusCode()|Out-Null
$rwStream=$rwResponse.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
$rwReader=[IO.StreamReader]::new($rwStream)
try {
    $rwLine=$rwReader.ReadLine()
    $rwItem=$rwLine|ConvertFrom-Json
    if(-not $rwItem.task_id -or -not $rwItem.traj) {throw 'Not a complete trajectory record'}
    [IO.File]::WriteAllText((Join-Path $rwDest 'schema_sample.json'),$rwLine,[Text.UTF8Encoding]::new($false))
    $rwEvidence=@{repo='xlangai/AgentNet';revision=$rwRev;task_id=$rwItem.task_id;steps=$rwItem.traj.Count;record_sha256=(Get-FileHash -LiteralPath (Join-Path $rwDest 'schema_sample.json')).Hash.ToLowerInvariant();images_downloaded=$false;accepted_learning_input=$false;purpose='complete single-record schema inspection; screenshot archives pending';source_type='human demonstrations with synthetic enrichment'}
    [IO.File]::WriteAllText((Join-Path $rwRoot 'reports/external_sample.json'),($rwEvidence|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    @{complete_episode_sample=$true;steps=$rwItem.traj.Count;images_downloaded=$false}|ConvertTo-Json -Compress
} finally {$rwReader.Dispose();$rwResponse.Dispose();$rwClient.Dispose()}
