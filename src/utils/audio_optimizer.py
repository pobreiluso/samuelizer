import os
import subprocess
import logging
import json
import time
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioOptimizer:
    """
    Clase responsable de optimizar archivos de audio para transcripción.
    Sigue el principio de responsabilidad única (SRP) de SOLID.
    """
    
    @staticmethod
    def get_audio_info(file_path):
        """
        Obtiene información del archivo de audio usando ffprobe.
        
        Args:
            file_path (str): Ruta al archivo de audio
            
        Returns:
            dict: Información del stream de audio que contiene:
                - bit_rate: Bitrate actual
                - codec_name: Códec de audio utilizado
                
        Raises:
            subprocess.CalledProcessError: Si el comando ffprobe falla
            json.JSONDecodeError: Si la salida de ffprobe no es JSON válido
        """
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=bit_rate,codec_name',
                '-of', 'json',
                file_path
            ], capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return info.get('streams', [{}])[0]
        except Exception as e:
            logger.warning(f"No se pudo obtener información del audio: {e}")
            return {}

    @staticmethod
    def needs_optimization(file_path, target_bitrate='32k'):
        """
        Determina si el archivo de audio necesita optimización.
        
        Args:
            file_path (str): Ruta al archivo de audio
            target_bitrate (str): Bitrate objetivo (ej. '32k', '64k')
            
        Returns:
            bool: True si el archivo necesita optimización, False en caso contrario
            
        Notes:
            - Archivos que no son MP3 siempre necesitan optimización
            - Archivos con bitrate mayor al objetivo necesitan optimización
            - Archivos sin información de bitrate se asume que necesitan optimización
        """
        if not file_path.lower().endswith('.mp3'):
            return True
            
        info = AudioOptimizer.get_audio_info(file_path)
        current_bitrate = info.get('bit_rate')
        
        if not current_bitrate:
            return True
            
        # Convertir target_bitrate a bits
        target_bits = int(target_bitrate.rstrip('k')) * 1024
        
        # Si el bitrate actual es mayor que el objetivo, necesita optimización
        return int(current_bitrate) > target_bits

    @staticmethod
    def get_file_size_mb(file_path):
        """
        Obtiene el tamaño del archivo en megabytes
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            float: Tamaño del archivo en MB
        """
        return os.path.getsize(file_path) / (1024 * 1024)
    
    @staticmethod
    def remove_silence(input_file: str, output_file: str, silence_threshold: str = '-30dB', 
                       min_silence_duration: str = '1.0', keep_silence: str = '0.3') -> str:
        """
        Elimina silencios largos del archivo de audio
        
        Args:
            input_file (str): Ruta al archivo de audio de entrada
            output_file (str): Ruta al archivo de audio de salida
            silence_threshold (str): Umbral para detección de silencio (ej. '-30dB')
            min_silence_duration (str): Duración mínima de silencio a eliminar (en segundos)
            keep_silence (str): Cantidad de silencio a mantener al inicio/fin de secciones no silenciosas
            
        Returns:
            str: Ruta al archivo de audio procesado
        """
        logger.info(f"Eliminando silencios del archivo de audio: {input_file}")
        
        # Usar el filtro silenceremove de ffmpeg para eliminar silencios largos
        subprocess.run([
            'ffmpeg',
            '-i', input_file,
            '-af', f'silenceremove=stop_periods=-1:stop_threshold={silence_threshold}:stop_duration={min_silence_duration}:stop_silence={keep_silence}',
            '-y',
            output_file
        ], check=True)
        
        # Obtener información de reducción de tamaño
        original_size = AudioOptimizer.get_file_size_mb(input_file)
        new_size = AudioOptimizer.get_file_size_mb(output_file)
        reduction = (1 - (new_size / original_size)) * 100 if original_size > 0 else 0
        
        logger.info(f"Eliminación de silencios completada. Tamaño reducido de {original_size:.2f}MB a {new_size:.2f}MB ({reduction:.1f}% reducción)")
        return output_file

    @staticmethod
    def optimize_audio(input_file: str, output_file: str = None, target_bitrate: str = '128k',
                      remove_silences: bool = True, max_size_mb: int = 100) -> str:
        """
        Optimiza un archivo de audio para procesamiento con Whisper.
        
        Args:
            input_file (str): Ruta al archivo de audio de entrada
            output_file (str): Ruta al archivo de audio de salida
            target_bitrate (str): Bitrate objetivo para optimización
                                 '128k' para alta calidad (por defecto)
                                 '64k' para calidad media
                                 '32k' para calidad baja
            remove_silences (bool): Si se deben eliminar silencios largos
            max_size_mb (int): Tamaño máximo del archivo en MB antes de aplicar optimización más agresiva
                                 
        Returns:
            str: Ruta al archivo de audio procesado
            
        Raises:
            subprocess.CalledProcessError: Si el comando ffmpeg falla
            OSError: Si las operaciones de archivo fallan
        """
        # Si output_file es None o es igual a input_file, generar un nombre de archivo único
        if output_file is None or output_file == input_file:
            base_dir = os.path.dirname(input_file) or '.'
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(base_dir, f"{base_name}_optimized_{int(time.time())}.mp3")
            
        logger.info(f"Optimizando archivo de audio: {input_file}...")
        
        with tqdm(total=100, desc="Optimizando audio", unit="%") as pbar:
            # Extracción inicial con alta calidad
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-vn',                    # Sin video
                '-acodec', 'libmp3lame', # Usar códec MP3
                '-b:a', target_bitrate,  # Bitrate objetivo (alta calidad por defecto)
                '-ac', '1',              # Audio mono
                '-ar', '16000',          # Tasa de muestreo 16kHz (suficiente para voz)
                '-y',                    # Sobrescribir archivo si existe
                output_file
            ], check=True)
            pbar.update(40)
            
            # Verificar si el archivo es demasiado grande y necesita más optimización
            file_size_mb = AudioOptimizer.get_file_size_mb(output_file)
            if file_size_mb > max_size_mb:
                logger.info(f"Tamaño del archivo ({file_size_mb:.2f}MB) excede {max_size_mb}MB. Aplicando optimización adicional...")
                
                # Calcular bitrate apropiado basado en el tamaño del archivo
                new_bitrate = min(int(target_bitrate.rstrip('k')), int((max_size_mb / file_size_mb) * int(target_bitrate.rstrip('k'))))
                new_bitrate = max(new_bitrate, 32)  # No bajar de 32k
                new_bitrate_str = f"{new_bitrate}k"
                
                temp_output = output_file + ".temp.mp3"
                subprocess.run([
                    'ffmpeg',
                    '-i', output_file,
                    '-b:a', new_bitrate_str,
                    '-y',
                    temp_output
                ], check=True)
                
                os.replace(temp_output, output_file)
                logger.info(f"Bitrate reducido a {new_bitrate_str}")
            
            pbar.update(30)
            
            # Eliminar silencios si se solicita
            if remove_silences:
                silence_removed_output = output_file + ".nosilence.mp3"
                AudioOptimizer.remove_silence(output_file, silence_removed_output)
                os.replace(silence_removed_output, output_file)
                pbar.update(30)
            
            logger.info(f"Audio optimizado correctamente: {output_file}")
            logger.info(f"Tamaño final del archivo: {AudioOptimizer.get_file_size_mb(output_file):.2f}MB")
        
        return output_file
