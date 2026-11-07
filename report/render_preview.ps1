param([string]$Path, [string]$OutDir)
New-Item -ItemType Directory -Force $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Path, $true, $false, $false)
$pres.Export($OutDir, "PNG", 1600, 900)
$pres.Close()
$app.Quit()
