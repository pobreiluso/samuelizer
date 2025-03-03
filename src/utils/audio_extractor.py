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
        """
        Get audio file information using ffprobe.
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            dict: Audio stream information containing:
                - bit_rate: Current bitrate
                - codec_name: Audio codec used
                
        Raises:
            subprocess.CalledProcessError: If ffprobe command fails
            json.JSONDecodeError: If ffprobe output is not valid JSON
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
            logger.warning(f"Could not get audio information: {e}")
            return {}

    @staticmethod
    def needs_optimization(file_path, target_bitrate='32k'):
        """
        Determine if the audio file needs optimization.
        
        Args:
            file_path (str): Path to the audio file
            target_bitrate (str): Target bitrate (e.g., '32k', '64k')
            
        Returns:
            bool: True if file needs optimization, False otherwise
            
        Notes:
            - Non-MP3 files always need optimization
            - Files with higher bitrate than target need optimization
            - Files without bitrate info are assumed to need optimization
        """
        if not file_path.lower().endswith('.mp3'):
            return True
            
        info = AudioExtractor.get_audio_info(file_path)
        current_bitrate = info.get('bit_rate')
        
        if not current_bitrate:
            return True
            
        # Convert target_bitrate to bits
        target_bits = int(target_bitrate.rstrip('k')) * 1024
        
        # If current bitrate is higher than target, needs optimization
        return int(current_bitrate) > target_bits

    @staticmethod
    def extract_audio(input_file: str, target_bitrate: str = '32k', chunk_size: int = 8192) -> str:
        """
        Extract or optimize audio for Whisper processing.
        
        Args:
            input_file (str): Path to input media file
            target_bitrate (str): Target bitrate for optimization
                                 '32k' for low quality
                                 '64k' for medium quality
                                 
        Returns:
            str: Path to the processed audio file
            
        Raises:
            subprocess.CalledProcessError: If ffmpeg command fails
            OSError: If file operations fail
        """
        logger.info(f"Processing media file: {input_file}...")
        
        # If it's a supported audio file, check if it needs optimization
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

        with tqdm(total=100, desc="Extracting audio", unit="%") as pbar:
            logger.info("Starting audio extraction with ffmpeg...")
            pbar.update(10)
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-vn',                    # No video
                '-acodec', 'libmp3lame', # Use MP3 codec
                '-b:a', target_bitrate,  # Target bitrate
                '-ac', '1',              # Mono audio
                '-ar', '16000',          # Sample rate 16kHz (sufficient for voice)
                '-y',                    # Overwrite file if exists
                output_audio
            ], check=True)
            pbar.update(90)
            logger.info(f"Audio successfully extracted to {output_audio}")
        return output_audio
