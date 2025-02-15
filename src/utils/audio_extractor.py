import os
import subprocess
import logging
import json
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioExtractor:
    @staticmethod
    def get_supported_formats():
        return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4a', '.wav', '.aac', '.mp3', '.ogg']

    @staticmethod
    def get_audio_info(file_path):
        """Obtiene información del archivo de audio usando ffprobe"""
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
        """Determina si el archivo necesita optimización"""
        if not file_path.lower().endswith('.mp3'):
            return True
            
        info = AudioExtractor.get_audio_info(file_path)
        current_bitrate = info.get('bit_rate')
        
        if not current_bitrate:
            return True
            
        # Convertir target_bitrate a bits
        target_bits = int(target_bitrate.rstrip('k')) * 1024
        
        # Si el bitrate actual es más alto que el objetivo, necesita optimización
        return int(current_bitrate) > target_bits

    @staticmethod
    def extract_audio(input_file, target_bitrate='32k'):
        """
        Extrae o optimiza el audio para Whisper.
        target_bitrate: '32k' para calidad baja, '64k' para calidad media
        """
        logger.info(f"Processing media file: {input_file}...")
        
        # Si es un archivo de audio soportado, verificar si necesita optimización
        if input_file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
            if not AudioExtractor.needs_optimization(input_file, target_bitrate):
                logger.info("File is already optimized, skipping processing")
                return input_file
            
            output_audio = os.path.splitext(input_file)[0] + f'_optimized_{target_bitrate}.mp3'
        else:
            output_audio = os.path.splitext(input_file)[0] + f'_{target_bitrate}.mp3'
        if os.path.exists(output_audio):
            answer = input("Output audio file already exists. Delete it? (yes/no): ")
            if answer.lower() == 'yes':
                logger.info(f"Deleting {output_audio}...")
                os.remove(output_audio)
            else:
                logger.info("Audio extraction cancelled by user.")
                return output_audio

        with tqdm(total=100, desc="Extrayendo audio", unit="%") as pbar:
            logger.info("Starting audio extraction with ffmpeg...")
            pbar.update(10)
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-vn',                    # No video
                '-acodec', 'libmp3lame', # Usar codec MP3
                '-b:a', target_bitrate,  # Bitrate objetivo
                '-ac', '1',              # Mono audio
                '-ar', '16000',          # Sample rate de 16kHz (suficiente para voz)
                '-y',                    # Sobrescribir archivo si existe
                output_audio
            ], check=True)
            pbar.update(90)
            logger.info(f"Audio successfully extracted to {output_audio}")
        return output_audio
