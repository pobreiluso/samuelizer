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
    def get_file_size_mb(file_path):
        """
        Get file size in megabytes
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            float: File size in MB
        """
        return os.path.getsize(file_path) / (1024 * 1024)
    
    @staticmethod
    def remove_silence(input_file: str, output_file: str, silence_threshold: str = '-30dB', 
                       min_silence_duration: str = '1.0', keep_silence: str = '0.3') -> str:
        """
        Remove long silences from audio file
        
        Args:
            input_file (str): Path to input audio file
            output_file (str): Path to output audio file
            silence_threshold (str): Threshold for silence detection (e.g. '-30dB')
            min_silence_duration (str): Minimum silence duration to remove (in seconds)
            keep_silence (str): Amount of silence to keep at the beginning/end of non-silent sections
            
        Returns:
            str: Path to the processed audio file
        """
        logger.info(f"Removing silences from audio file: {input_file}")
        
        # Use ffmpeg's silenceremove filter to remove long silences
        subprocess.run([
            'ffmpeg',
            '-i', input_file,
            '-af', f'silenceremove=stop_periods=-1:stop_threshold={silence_threshold}:stop_duration={min_silence_duration}:stop_silence={keep_silence}',
            '-y',
            output_file
        ], check=True)
        
        # Get size reduction information
        original_size = AudioExtractor.get_file_size_mb(input_file)
        new_size = AudioExtractor.get_file_size_mb(output_file)
        reduction = (1 - (new_size / original_size)) * 100 if original_size > 0 else 0
        
        logger.info(f"Silence removal complete. Size reduced from {original_size:.2f}MB to {new_size:.2f}MB ({reduction:.1f}% reduction)")
        return output_file

    @staticmethod
    def extract_audio(input_file: str, target_bitrate: str = '128k', chunk_size: int = 8192, 
                      remove_silences: bool = True, max_size_mb: int = 100) -> str:
        """
        Extract or optimize audio for Whisper processing.
        
        Args:
            input_file (str): Path to input media file
            target_bitrate (str): Target bitrate for optimization
                                 '128k' for high quality (default)
                                 '64k' for medium quality
                                 '32k' for low quality
            chunk_size (int): Chunk size for file operations
            remove_silences (bool): Whether to remove long silences
            max_size_mb (int): Maximum file size in MB before applying more aggressive optimization
                                 
        Returns:
            str: Path to the processed audio file
            
        Raises:
            subprocess.CalledProcessError: If ffmpeg command fails
            OSError: If file operations fail
        """
        logger.info(f"Processing media file: {input_file}...")
        
        # Get output directory (same as recordings directory)
        output_dir = os.path.dirname(input_file)
        if not output_dir:
            output_dir = "recordings"
            os.makedirs(output_dir, exist_ok=True)
        
        # If it's a supported audio file, check if it needs optimization
        if input_file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
            if not AudioExtractor.needs_optimization(input_file, target_bitrate):
                logger.info("File is already optimized, skipping processing")
                return input_file
            
            output_audio = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + f'_optimized.mp3')
        else:
            output_audio = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + f'_audio.mp3')
        
        if os.path.exists(output_audio):
            answer = input(f"Output audio file {output_audio} already exists. Delete it? (yes/no): ")
            if answer.lower() == 'yes':
                logger.info(f"Deleting {output_audio}...")
                os.remove(output_audio)
            else:
                logger.info("Audio extraction cancelled by user.")
                return output_audio

        with tqdm(total=100, desc="Extracting audio", unit="%") as pbar:
            logger.info("Starting audio extraction with ffmpeg...")
            pbar.update(10)
            
            # Initial extraction with high quality
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-vn',                    # No video
                '-acodec', 'libmp3lame', # Use MP3 codec
                '-b:a', target_bitrate,  # Target bitrate (high quality by default)
                '-ac', '1',              # Mono audio
                '-ar', '16000',          # Sample rate 16kHz (sufficient for voice)
                '-y',                    # Overwrite file if exists
                output_audio
            ], check=True)
            pbar.update(40)
            
            # Check if file is too large and needs more optimization
            file_size_mb = AudioExtractor.get_file_size_mb(output_audio)
            if file_size_mb > max_size_mb:
                logger.info(f"File size ({file_size_mb:.2f}MB) exceeds {max_size_mb}MB. Applying additional optimization...")
                
                # Calculate appropriate bitrate based on file size
                new_bitrate = min(int(target_bitrate.rstrip('k')), int((max_size_mb / file_size_mb) * int(target_bitrate.rstrip('k'))))
                new_bitrate = max(new_bitrate, 32)  # Don't go below 32k
                new_bitrate_str = f"{new_bitrate}k"
                
                temp_output = output_audio + ".temp.mp3"
                subprocess.run([
                    'ffmpeg',
                    '-i', output_audio,
                    '-b:a', new_bitrate_str,
                    '-y',
                    temp_output
                ], check=True)
                
                os.replace(temp_output, output_audio)
                logger.info(f"Reduced bitrate to {new_bitrate_str}")
            
            pbar.update(30)
            
            # Remove silences if requested
            if remove_silences:
                silence_removed_output = output_audio + ".nosilence.mp3"
                AudioExtractor.remove_silence(output_audio, silence_removed_output)
                os.replace(silence_removed_output, output_audio)
                pbar.update(20)
            
            logger.info(f"Audio successfully extracted and optimized: {output_audio}")
            logger.info(f"Final file size: {AudioExtractor.get_file_size_mb(output_audio):.2f}MB")
        
        return output_audio
