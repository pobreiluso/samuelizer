import os
import subprocess
import logging
from tqdm import tqdm
from src.utils.audio_optimizer import AudioOptimizer

logger = logging.getLogger(__name__)

class AudioExtractor:
    """
    Clase responsable de extraer audio de archivos multimedia.
    Sigue el principio de responsabilidad única (SRP) de SOLID.
    """
    
    @staticmethod
    def get_supported_formats():
        """
        Obtiene los formatos de archivo soportados para extracción de audio
        
        Returns:
            list: Lista de extensiones de archivo soportadas
        """
        return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4a', '.wav', '.aac', '.mp3', '.ogg']

    @staticmethod
    def extract_audio(input_file: str, target_bitrate: str = '128k', chunk_size: int = 8192, 
                      remove_silences: bool = True, max_size_mb: int = 100) -> str:
        """
        Extrae audio de un archivo multimedia y lo optimiza para procesamiento con Whisper.
        
        Args:
            input_file (str): Ruta al archivo multimedia de entrada
            target_bitrate (str): Bitrate objetivo para optimización
                                 '128k' para alta calidad (por defecto)
                                 '64k' para calidad media
                                 '32k' para calidad baja
            chunk_size (int): Tamaño de chunk para operaciones de archivo
            remove_silences (bool): Si se deben eliminar silencios largos
            max_size_mb (int): Tamaño máximo del archivo en MB antes de aplicar optimización más agresiva
                                 
        Returns:
            str: Ruta al archivo de audio procesado
            
        Raises:
            subprocess.CalledProcessError: Si el comando ffmpeg falla
            OSError: Si las operaciones de archivo fallan
        """
        logger.info(f"Procesando archivo multimedia: {input_file}...")
        
        # Obtener directorio de salida (mismo que el directorio de grabaciones)
        output_dir = os.path.dirname(input_file)
        if not output_dir:
            output_dir = "recordings"
            os.makedirs(output_dir, exist_ok=True)
        
        # Si es un archivo de audio soportado, verificar si necesita optimización
        if input_file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
            if not AudioOptimizer.needs_optimization(input_file, target_bitrate):
                logger.info("El archivo ya está optimizado, omitiendo procesamiento")
                return input_file
            
            output_audio = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + f'_optimized.mp3')
        else:
            output_audio = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + f'_audio.mp3')
        
        if os.path.exists(output_audio):
            answer = input(f"El archivo de audio de salida {output_audio} ya existe. ¿Eliminarlo? (yes/no): ")
            if answer.lower() == 'yes':
                logger.info(f"Eliminando {output_audio}...")
                os.remove(output_audio)
            else:
                logger.info("Extracción de audio cancelada por el usuario.")
                return output_audio

        # Extraer audio del archivo multimedia
        with tqdm(total=100, desc="Extrayendo audio", unit="%") as pbar:
            logger.info("Iniciando extracción de audio con ffmpeg...")
            
            # Extracción inicial
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-vn',                    # Sin video
                '-acodec', 'libmp3lame', # Usar códec MP3
                '-b:a', target_bitrate,  # Bitrate objetivo
                '-ac', '1',              # Audio mono
                '-ar', '16000',          # Tasa de muestreo 16kHz (suficiente para voz)
                '-y',                    # Sobrescribir archivo si existe
                output_audio
            ], check=True)
            pbar.update(100)
            
            logger.info(f"Audio extraído correctamente: {output_audio}")
        
        # Optimizar el audio extraído
        return AudioOptimizer.optimize_audio(
            output_audio, 
            output_audio, 
            target_bitrate=target_bitrate,
            remove_silences=remove_silences,
            max_size_mb=max_size_mb
        )
