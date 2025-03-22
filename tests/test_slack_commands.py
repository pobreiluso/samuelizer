#!/usr/bin/env python
"""
Script para probar específicamente los comandos de Slack de Samuelize.
"""

import os
import sys
import subprocess
import logging
import argparse
import tempfile
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('slack_tests.log')
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, expected_success=True, timeout=None):
    """
    Ejecuta un comando y registra el resultado
    
    Args:
        command: Comando a ejecutar (lista o cadena)
        expected_success: Si se espera que el comando tenga éxito
        timeout: Tiempo máximo de ejecución en segundos
        
    Returns:
        tuple: (código de salida, stdout, stderr)
    """
    logger.info(f"Ejecutando: {command}")
    
    try:
        if isinstance(command, str):
            command_str = command
        else:
            command_str = " ".join(command)
        
        # Usar PIPE para stdout y stderr para capturar la salida
        # pero también mostrarla en tiempo real para debugging
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=isinstance(command, str)
        )
        
        # Capturar la salida con timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            # Matar el proceso si excede el timeout
            process.kill()
            logger.error(f"Tiempo de espera agotado para el comando: {command_str}")
            return -1, "", "Timeout"
        logger.info(f"Código de salida: {exit_code}")
        
        if stdout:
            logger.debug(f"Salida estándar:\n{stdout}")
        
        if stderr:
            log_level = logging.WARNING if exit_code != 0 else logging.DEBUG
            logger.log(log_level, f"Salida de error:\n{stderr}")
            
        if expected_success and exit_code != 0:
            logger.error(f"El comando falló inesperadamente: {command_str}")
        elif not expected_success and exit_code == 0:
            logger.warning(f"El comando tuvo éxito inesperadamente: {command_str}")
            
        return exit_code, stdout, stderr
        
    except Exception as e:
        logger.error(f"Error al ejecutar el comando {command_str}: {e}")
        return -2, "", str(e)

def test_slack_list_channels(slack_token):
    """Prueba el comando 'slack --list-channels'"""
    logger.info("=== PRUEBA DEL COMANDO SLACK --LIST-CHANNELS ===")
    
    if not slack_token:
        logger.warning("No se proporcionó token de Slack. Omitiendo prueba.")
        return None
    
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    output_file = os.path.join(output_dir, "canales_slack.txt")
    
    # Comando a probar
    command = [
        "poetry", "run", "samuelize", "slack", 
        "--list-channels", 
        "--token", slack_token,
        "--output", output_file
    ]
    
    # Ejecutar comando
    exit_code, stdout, stderr = run_command(command, timeout=300)
    
    # Verificar si se creó el archivo de salida
    if exit_code == 0 and os.path.exists(output_file):
        logger.info(f"Archivo de salida creado: {output_file}")
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Contenido del archivo (primeras 200 caracteres): {content[:200]}...")
    
    return exit_code == 0

def test_slack_summary(slack_token, api_key):
    """Prueba el comando 'slack --summary'"""
    logger.info("=== PRUEBA DEL COMANDO SLACK --SUMMARY ===")
    
    if not slack_token or not api_key:
        logger.warning("No se proporcionó token de Slack o API key. Omitiendo prueba.")
        return None
    
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    output_file = os.path.join(output_dir, "resumen_slack.docx")
    
    # Obtener fecha del último día laborable (viernes) y una semana antes
    from datetime import datetime, timedelta
    today = datetime.now()
    # Calcular el último viernes (día 4 de la semana, donde lunes es 0)
    days_since_friday = (today.weekday() - 4) % 7
    last_friday = (today - timedelta(days=days_since_friday)).strftime("%Y-%m-%d")
    # Una semana antes del último viernes
    week_before_friday = (today - timedelta(days=days_since_friday+7)).strftime("%Y-%m-%d")
    
    logger.info(f"Analizando mensajes desde {week_before_friday} hasta {last_friday}")
    
    # Comando a probar
    command = [
        "poetry", "run", "samuelize", "slack", 
        "--summary", 
        "--token", slack_token,
        "--api_key", api_key,
        "--start-date", week_before_friday,
        "--end-date", last_friday,
        "--output", output_file,
        "--min-messages", "1",  # Reducir el mínimo para pruebas
        "--max-channels", "3"   # Limitar a 3 canales para que sea más rápido
    ]
    
    # Ejecutar comando con timeout más corto para evitar bloqueos
    exit_code, stdout, stderr = run_command(command, timeout=180)  # 3 minutos máximo
    
    # Verificar si se creó el archivo de salida
    if exit_code == 0 and os.path.exists(output_file):
        logger.info(f"Archivo de salida creado: {output_file}")
        # Verificar tamaño del archivo
        file_size = os.path.getsize(output_file)
        logger.info(f"Tamaño del archivo: {file_size} bytes")
    
    return exit_code == 0

def test_slack_channel(slack_token, api_key, channel_id):
    """Prueba el comando 'slack' con un canal específico"""
    logger.info("=== PRUEBA DEL COMANDO SLACK CON CANAL ESPECÍFICO ===")
    
    if not slack_token or not api_key or not channel_id:
        logger.warning("No se proporcionó token de Slack, API key o ID de canal. Omitiendo prueba.")
        return None
    
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    output_file = os.path.join(output_dir, "canal_slack.docx")
    
    # Obtener fecha del último día laborable (viernes) y una semana antes
    from datetime import datetime, timedelta
    today = datetime.now()
    # Calcular el último viernes (día 4 de la semana, donde lunes es 0)
    days_since_friday = (today.weekday() - 4) % 7
    last_friday = (today - timedelta(days=days_since_friday)).strftime("%Y-%m-%d")
    # Una semana antes del último viernes
    week_before_friday = (today - timedelta(days=days_since_friday+7)).strftime("%Y-%m-%d")
    
    logger.info(f"Analizando mensajes desde {week_before_friday} hasta {last_friday}")
    
    # Comando a probar con fechas específicas
    command = [
        "poetry", "run", "samuelize", "slack", 
        channel_id,
        "--token", slack_token,
        "--api_key", api_key,
        "--start-date", week_before_friday,
        "--end-date", last_friday,
        "--output", output_file
    ]
    
    # Ejecutar comando
    exit_code, stdout, stderr = run_command(command, timeout=300)
    
    # Verificar si se creó el archivo de salida
    if exit_code == 0 and os.path.exists(output_file):
        logger.info(f"Archivo de salida creado: {output_file}")
        # Verificar tamaño del archivo
        file_size = os.path.getsize(output_file)
        logger.info(f"Tamaño del archivo: {file_size} bytes")
    
    return exit_code == 0

def main():
    """Función principal que ejecuta todas las pruebas"""
    parser = argparse.ArgumentParser(description="Ejecuta pruebas de comandos de Slack de Samuelize")
    parser.add_argument("--api-key", help="Clave API de OpenAI")
    parser.add_argument("--slack-token", help="Token de Slack para pruebas")
    parser.add_argument("--slack-channel", help="ID del canal de Slack para pruebas")
    
    args = parser.parse_args()
    
    # Verificar credenciales
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    slack_token = args.slack_token or os.environ.get("SLACK_TOKEN")
    slack_channel = args.slack_channel or os.environ.get("SLACK_CHANNEL")
    
    if not slack_token:
        logger.error("No se proporcionó token de Slack. Use --slack-token o establezca SLACK_TOKEN")
        return 1
    
    # Si no se proporciona un canal específico, intentar obtener uno válido
    if not slack_channel and slack_token:
        try:
            # Ejecutar comando para listar canales
            list_cmd = ["poetry", "run", "samuelize", "slack", "--list-channels", "--token", slack_token]
            exit_code, stdout, stderr = run_command(list_cmd, timeout=60)
            
            if exit_code == 0 and stdout:
                # Buscar un canal público en la salida
                import re
                channel_matches = re.findall(r'#([a-z0-9_-]+) \(ID: (C[A-Z0-9]+)\)', stdout)
                if channel_matches:
                    # Usar el primer canal encontrado
                    channel_name, channel_id = channel_matches[0]
                    logger.info(f"Usando canal encontrado automáticamente: #{channel_name} (ID: {channel_id})")
                    slack_channel = channel_id
        except Exception as e:
            logger.warning(f"No se pudo obtener un canal automáticamente: {e}")
    
    # Resultados de las pruebas
    results = {}
    
    # Probar comando slack --list-channels
    results["list_channels"] = test_slack_list_channels(slack_token)
    
    # Probar comando slack --summary
    if api_key:
        results["summary"] = test_slack_summary(slack_token, api_key)
    else:
        logger.warning("No se proporcionó API key. Omitiendo prueba de slack --summary")
    
    # Probar comando slack con canal específico
    if api_key and slack_channel:
        results["channel"] = test_slack_channel(slack_token, api_key, slack_channel)
    else:
        logger.warning("No se proporcionó API key o ID de canal. Omitiendo prueba de slack con canal específico")
    
    # Resumen final
    logger.info("=== RESUMEN DE RESULTADOS ===")
    for command, success in results.items():
        if success is None:
            status = "OMITIDO"
        elif success:
            status = "ÉXITO"
        else:
            status = "FALLO"
        logger.info(f"Comando slack {command}: {status}")
    
    # Determinar éxito general
    successful_tests = [result for result in results.values() if result is True]
    failed_tests = [result for result in results.values() if result is False]
    
    if failed_tests:
        logger.error(f"ALGUNAS PRUEBAS FALLARON: {len(failed_tests)} de {len(results)}")
        return 1
    elif successful_tests:
        logger.info(f"TODAS LAS PRUEBAS PASARON: {len(successful_tests)} de {len(results)}")
        return 0
    else:
        logger.warning("NO SE EJECUTARON PRUEBAS")
        return 0

if __name__ == "__main__":
    sys.exit(main())
