# Run the browser test suite in headless Chrome or Edge and fail on any failure.
#
#   powershell -ExecutionPolicy Bypass -File frontend/tools/run-tests.ps1
#
# Starts serve.ps1 on a free port, loads frontend/tests/index.html, and prints
# the results the page writes. Exit code 0 = all tests passed.

param([int]$Port = 8766)

$browsers = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$browser = $browsers | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $browser) { Write-Error "Chrome or Edge not found."; exit 2 }

$server = Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @(
  "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "serve.ps1"), "-Port", $Port
)
try {
  $url = "http://localhost:$Port/frontend/tests/index.html"
  for ($i = 0; $i -lt 40; $i++) {
    try { Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep -Milliseconds 250 }
  }
  $profileDir = Join-Path ([IO.Path]::GetTempPath()) "flameguard-test-profile"
  $dom = & $browser --headless=new --disable-gpu --no-first-run "--user-data-dir=$profileDir" --virtual-time-budget=60000 --dump-dom $url | Out-String
  $pre = [regex]::Match($dom, '<pre id="results">([\s\S]*?)</pre>').Groups[1].Value
  $text = [System.Net.WebUtility]::HtmlDecode($pre)
  Write-Output $text
  $title = [regex]::Match($dom, '<title>([^<]*)</title>').Groups[1].Value
  Write-Output "Result: $title"
  if ($title -like "PASS*") { exit 0 } else { exit 1 }
} finally {
  Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
}
