# Extract content[0].text from MCP envelope JSON
param(
    [Parameter(Mandatory=$true)][string]$InFile,
    [Parameter(Mandatory=$true)][string]$OutFile
)

$j = Get-Content $InFile -Raw | ConvertFrom-Json
if ($j.error) {
    Write-Host ("MCP ERROR: " + ($j.error | ConvertTo-Json -Depth 5))
    exit 1
}
$text = $j.result.content[0].text
Set-Content -Path $OutFile -Value $text -Encoding UTF8
$len = (Get-Item $OutFile).Length
Write-Host ("Extracted -> {0} ({1} bytes)" -f $OutFile, $len)
