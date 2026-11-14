# Keyboard, mobile-layout, and "served at /" checks in a real Chrome/Edge,
# driven through the Chrome DevTools Protocol (real key events, real
# device-metrics emulation). Complements the unit tests in frontend/tests/.
#
#   powershell -ExecutionPolicy Bypass -File frontend/tools/browser-check.ps1 [-OutDir shots] [-Headed]
#
# Exit code 0 = every check passed. Screenshots are written to -OutDir.

param(
  [int]$Port = 8771,
  [int]$RootPort = 8772,
  [int]$MountPort = 8773,
  [int]$DebugPort = 9339,
  [string]$OutDir = (Join-Path ([IO.Path]::GetTempPath()) "flameguard-browser-check"),
  [switch]$Headed
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$browser = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $browser) { Write-Error "Chrome or Edge not found."; exit 2 }

$serve = Join-Path $PSScriptRoot "serve.ps1"
$procs = @()
$procs += Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $serve, "-Port", $Port)
$procs += Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $serve, "-Port", $RootPort, "-Root", "frontend")
$procs += Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $serve, "-Port", $MountPort, "-Root", "frontend", "-MountContracts")
$profileDir = Join-Path ([IO.Path]::GetTempPath()) "flameguard-cdp-profile"
$chromeArgs = @("--remote-debugging-port=$DebugPort", "--user-data-dir=$profileDir", "--no-first-run", "--disable-gpu", "about:blank")
if (-not $Headed) { $chromeArgs = @("--headless=new") + $chromeArgs }
$procs += Start-Process $browser -PassThru -ArgumentList $chromeArgs

$results = New-Object System.Collections.ArrayList
function Check([string]$name, [bool]$ok, [string]$detail = "") {
  [void]$results.Add([pscustomobject]@{ ok = $ok; name = $name; detail = $detail })
  $mark = if ($ok) { "ok  " } else { "FAIL" }
  Write-Output ("{0} {1}{2}" -f $mark, $name, $(if ($detail) { "  [$detail]" } else { "" }))
}

try {
  # ---- connect ----
  $target = $null
  for ($i = 0; $i -lt 40 -and -not $target; $i++) {
    try { $target = (Invoke-RestMethod "http://127.0.0.1:$DebugPort/json/list") | Where-Object { $_.type -eq "page" } | Select-Object -First 1 } catch { Start-Sleep -Milliseconds 250 }
  }
  if (-not $target) { throw "Could not reach the browser DevTools endpoint." }
  $ws = New-Object System.Net.WebSockets.ClientWebSocket
  $ws.ConnectAsync([Uri]$target.webSocketDebuggerUrl, [Threading.CancellationToken]::None).Wait()
  $script:msgId = 0

  function Cdp([string]$method, [hashtable]$params = @{}) {
    $script:msgId++
    $json = @{ id = $script:msgId; method = $method; params = $params } | ConvertTo-Json -Depth 10 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $ws.SendAsync((New-Object ArraySegment[byte] -ArgumentList @(, $bytes)), [Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).Wait()
    while ($true) {
      $ms = New-Object IO.MemoryStream
      do {
        $buf = New-Object byte[] 262144
        $r = $ws.ReceiveAsync((New-Object ArraySegment[byte] -ArgumentList @(, $buf)), [Threading.CancellationToken]::None).Result
        $ms.Write($buf, 0, $r.Count)
      } while (-not $r.EndOfMessage)
      $msg = [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json
      if ($msg.id -eq $script:msgId) { return $msg }
    }
  }
  function Js([string]$expr) {
    $r = Cdp "Runtime.evaluate" @{ expression = $expr; returnByValue = $true; awaitPromise = $true }
    if ($r.result.exceptionDetails) { return "JS-ERROR: " + $r.result.exceptionDetails.text }
    return $r.result.result.value
  }
  function WaitFor([string]$expr, [int]$ms = 6000) {
    $t = [Diagnostics.Stopwatch]::StartNew()
    while ($t.ElapsedMilliseconds -lt $ms) { if ((Js "!!($expr)") -eq $true) { return $true }; Start-Sleep -Milliseconds 100 }
    return $false
  }
  function Press([string]$key, [int]$modifiers = 0) {
    $map = @{ Tab = @("Tab", 9, $null); Enter = @("Enter", 13, "`r"); Escape = @("Escape", 27, $null); Space = @("Space", 32, " ") }
    $code, $vk, $text = $map[$key]
    $keyName = if ($key -eq "Space") { " " } else { $key }
    $down = @{ type = $(if ($text) { "keyDown" } else { "rawKeyDown" }); key = $keyName; code = $code; windowsVirtualKeyCode = $vk; nativeVirtualKeyCode = $vk; modifiers = $modifiers }
    if ($text) { $down.text = $text; $down.unmodifiedText = $text }
    Cdp "Input.dispatchKeyEvent" $down | Out-Null
    Cdp "Input.dispatchKeyEvent" @{ type = "keyUp"; key = $keyName; code = $code; windowsVirtualKeyCode = $vk; nativeVirtualKeyCode = $vk; modifiers = $modifiers } | Out-Null
    Start-Sleep -Milliseconds 80
  }
  function Active { Js "(() => { const e = document.activeElement; if (!e || e === document.body) return 'BODY'; const s = getComputedStyle(e); const r = e.getBoundingClientRect(); return [e.tagName, e.getAttribute('href') || e.id || e.dataset.action || e.name || e.type || '', (e.getAttribute('aria-label') || e.textContent || e.value || '').trim().replace(/\s+/g, ' ').slice(0, 40), s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0 ? 'ring' : 'NO-RING', r.width > 0 && r.height > 0 && r.right > 0 && r.left < innerWidth ? 'visible' : 'HIDDEN'].join(' | '); })()" }
  function Go([string]$url) {
    Cdp "Page.navigate" @{ url = $url } | Out-Null
    Start-Sleep -Milliseconds 300
    WaitFor "document.readyState === 'complete' && document.querySelector('#main h1')" | Out-Null
    Start-Sleep -Milliseconds 400
  }
  function Shot([string]$name) {
    $r = Cdp "Page.captureScreenshot" @{ format = "png"; captureBeyondViewport = $true }
    [IO.File]::WriteAllBytes((Join-Path $OutDir "$name.png"), [Convert]::FromBase64String($r.result.data))
  }

  Cdp "Page.enable" | Out-Null
  $base = "http://localhost:$Port/frontend/index.html"

  # ---- desktop keyboard ----
  Cdp "Emulation.setDeviceMetricsOverride" @{ width = 1280; height = 900; deviceScaleFactor = 1; mobile = $false } | Out-Null
  Go "$base`?fixtures=1#/"
  Js "sessionStorage.clear(); document.activeElement && document.activeElement.blur(); window.scrollTo(0,0); true" | Out-Null
  Go "$base`?fixtures=1#/"

  Press Tab
  $a = Active
  Check "Tab 1 focuses the skip link with a visible focus ring" ($a -like "A | #main*ring*visible") $a
  Press Enter
  $a = Active
  $hash = Js "location.hash"
  Check "Skip link moves focus to main without changing the route" (($a -like "MAIN*") -and ($hash -eq "#/")) "$a ; hash=$hash"

  Js "document.querySelector('.skip-link').focus(); true" | Out-Null
  $seen = @(); $noRing = @()
  for ($i = 0; $i -lt 20; $i++) {
    Press Tab
    $a = Active
    if ($a -eq "BODY") { break }   # tabbed past the last focusable element
    $seen += $a
    if ($a -notlike "*| ring |*") { $noRing += $a }
  }
  $order = ($seen | ForEach-Object { ($_ -split " \| ")[1] }) -join ", "
  foreach ($href in @("#/", "#/explorer", "#/compare", "#/rank", "#/interpret", "#/tars", "#/integrations")) {
    Check "Nav link $href reachable by Tab" (($seen | Where-Object { $_ -like "A | $href |*" }).Count -gt 0) ""
  }
  Check "Judge demo button reachable by Tab" (($seen | Where-Object { $_ -like "BUTTON*Judge demo*" }).Count -gt 0) ""
  Check "Every Tab stop shows a visible focus ring" ($noRing.Count -eq 0) ($noRing -join " / ")
  Write-Output "     tab order: $order"

  Js "document.querySelector('#nav a[href=""#/explorer""]').focus(); true" | Out-Null
  Press Enter
  WaitFor "location.hash === '#/explorer' && document.querySelector('.investigation')" | Out-Null
  $a = Active
  Check "Enter on nav link opens Explorer and focuses its heading" ((Js "location.hash") -eq "#/explorer" -and $a -like "H1*Evidence Explorer*") $a

  Js "document.querySelector('input[type=search]').focus(); true" | Out-Null
  Cdp "Input.insertText" @{ text = "zzzz-no-match" } | Out-Null
  $empty = WaitFor "document.querySelector('.results .state-empty')"
  Check "Typing a non-matching search shows the empty state" $empty (Js "document.querySelector('.result-count').textContent")
  Js "const i = document.querySelector('input[type=search]'); i.select(); true" | Out-Null
  Cdp "Input.insertText" @{ text = "fixture" } | Out-Null
  $found = WaitFor "document.querySelectorAll('.results .investigation').length === 1"
  Check "Typing a matching search shows the record" $found (Js "document.querySelector('.result-count').textContent")

  Js "document.querySelector('.compare-toggle input').focus(); true" | Out-Null
  Press Space
  Check "Space toggles the Compare checkbox" ((Js "document.querySelector('.compare-toggle input').checked") -eq $true) ""

  Js "document.querySelector('.nav-demo').focus(); true" | Out-Null
  Press Enter
  $bar = WaitFor "!document.querySelector('.demo-bar').hidden && location.hash === '#/explorer'"
  Check "Enter on Judge demo starts the walkthrough at Discover" $bar (Js "location.hash")
  Js "document.querySelector('.demo-bar [data-action=exit]').focus(); true" | Out-Null
  Press Tab 8   # Shift+Tab
  Press Tab 8
  $a = Active
  Check "Shift+Tab reaches the demo Next button" ($a -like "BUTTON | next*") $a
  Press Enter
  WaitFor "location.hash === '#/compare'" | Out-Null
  $a = Active
  Check "Enter on Next advances to Compare and keeps focus in the demo bar" ((Js "location.hash") -eq "#/compare" -and $a -like "BUTTON | next*") "$a ; hash=$(Js 'location.hash')"
  for ($i = 0; $i -lt 3; $i++) { Press Enter; Start-Sleep -Milliseconds 200 }
  $a = Active
  Check "Keyboard reaches the final Safety Insight step (button becomes Restart)" ($a -like "BUTTON | next | Restart*" -and (Js "location.hash") -eq "#/interpret") $a
  Shot "desktop-demo-insight"
  Press Enter
  WaitFor "location.hash === '#/explorer'" | Out-Null
  Check "Restart returns to Discover" ((Js "location.hash") -eq "#/explorer") ""
  Js "document.querySelector('.demo-bar [data-action=exit]').focus(); true" | Out-Null
  Press Enter
  Check "Exit closes the demo bar" ((Js "document.querySelector('.demo-bar').hidden") -eq $true) ""

  # F8: theme toggle by keyboard
  Js "try { localStorage.removeItem('flameguard.theme') } catch (e) {} ; document.getElementById('theme-button').focus(); true" | Out-Null
  $before = Js "getComputedStyle(document.body).backgroundColor"
  Press Enter
  Start-Sleep -Milliseconds 150
  $after = Js "[document.documentElement.dataset.theme, getComputedStyle(document.body).backgroundColor, document.getElementById('theme-button').getAttribute('aria-pressed')].join('|')"
  Check "Theme button toggles light/dark by keyboard and changes the page colours" ($after -notlike "|*" -and ($after -split "\|")[1] -ne $before) "$before -> $after"
  Shot "desktop-theme-toggled"
  Press Enter
  Js "try { localStorage.removeItem('flameguard.theme') } catch (e) {} ; true" | Out-Null

  # P3: backend comparison in fixture mode, operated by keyboard
  Go "$base`?fixtures=1#/compare"
  WaitFor "document.querySelector('#cmp-quantity')" | Out-Null
  Js "document.querySelector('.compare-controls button[type=submit]').focus(); true" | Out-Null
  Press Enter
  $cmp = WaitFor "/Backend decision/.test(document.querySelector('.compare-body').textContent)"
  $txt = Js "document.querySelector('.compare-body').textContent"
  Check "Compare: Enter requests /api/compare and shows the backend decision with its reasons verbatim, no chart" ($cmp -and $txt -like "*Not comparable*" -and $txt -like "*pressure_kpa not reported for either row*" -and (Js "!!document.querySelector('.compare-body svg')") -eq $false) ""

  # P4: ranking in fixture mode follows backend rank, shows criteria and not-ranked investigations
  Go "$base`?fixtures=1#/rank"
  $rk = WaitFor "document.querySelector('.ranking .rank-item')"
  $txt = Js "document.querySelector('main').textContent"
  Check "Rank: fixture ranking shows criteria weights, criterion inputs and the not-ranked investigation" ($rk -and $txt -like "*FIXTURE criterion A*" -and $txt -like "*fixture-finding-interp-1*" -and $txt -like "*Not ranked for Spacecraft*") ""

  # ---- mobile layout ----
  Cdp "Emulation.setDeviceMetricsOverride" @{ width = 360; height = 780; deviceScaleFactor = 2; mobile = $true } | Out-Null
  Cdp "Emulation.setTouchEmulationEnabled" @{ enabled = $true; maxTouchPoints = 5 } | Out-Null
  foreach ($route in @("#/", "#/explorer", "#/compare", "#/rank", "#/interpret", "#/tars", "#/integrations")) {
    Go "$base`?fixtures=1$route"
    Start-Sleep -Milliseconds 300
    $w = Js "[document.documentElement.scrollWidth, 360, [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > 360.5).slice(0, 4).map(e => e.tagName + '.' + (e.className || '')).join(',')].join('/')"
    $parts = $w -split "/"
    Check "Mobile 360px $route has no horizontal scroll (page width <= 360 px)" ([int]$parts[0] -le 360) "scrollWidth/limit/overflowing=$w"
    $banner = Js "(document.querySelector('.banner-fixture') || {}).textContent || ''"
    Check "Fixture mode $route shows the permanent 'FIXTURE DATA. NOT NASA DATA.' banner" ($banner -like "*FIXTURE DATA. NOT NASA DATA.*") ""
    Shot ("mobile-" + ($route -replace "[#/]", "").Trim() + $(if ($route -eq "#/") { "overview" } else { "" }))
  }
  Go "$base`?fixtures=1#/explorer"
  $hiddenNav = Js "getComputedStyle(document.getElementById('sidebar')).visibility"
  Check "Mobile: closed sidebar is hidden from Tab order" ($hiddenNav -eq "hidden") $hiddenNav
  Js "document.getElementById('menu-button').focus(); true" | Out-Null
  Press Enter
  Start-Sleep -Milliseconds 300
  $open = Js "document.body.classList.contains('nav-open') + '/' + document.getElementById('menu-button').getAttribute('aria-expanded') + '/' + getComputedStyle(document.getElementById('sidebar')).visibility"
  Check "Mobile: Enter on menu opens the sidebar (aria-expanded=true)" ($open -eq "true/true/visible") $open
  Shot "mobile-nav-open"
  Press Escape
  Start-Sleep -Milliseconds 300
  $a = Active
  $closed = Js "document.body.classList.contains('nav-open')"
  Check "Mobile: Escape closes the sidebar and returns focus to the menu button" ($closed -eq $false -and $a -like "BUTTON | menu-button*") $a

  # P2: a FLEX-sized investigation (40 findings, 10 rows) at 360 px. Test page only; test records from tests/fixtures/frontend.
  Go "http://localhost:$Port/frontend/tests/layout.html"
  WaitFor "document.body.dataset.ready === '1'" | Out-Null
  Js "document.querySelectorAll('details.row-group').forEach(d => d.open = true); true" | Out-Null
  Start-Sleep -Milliseconds 200
  $w = Js "[document.documentElement.scrollWidth, innerWidth, document.querySelectorAll('details.row-group').length, document.querySelectorAll('article.finding').length].join('/')"
  $parts = $w -split "/"
  Check "Mobile 360px: 40-finding investigation grouped into 10 rows, no horizontal scroll with every row open" (([int]$parts[0] -le 360) -and $parts[2] -eq "10" -and $parts[3] -eq "40") "scrollWidth/innerWidth/rows/findings=$w"
  Shot "mobile-grouped-40"

  # ---- served at / (as FastAPI StaticFiles(directory='frontend') would) ----
  Cdp "Emulation.setDeviceMetricsOverride" @{ width = 1280; height = 900; deviceScaleFactor = 1; mobile = $false } | Out-Null
  $rootUrl = "http://localhost:$RootPort/"
  Go "$rootUrl#/"
  $assets = Js "[getComputedStyle(document.body).backgroundColor, document.querySelectorAll('#nav a').length].join('/')"
  Check "Served at /: CSS and JS load via relative paths" ($assets -like "*/7") $assets
  $api = WaitFor "document.querySelector('#health .badge') && /API/.test(document.querySelector('#health').textContent) && !/checking/.test(document.querySelector('#health').textContent)"
  Check "Served at /: API mode calls /api/health at the same origin" $api (Js "document.querySelector('#health').textContent")

  # No fixture leak (CP1 F-check): without ?fixtures=1, visiting every route never requests contracts/examples/.
  Go "http://localhost:$MountPort/#/"
  foreach ($route in @("#/explorer", "#/compare", "#/rank", "#/interpret", "#/tars", "#/integrations", "#/")) {
    Js "location.hash = '$route'; true" | Out-Null
    Start-Sleep -Milliseconds 500
  }
  $leak = Js "performance.getEntriesByType('resource').filter(e => e.name.includes('contracts/examples')).map(e => e.name).join(' ')"
  $apiCalls = Js "performance.getEntriesByType('resource').filter(e => e.name.includes('/api/')).length"
  Check "No fixture leak: API mode on every route makes no request to contracts/examples/ (while /contracts/examples is reachable)" ($leak -eq "" -and [int]$apiCalls -gt 0) "leaked=[$leak] apiRequests=$apiCalls"

  Go "$rootUrl`?fixtures=1#/explorer"
  WaitFor "document.querySelector('.results .state')" | Out-Null
  $msg = Js "(document.querySelector('.results .state') || {}).textContent || ''"
  Check "Served at / with ?fixtures=1 and no /contracts/examples mount: explicit error, no data shown" ($msg -like "*Fixture file could not be loaded*" -and $msg -like "*HTTP 404*") $msg
  Shot "served-at-root-fixtures-unmounted"
  Go "http://localhost:$MountPort/?fixtures=1#/explorer"
  $ok = WaitFor "document.querySelectorAll('.results .investigation').length === 1"
  Check "Served at / with /contracts/examples/ mounted: default fixture URL works unchanged" $ok (Js "location.href")
} finally {
  try { if ($ws) { $ws.Dispose() } } catch {}
  foreach ($p in $procs) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
}

$failed = @($results | Where-Object { -not $_.ok }).Count
Write-Output ""
Write-Output ("{0} passed, {1} failed, {2} total. Screenshots: {3}" -f ($results.Count - $failed), $failed, $results.Count, $OutDir)
if ($failed) { exit 1 } else { exit 0 }
