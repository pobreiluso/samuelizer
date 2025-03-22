#!/usr/bin/env python
"""
Script para probar todos los comandos posibles de Samuelize con diferentes opciones.
Este script ejecuta cada comando con diferentes combinaciones de parámetros
para verificar que todo funciona correctamente.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import argparse
import tempfile
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('command_tests.log')
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
            
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            shell=isinstance(command, str)
        )
        
        logger.info(f"Código de salida: {result.returncode}")
        
        if result.stdout:
            logger.debug(f"Salida estándar:\n{result.stdout}")
        
        if result.stderr:
            log_level = logging.WARNING if result.returncode != 0 else logging.DEBUG
            logger.log(log_level, f"Salida de error:\n{result.stderr}")
            
        if expected_success and result.returncode != 0:
            logger.error(f"El comando falló inesperadamente: {command_str}")
        elif not expected_success and result.returncode == 0:
            logger.warning(f"El comando tuvo éxito inesperadamente: {command_str}")
            
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"Tiempo de espera agotado para el comando: {command_str}")
        return -1, "", "Timeout"
    except Exception as e:
        logger.error(f"Error al ejecutar el comando {command_str}: {e}")
        return -2, "", str(e)

def test_media_command(sample_media_file, api_key):
    """Prueba el comando 'media' con diferentes opciones"""
    logger.info("=== PRUEBAS DEL COMANDO MEDIA ===")
    
    # Comprobar que el archivo existe
    if not os.path.exists(sample_media_file):
        logger.error(f"El archivo de prueba no existe: {sample_media_file}")
        return False
        
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    output_file = os.path.join(output_dir, "resultado.docx")
    
    # Lista de comandos a probar
    commands = [
        # Comando básico
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key],
        
        # Con diarización
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--diarization"],
        
        # Con diferentes plantillas
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--template", "summary"],
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--template", "key_points"],
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--template", "action_items"],
        
        # Con salida específica
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--output", output_file],
        
        # Con modelo específico
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--model", "whisper-1"],
        
        # Con proveedor específico
        ["poetry", "run", "samuelize", "media", sample_media_file, "--api_key", api_key, "--provider", "openai"],
    ]
    
    # Ejecutar cada comando
    results = []
    for cmd in commands:
        exit_code, _, _ = run_command(cmd, timeout=600)  # 10 minutos máximo
        results.append(exit_code == 0)
        
        # Esperar un poco entre comandos para no sobrecargar la API
        time.sleep(5)
    
    # Verificar resultados
    success_rate = sum(results) / len(results) if results else 0
    logger.info(f"Tasa de éxito del comando media: {success_rate:.2%} ({sum(results)}/{len(results)})")
    
    return all(results)

def test_optimize_command(sample_audio_file):
    """Prueba el comando 'optimize' con diferentes opciones"""
    logger.info("=== PRUEBAS DEL COMANDO OPTIMIZE ===")
    
    # Comprobar que el archivo existe
    if not os.path.exists(sample_audio_file):
        logger.error(f"El archivo de audio de prueba no existe: {sample_audio_file}")
        return False
        
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    
    # Lista de comandos a probar
    commands = [
        # Comando básico
        ["poetry", "run", "samuelize", "optimize", sample_audio_file],
        
        # Con diferentes bitrates
        ["poetry", "run", "samuelize", "optimize", sample_audio_file, "--bitrate", "32k"],
        ["poetry", "run", "samuelize", "optimize", sample_audio_file, "--bitrate", "64k"],
        ["poetry", "run", "samuelize", "optimize", sample_audio_file, "--bitrate", "128k"],
        
        # Con/sin eliminación de silencios
        ["poetry", "run", "samuelize", "optimize", sample_audio_file, "--no-remove-silences"],
        
        # Con salida específica
        ["poetry", "run", "samuelize", "optimize", sample_audio_file, 
         "--output", os.path.join(output_dir, "optimized.mp3")],
    ]
    
    # Ejecutar cada comando
    results = []
    for cmd in commands:
        exit_code, _, _ = run_command(cmd, timeout=300)  # 5 minutos máximo
        results.append(exit_code == 0)
        
        # Esperar un poco entre comandos
        time.sleep(2)
    
    # Verificar resultados
    success_rate = sum(results) / len(results) if results else 0
    logger.info(f"Tasa de éxito del comando optimize: {success_rate:.2%} ({sum(results)}/{len(results)})")
    
    return all(results)

def test_slack_command(slack_token, channel_id, api_key):
    """Prueba el comando 'slack' con diferentes opciones"""
    logger.info("=== PRUEBAS DEL COMANDO SLACK ===")
    
    if not slack_token or not channel_id:
        logger.warning("No se proporcionó token de Slack o ID de canal. Omitiendo pruebas de Slack.")
        return True
        
    # Crear directorio temporal para salidas
    output_dir = tempfile.mkdtemp()
    output_file = os.path.join(output_dir, "slack_resultado.docx")
    
    # Lista de comandos a probar
    commands = [
        # Comando básico - Pasar el channel_id como argumento posicional
        ["poetry", "run", "samuelize", "slack", channel_id, "--token", slack_token, 
         "--api_key", api_key],
        
        # Con diferentes plantillas
        ["poetry", "run", "samuelize", "slack", channel_id, "--token", slack_token, 
         "--api_key", api_key, "--template", "summary"],
        
        # Con salida específica
        ["poetry", "run", "samuelize", "slack", channel_id, "--token", slack_token, 
         "--api_key", api_key, "--output", output_file],
    ]
    
    # Ejecutar cada comando
    results = []
    for cmd in commands:
        exit_code, _, _ = run_command(cmd, timeout=300)  # 5 minutos máximo
        results.append(exit_code == 0)
        
        # Esperar un poco entre comandos para no sobrecargar la API
        time.sleep(5)
    
    # Verificar resultados
    success_rate = sum(results) / len(results) if results else 0
    logger.info(f"Tasa de éxito del comando slack: {success_rate:.2%} ({sum(results)}/{len(results)})")
    
    return all(results)

def main():
    """Función principal que ejecuta todas las pruebas"""
    parser = argparse.ArgumentParser(description="Ejecuta pruebas de todos los comandos de Samuelize")
    parser.add_argument("--api-key", help="Clave API de OpenAI")
    parser.add_argument("--media-file", help="Archivo de audio/video para pruebas")
    parser.add_argument("--audio-file", help="Archivo de audio para pruebas de optimización")
    parser.add_argument("--slack-token", help="Token de Slack para pruebas")
    parser.add_argument("--slack-channel", help="ID del canal de Slack para pruebas")
    
    args = parser.parse_args()
    
    # Verificar API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No se proporcionó clave API de OpenAI. Use --api-key o establezca OPENAI_API_KEY")
        return 1
        
    # Resultados de las pruebas
    results = {}
    
    # Probar comando media si se proporciona un archivo
    if args.media_file:
        results["media"] = test_media_command(args.media_file, api_key)
    else:
        logger.warning("No se proporcionó archivo de media. Omitiendo pruebas del comando media.")
        
    # Probar comando optimize si se proporciona un archivo de audio
    if args.audio_file:
        results["optimize"] = test_optimize_command(args.audio_file)
    else:
        logger.warning("No se proporcionó archivo de audio. Omitiendo pruebas del comando optimize.")
        
    # Probar comando slack si se proporcionan credenciales
    slack_token = args.slack_token or os.environ.get("SLACK_TOKEN")
    slack_channel = args.slack_channel or os.environ.get("SLACK_CHANNEL")
    
    if slack_token and slack_channel:
        results["slack"] = test_slack_command(slack_token, slack_channel, api_key)
    else:
        logger.warning("No se proporcionaron credenciales de Slack. Omitiendo pruebas del comando slack.")
        
    # Resumen final
    logger.info("=== RESUMEN DE RESULTADOS ===")
    for command, success in results.items():
        status = "ÉXITO" if success else "FALLO"
        logger.info(f"Comando {command}: {status}")
        
    # Determinar éxito general
    if all(results.values()):
        logger.info("TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
        return 0
    else:
        logger.error("ALGUNAS PRUEBAS FALLARON")
        return 1

if __name__ == "__main__":
    sys.exit(main())
