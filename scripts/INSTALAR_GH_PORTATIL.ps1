param(
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

try {
    # Instalador portatil: so baixa binarios oficiais, sem alterar PATH global ou registro.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $architecture = $env:PROCESSOR_ARCHITECTURE
    $platform = switch ($architecture) {
        'ARM64' { 'arm64' }
        'x86' { '386' }
        default { 'amd64' }
    }
    $headers = @{ 'User-Agent' = 'Blue-Studio-Setup' }
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest' -Headers $headers
    $asset = $release.assets | Where-Object { $_.name -match ("windows_{0}\.zip$" -f $platform) } | Select-Object -First 1
    if (-not $asset) { throw "Nao encontrei o pacote Windows $platform na release oficial." }
    if ($asset.browser_download_url -notmatch '^https://github\.com/cli/cli/releases/download/') {
        throw 'URL do pacote nao pertence ao repositorio oficial cli/cli.'
    }
    $temp = Join-Path $env:TEMP ('blue-studio-gh-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temp -Force | Out-Null
    try {
        $zip = Join-Path $temp 'gh.zip'
        Write-Host "Baixando $($asset.name) da release $($release.tag_name)..."
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing
        if ($asset.digest -and $asset.digest.StartsWith('sha256:')) {
            $expected = $asset.digest.Substring(7)
            $actual = (Get-FileHash $zip -Algorithm SHA256).Hash
            if ($actual -ine $expected) { throw 'Checksum SHA256 do pacote nao corresponde ao publicado.' }
        }
        $unpacked = Join-Path $temp 'unpacked'
        Expand-Archive -LiteralPath $zip -DestinationPath $unpacked
        $executable = Get-ChildItem -LiteralPath $unpacked -Filter gh.exe -File -Recurse | Select-Object -First 1
        if (-not $executable) { throw 'Pacote nao continha gh.exe.' }
        New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
        Copy-Item -LiteralPath $executable.FullName -Destination (Join-Path $InstallRoot 'gh.exe') -Force
        & (Join-Path $InstallRoot 'gh.exe') --version
        if ($LASTEXITCODE -ne 0) { throw 'gh.exe foi instalado, mas nao conseguiu executar.' }
        Write-Host '[OK] GitHub CLI portatil instalado.'
    } finally {
        Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Error ("Falha ao instalar o GitHub CLI: " + $_.Exception.Message)
    exit 1
}
