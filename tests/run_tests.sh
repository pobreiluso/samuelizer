#!/bin/bash
# Script para ejecutar todas las pruebas de Samuelize

# Colores para la salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== EJECUTANDO PRUEBAS DE SAMUELIZE ===${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -d "src" ] || [ ! -d "tests" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Verificar que poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry no está instalado. Instálalo con 'pip install poetry'${NC}"
    exit 1
fi

# Verificar que las dependencias están instaladas
echo -e "${YELLOW}Verificando dependencias...${NC}"
poetry install

# Cargar variables de entorno para pruebas si existe el archivo
if [ -f ".env.test" ]; then
    echo -e "${GREEN}Cargando variables de entorno para pruebas desde .env.test${NC}"
    export $(grep -v '^#' .env.test | xargs)
fi

# Ejecutar pruebas unitarias con mock para evitar llamadas reales a APIs
echo -e "${YELLOW}Ejecutando pruebas unitarias...${NC}"
poetry run python -m unittest discover tests

# Verificar si hay un archivo de audio/video para pruebas
SAMPLE_MEDIA=""
SAMPLE_AUDIO=""

# Buscar archivos de prueba en el directorio tests/samples
if [ -d "tests/samples" ]; then
    # Buscar archivos de video
    for file in tests/samples/*.mp4 tests/samples/*.mov tests/samples/*.avi; do
        if [ -f "$file" ]; then
            SAMPLE_MEDIA="$file"
            echo -e "${GREEN}Encontrado archivo de video para pruebas: $SAMPLE_MEDIA${NC}"
            break
        fi
    done
    
    # Buscar archivos de audio
    for file in tests/samples/*.mp3 tests/samples/*.wav tests/samples/*.m4a; do
        if [ -f "$file" ]; then
            SAMPLE_AUDIO="$file"
            echo -e "${GREEN}Encontrado archivo de audio para pruebas: $SAMPLE_AUDIO${NC}"
            break
        fi
    done
fi

# Verificar API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}ADVERTENCIA: No se encontró OPENAI_API_KEY en el entorno${NC}"
    echo -e "${YELLOW}Algunas pruebas pueden fallar. Establece la variable de entorno OPENAI_API_KEY para pruebas completas.${NC}"
    # Establecer una API key de prueba para evitar errores de autenticación
    export OPENAI_API_KEY="sk-test-key-for-testing-purposes-only"
fi

# Verificar credenciales de Slack
SLACK_ARGS=""
if [ ! -z "$SLACK_TOKEN" ] && [ ! -z "$SLACK_CHANNEL" ]; then
    SLACK_ARGS="--slack-token $SLACK_TOKEN --slack-channel $SLACK_CHANNEL"
    echo -e "${GREEN}Credenciales de Slack encontradas para pruebas${NC}"
else
    echo -e "${YELLOW}ADVERTENCIA: No se encontraron credenciales de Slack en el entorno${NC}"
    echo -e "${YELLOW}Las pruebas de Slack se omitirán. Establece SLACK_TOKEN y SLACK_CHANNEL para pruebas completas.${NC}"
fi

# Ejecutar pruebas específicas de Slack si hay credenciales
if [ ! -z "$SLACK_TOKEN" ]; then
    echo -e "${YELLOW}Ejecutando pruebas específicas de Slack...${NC}"
    poetry run python tests/test_slack_commands.py $API_ARGS $SLACK_ARGS
fi

# Ejecutar pruebas de comandos
echo -e "${YELLOW}Ejecutando pruebas de comandos...${NC}"

MEDIA_ARGS=""
if [ ! -z "$SAMPLE_MEDIA" ]; then
    MEDIA_ARGS="--media-file $SAMPLE_MEDIA"
fi

AUDIO_ARGS=""
if [ ! -z "$SAMPLE_AUDIO" ]; then
    AUDIO_ARGS="--audio-file $SAMPLE_AUDIO"
fi

API_ARGS=""
if [ ! -z "$OPENAI_API_KEY" ]; then
    API_ARGS="--api-key $OPENAI_API_KEY"
fi

# Ejecutar script de pruebas de comandos
poetry run python tests/run_all_commands.py $API_ARGS $MEDIA_ARGS $AUDIO_ARGS $SLACK_ARGS

# Verificar resultado
if [ $? -eq 0 ]; then
    echo -e "${GREEN}¡Todas las pruebas completadas con éxito!${NC}"
else
    echo -e "${RED}Algunas pruebas fallaron. Revisa los logs para más detalles.${NC}"
    exit 1
fi

echo -e "${YELLOW}=== FIN DE LAS PRUEBAS ===${NC}"
