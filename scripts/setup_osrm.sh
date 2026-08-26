#!/usr/bin/env bash
# ==============================================================================
# Script de automação do OSRM para a região do Pará / Santarém / Alter do Chão
# ==============================================================================
set -euo pipefail

DATA_DIR="./osrm-data"
OSM_URL="https://download.geofabrik.de/south-america/brazil/norte-latest.osm.pbf"
PBF_FILE="${DATA_DIR}/norte-latest.osm.pbf"
OSRM_BASE="${DATA_DIR}/para-latest.osrm"

echo "==> 1. Criando diretório de dados: ${DATA_DIR}"
mkdir -p "${DATA_DIR}"

if [ ! -f "${PBF_FILE}" ]; then
  echo "==> 2. Baixando malha rodoviária do Norte/Pará (~150MB)..."
  curl -L -o "${PBF_FILE}" "${OSM_URL}"
else
  echo "==> 2. Arquivo ${PBF_FILE} já existe. Pulando download."
fi

echo "==> 3. Extraindo malha com osrm-extract (perfil car)..."
docker run --rm -v "${PWD}/${DATA_DIR}:/data" osrm/osrm-backend:v5.27.1 osrm-extract -p /opt/car.lua /data/norte-latest.osm.pbf

echo "==> 4. Particionando grafo com osrm-partition..."
docker run --rm -v "${PWD}/${DATA_DIR}:/data" osrm/osrm-backend:v5.27.1 osrm-partition /data/norte-latest.osrm

echo "==> 5. Customizando células com osrm-customize..."
docker run --rm -v "${PWD}/${DATA_DIR}:/data" osrm/osrm-backend:v5.27.1 osrm-customize /data/norte-latest.osrm

# Renomear para o nome canônico esperado pelo docker-compose se necessário
if [ -f "${DATA_DIR}/norte-latest.osrm" ] && [ ! -f "${OSRM_BASE}" ]; then
  echo "==> 6. Linkando grafo consolidado para ${OSRM_BASE}..."
  cp "${DATA_DIR}/norte-latest.osrm" "${OSRM_BASE}" || true
  for ext in cells fileIndex mldgr names osrm partitionDataSourceIndex partitionIndex restrictions timestamp; do
    if [ -f "${DATA_DIR}/norte-latest.osrm.${ext}" ]; then
      cp "${DATA_DIR}/norte-latest.osrm.${ext}" "${DATA_DIR}/para-latest.osrm.${ext}" || true
    fi
  done
fi

echo "==> 7. Grafo OSRM pronto para execução!"
echo "Para iniciar o serviço, execute: docker compose -f docker-compose.osrm.yml up -d"
