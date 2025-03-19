import os
import unittest
import tempfile
import shutil
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

# Configurar logging para las pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSamuelize(unittest.TestCase):
    """
    Pruebas para los comandos principales de Samuelize
    """
    
    def setUp(self):
        """Preparar entorno de prueba"""
        # Crear directorio temporal para pruebas
        self.test_dir = tempfile.mkdtemp()
        self.sample_audio = os.path.join(self.test_dir, "sample_audio.mp3")
        self.sample_video = os.path.join(self.test_dir, "sample_video.mp4")
        
        # Crear archivos de prueba vacíos
        Path(self.sample_audio).touch()
        Path(self.sample_video).touch()
        
        # Configurar variables de entorno para pruebas
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
    def tearDown(self):
        """Limpiar después de las pruebas"""
        # Eliminar directorio temporal
        shutil.rmtree(self.test_dir)
        
    @patch('src.controller.run_transcription')
    @patch('src.controller.run_analysis')
    @patch('src.controller.save_meeting_info')
    def test_media_command(self, mock_save, mock_analyze, mock_transcribe):
        """Probar el comando 'media'"""
        from src.cli import process_media_command
        
        # Configurar mocks
        mock_transcribe.return_value = "Transcripción de prueba"
        mock_analyze.return_value = {
            "abstract_summary": "Resumen de prueba",
            "key_points": "Puntos clave de prueba",
            "action_items": "Acciones de prueba",
            "sentiment": "Sentimiento de prueba"
        }
        mock_save.return_value = os.path.join(self.test_dir, "output.docx")
        
        # Ejecutar comando
        args = MagicMock()
        args.file_path = self.sample_video
        args.diarization = False
        args.api_key = "test_api_key"
        args.provider = "openai"
        args.model = "whisper-1"
        args.template = "summary"
        args.output = os.path.join(self.test_dir, "output.docx")
        
        process_media_command(args)
        
        # Verificar que se llamaron las funciones correctas
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()
        mock_save.assert_called_once()
        
    @patch('src.slack.download_slack_channel.SlackDownloader')
    @patch('src.controller.run_analysis')
    @patch('src.controller.save_meeting_info')
    def test_slack_command(self, mock_save, mock_analyze, mock_downloader):
        """Probar el comando 'slack'"""
        from src.cli import process_slack_command
        
        # Configurar mocks
        mock_instance = MagicMock()
        mock_instance.fetch_messages.return_value = [
            {"text": "Mensaje 1", "user": "U123", "ts": "1616161616.123456"},
            {"text": "Mensaje 2", "user": "U456", "ts": "1616161617.123456"}
        ]
        mock_downloader.return_value = mock_instance
        
        mock_analyze.return_value = {
            "abstract_summary": "Resumen de prueba",
            "key_points": "Puntos clave de prueba",
            "action_items": "Acciones de prueba",
            "sentiment": "Sentimiento de prueba"
        }
        mock_save.return_value = os.path.join(self.test_dir, "output.docx")
        
        # Ejecutar comando
        args = MagicMock()
        args.token = "test_token"
        args.channel_id = "C123456"
        args.api_key = "test_api_key"
        args.provider = "openai"
        args.model = "gpt-3.5-turbo"
        args.template = "summary"
        args.output = os.path.join(self.test_dir, "output.docx")
        args.start_date = None
        args.end_date = None
        args.limit = 100
        
        process_slack_command(args)
        
        # Verificar que se llamaron las funciones correctas
        mock_downloader.assert_called_once()
        mock_instance.fetch_messages.assert_called_once()
        mock_analyze.assert_called_once()
        mock_save.assert_called_once()
        
    @patch('src.utils.audio_optimizer.AudioOptimizer.optimize_audio')
    def test_optimize_command(self, mock_optimize):
        """Probar el comando 'optimize'"""
        from src.cli import process_optimize_command
        
        # Configurar mock
        optimized_file = os.path.join(self.test_dir, "optimized.mp3")
        mock_optimize.return_value = optimized_file
        
        # Ejecutar comando
        args = MagicMock()
        args.file_path = self.sample_audio
        args.output = optimized_file
        args.bitrate = "32k"
        args.remove_silences = True
        
        process_optimize_command(args)
        
        # Verificar que se llamó la función correcta
        mock_optimize.assert_called_once_with(
            self.sample_audio, 
            optimized_file, 
            target_bitrate="32k", 
            remove_silences=True
        )
        
    def test_audio_optimizer(self):
        """Probar directamente el optimizador de audio"""
        from src.utils.audio_optimizer import AudioOptimizer
        
        # Crear un archivo de audio de prueba más grande
        with open(self.sample_audio, 'wb') as f:
            f.write(b'\x00' * 1024 * 1024)  # 1MB de datos
            
        # Probar la detección de necesidad de optimización
        with patch('src.utils.audio_optimizer.AudioOptimizer.get_audio_info') as mock_info:
            mock_info.return_value = {'bit_rate': '256000'}  # 256kbps
            self.assertTrue(AudioOptimizer.needs_optimization(self.sample_audio, '32k'))
            
        # Probar la obtención del tamaño del archivo
        self.assertAlmostEqual(
            AudioOptimizer.get_file_size_mb(self.sample_audio), 
            1.0,  # 1MB
            delta=0.1
        )
        
    def test_transcription_client(self):
        """Probar el cliente de transcripción"""
        from src.transcription.meeting_transcription import TranscriptionClient
        
        # Crear mock para el proveedor
        mock_provider = MagicMock()
        mock_provider.transcribe.return_value = "Transcripción de prueba"
        
        # Crear cliente con el proveedor mock
        client = TranscriptionClient(provider=mock_provider)
        
        # Probar transcripción
        with open(self.sample_audio, 'rb') as audio_file:
            result = client.transcribe(audio_file, "whisper-1")
            
        # Verificar resultado
        self.assertEqual(result, "Transcripción de prueba")
        mock_provider.transcribe.assert_called_once()
        
    def test_analysis_client(self):
        """Probar el cliente de análisis"""
        from src.transcription.meeting_analyzer import AnalysisClient
        
        # Crear mock para el proveedor
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = "Análisis de prueba"
        
        # Crear cliente con el proveedor mock
        client = AnalysisClient(provider=mock_provider)
        
        # Probar análisis
        messages = [
            {"role": "system", "content": "Eres un asistente útil"},
            {"role": "user", "content": "Analiza este texto"}
        ]
        result = client.analyze(messages)
        
        # Verificar resultado
        self.assertEqual(result, "Análisis de prueba")
        mock_provider.analyze.assert_called_once()
        
    @patch('src.transcription.meeting_analyzer.AnalysisClient')
    def test_meeting_analyzer(self, mock_client_class):
        """Probar el analizador de reuniones"""
        from src.transcription.meeting_analyzer import MeetingAnalyzer
        
        # Configurar mock
        mock_client = MagicMock()
        mock_client.analyze.return_value = "Análisis de prueba"
        mock_client_class.return_value = mock_client
        
        # Crear analizador
        analyzer = MeetingAnalyzer("Transcripción de prueba")
        
        # Probar métodos
        summary = analyzer.summarize()
        key_points = analyzer.extract_key_points()
        action_items = analyzer.extract_action_items()
        sentiment = analyzer.analyze_sentiment()
        
        # Verificar resultados
        self.assertEqual(summary, "Análisis de prueba")
        self.assertEqual(key_points, "Análisis de prueba")
        self.assertEqual(action_items, "Análisis de prueba")
        self.assertEqual(sentiment, "Análisis de prueba")
        
        # Verificar que se llamó al cliente correcto número de veces
        self.assertEqual(mock_client.analyze.call_count, 4)

if __name__ == '__main__':
    unittest.main()
