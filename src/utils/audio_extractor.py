import os
import subprocess
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioExtractor:
    @staticmethod
    def extract_audio(input_video, bitrate='56k'):
        logger.info(f"Extracting audio from {input_video}...")
        output_audio = input_video.replace('.mp4', '.mp3')
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
