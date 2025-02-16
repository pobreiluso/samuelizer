import sounddevice as sd
import numpy as np
import wave
import os
import logging
from datetime import datetime
from threading import Thread, Event
import queue

logger = logging.getLogger(__name__)

class SystemAudioCapture:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stop_event = Event()
        self.current_file = None
        
    def start_recording(self, output_dir="recordings"):
        """
        Start system audio recording.
        
        Args:
            output_dir (str): Directory where recordings will be saved
            
        Returns:
            None
            
        Note:
            Creates output directory if it doesn't exist
        """
        if self.recording:
            logger.warning("Recording already in progress")
            return
            
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = os.path.join(output_dir, f"recording_{timestamp}.wav")
        
        self.recording = True
        self.stop_event.clear()
        
        # Iniciar thread de grabación
        self.record_thread = Thread(target=self._record)
        self.record_thread.start()
        
        # Iniciar thread de guardado
        self.save_thread = Thread(target=self._save_audio)
        self.save_thread.start()
        
        logger.info(f"Starting recording to {self.current_file}")
        
    def _record(self):
        """Main recording function that captures system audio"""
        with sd.InputStream(samplerate=self.sample_rate, 
                          channels=self.channels, 
                          callback=self._audio_callback):
            self.stop_event.wait()
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback that receives system audio data"""
        if status:
            logger.warning(f"Status: {status}")
        self.audio_queue.put(indata.copy())
    
    def _save_audio(self):
        """Save audio data to WAV file"""
        with wave.open(self.current_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16 bits
            wf.setframerate(self.sample_rate)
            
            while self.recording or not self.audio_queue.empty():
                try:
                    data = self.audio_queue.get(timeout=1)
                    wf.writeframes((data * 32767).astype(np.int16).tobytes())
                except queue.Empty:
                    continue
    
    def stop_recording(self):
        """
        Stop recording and save the file.
        
        Returns:
            str: Path to the saved recording file
        """
        if not self.recording:
            return
            
        self.recording = False
        self.stop_event.set()
        
        # Esperar a que terminen los threads
        self.record_thread.join()
        self.save_thread.join()
        
        logger.info(f"Recording stopped and saved to {self.current_file}")
        return self.current_file
