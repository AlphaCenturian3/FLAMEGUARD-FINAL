# Minimal static file server for local frontend work on Windows without Python.
# Serves the repository root so frontend/ can read contracts/examples/.
#
#   powershell -ExecutionPolicy Bypass -File frontend/tools/serve.ps1 [-Port 8765]
#   then open http://localhost:8765/frontend/index.html?source=fixtures
#
# On macOS/Linux use:  python3 -m http.server 8765   (from the repository root)

param([int]$Port = 8765)

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$types = @{
  ".html" = "text/html; charset=utf-8"; ".js" = "text/javascript; charset=utf-8"
  ".css" = "text/css; charset=utf-8"; ".json" = "application/json; charset=utf-8"
  ".svg" = "image/svg+xml"; ".png" = "image/png"; ".ico" = "image/x-icon"; ".md" = "text/plain; charset=utf-8"
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Host "Serving $root at http://localhost:$Port/  (Ctrl+C to stop)"

try {
  while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $res = $ctx.Response
    try {
      $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart("/")
      if ($rel -eq "") { $rel = "frontend/index.html" }
      $full = [IO.Path]::GetFullPath((Join-Path $root $rel))
      if (-not $full.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        $res.StatusCode = 403
      } elseif (Test-Path $full -PathType Container) {
        $full = Join-Path $full "index.html"
      }
      if ($res.StatusCode -ne 403 -and (Test-Path $full -PathType Leaf)) {
        $bytes = [IO.File]::ReadAllBytes($full)
        $ext = [IO.Path]::GetExtension($full).ToLower()
        $res.ContentType = if ($types.ContainsKey($ext)) { $types[$ext] } else { "application/octet-stream" }
        $res.Headers.Add("Cache-Control", "no-store")
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
      } elseif ($res.StatusCode -ne 403) {
        $res.StatusCode = 404
      }
    } catch {
      $res.StatusCode = 500
    } finally {
      $res.Close()
    }
  }
} finally {
  $listener.Stop()
}
