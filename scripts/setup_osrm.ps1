# ==============================================================================
# Script de automação do OSRM para Windows PowerShell
# ==============================================================================
$ErrorActionPreference = "Stop"

$dataDir = Join-Path $PSScriptRoot "..\osrm-data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

$osmUrl = "https://download.geofabrik.de/south-america/brazil/norte-latest.osm.pbf"
$pbfFile = Join-Path $dataDir "norte-latest.osm.pbf"

Write-Host "==> 1. Verificando malha rodoviária do Norte/Pará..." -ForegroundColor Cyan
if (-not (Test-Path $pbfFile)) {
    Write-Host "Baixando malha do Norte (~150MB)..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $osmUrl -OutFile $pbfFile
} else {
    Write-Host "Arquivo $pbfFile ja existe. Pulando download." -ForegroundColor Green
}

$absDataDir = (Resolve-Path $dataDir).Path

Write-Host "==> 2. Extraindo malha com osrm-extract..." -ForegroundColor Cyan
docker run --rm -v "${absDataDir}:/data" osrm/osrm-backend:v5.27.1 osrm-extract -p /opt/car.lua /data/norte-latest.osm.pbf

Write-Host "==> 3. Particionando grafo com osrm-partition..." -ForegroundColor Cyan
docker run --rm -v "${absDataDir}:/data" osrm/osrm-backend:v5.27.1 osrm-partition /data/norte-latest.osrm

Write-Host "==> 4. Customizando celulas com osrm-customize..." -ForegroundColor Cyan
docker run --rm -v "${absDataDir}:/data" osrm/osrm-backend:v5.27.1 osrm-customize /data/norte-latest.osrm

Write-Host "==> 5. Configurando arquivos de grafo..." -ForegroundColor Cyan
$extensions = @("", ".cells", ".fileIndex", ".mldgr", ".names", ".osrm", ".partitionDataSourceIndex", ".partitionIndex", ".restrictions", ".timestamp")
foreach ($ext in $extensions) {
    $src = Join-Path $dataDir ("norte-latest.osrm" + $ext)
    $dst = Join-Path $dataDir ("para-latest.osrm" + $ext)
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
    }
}

Write-Host "==> Sucesso! O grafo OSRM esta pronto." -ForegroundColor Green
Write-Host "Para iniciar o container:" -ForegroundColor White
Write-Host "docker compose -f docker-compose.osrm.yml up -d" -ForegroundColor Yellow
