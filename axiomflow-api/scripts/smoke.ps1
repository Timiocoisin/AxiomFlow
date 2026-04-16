$ErrorActionPreference = "Stop"

$BaseUrl = $env:AXIOMFLOW_API_BASEURL
if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }

$Session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

function PostJson($Path, $Body) {
  return Invoke-RestMethod -Method Post -Uri ($BaseUrl + $Path) -WebSession $Session -ContentType "application/json" -Body ($Body | ConvertTo-Json)
}

Write-Host "BaseUrl: $BaseUrl"

$Email = "test_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "@example.com"
$Password = "TestPassw0rd!"

Write-Host "`n[1] Register: $Email"
try {
  $r = PostJson "/auth/register" @{ email = $Email; username = "testuser"; password = $Password }
  $r | ConvertTo-Json -Depth 5 | Write-Host
} catch {
  Write-Host "Register failed: $($_.Exception.Message)"
  throw
}

Write-Host "`n[2] Login"
$login = PostJson "/auth/login" @{ email = $Email; password = $Password }
$login | ConvertTo-Json -Depth 5 | Write-Host

Write-Host "`n[3] Refresh (cookie-based)"
$refresh = PostJson "/auth/refresh" @{}
$refresh | ConvertTo-Json -Depth 5 | Write-Host

Write-Host "`n[4] Logout"
$logout = PostJson "/auth/logout" @{}
$logout | ConvertTo-Json -Depth 5 | Write-Host

Write-Host "`nDone."
Write-Host "注意：邮箱验证与重置密码需要从邮件链接取 token："
Write-Host "- verify-email: POST /auth/verify-email { token }"
Write-Host "- reset-password: POST /auth/reset-password { token, new_password }"

