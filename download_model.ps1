$ModelDir = Join-Path $PSScriptRoot "model"
$ModelFile = Join-Path $ModelDir "tiny-aya-earth-q4_k_m.gguf"
$ModelUrl = "https://huggingface.co/CohereLabs/tiny-aya-earth-GGUF/resolve/main/tiny-aya-earth-q4_k_m.gguf"

if (!(Test-Path $ModelDir)) { New-Item -ItemType Directory -Path $ModelDir -Force | Out-Null }

if (Test-Path $ModelFile) {
    Write-Output "model already present at $ModelFile — skipping download"
    exit 0
}

Write-Output "downloading $ModelUrl → $ModelFile (~2.14 GB)..."
$ProgressPreference = 'Continue'
$wc = New-Object System.Net.WebClient
try {
    $wc.DownloadFile($ModelUrl, "$ModelFile.partial")
    Move-Item "$ModelFile.partial" $ModelFile -Force
    Write-Output "done: $ModelFile"
} catch {
    Write-Error "download failed: $_"
    exit 1
}
