import os
import subprocess
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioExtractor:
    @staticmethod
    @staticmethod
    def get_supported_formats():
        return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4a', '.wav', '.aac', '.mp3', '.ogg']

    @staticmethod
    def extract_audio(input_file, bitrate='56k'):
        logger.info(f"Processing media file: {input_file}...")
        
        # Si ya es un archivo de audio soportado, retornarlo directamente
        if input_file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
            logger.info("File is already an audio file, skipping extraction")
            return input_file
            
        output_audio = os.path.splitext(input_file)[0] + '.mp3'
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
                '-i', input_video,
                '-b:a', bitrate,
                '-vn',
                output_audio
            ], check=True)
            pbar.update(90)
            logger.info(f"Audio successfully extracted to {output_audio}")
        return output_audio
