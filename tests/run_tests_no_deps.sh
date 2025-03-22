#!/bin/bash
# Script para ejecutar pruebas sin instalar dependencias problemáticas

# Colores para la salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== EJECUTANDO PRUEBAS BÁSICAS DE SAMUELIZE ===${NC}"

# Configurar variables de entorno para pruebas
export OPENAI_API_KEY="sk-test-key-for-testing-purposes-only"
export TEST_LOCAL_MODE="true"

# Ejecutar pruebas unitarias
echo -e "${YELLOW}Ejecutando pruebas unitarias...${NC}"
PYTHONPATH=. python -m unittest tests/test_commands.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo -e "${GREEN}¡Pruebas unitarias completadas con éxito!${NC}"
else
    echo -e "${RED}Algunas pruebas unitarias fallaron. Revisa los logs para más detalles.${NC}"
    exit 1
fi

echo -e "${YELLOW}=== FIN DE LAS PRUEBAS ===${NC}"
