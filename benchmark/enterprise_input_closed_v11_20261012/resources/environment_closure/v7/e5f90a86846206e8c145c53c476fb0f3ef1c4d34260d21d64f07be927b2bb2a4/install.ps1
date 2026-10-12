$ErrorActionPreference = "Stop"
$Python = if ($args.Count -ge 1) { $args[0] } else { "python" }
& $Python -m pip install -r "$PSScriptRoot\requirements.txt"
& $Python -m paperconan --version
Write-Output "evomind-paper-scan dependencies installed."
