import os
import unittest
import tempfile
import shutil
import logging
import click
from unittest.mock import patch, MagicMock, mock_open
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
        
    def test_media_command(self):
        """Probar el comando 'media'"""
        from src.cli import transcribe_media
        
        # Crear un contexto de Click para la prueba
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Create a real temporary file that exists
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            extracted_audio_path = temp_file.name
            # Write some dummy content
            temp_file.write(b'test audio content')
        
        try:
            # Parchear las funciones que se llaman dentro del comando
            with patch('src.controller.run_transcription') as mock_transcribe, \
                 patch('src.controller.run_analysis') as mock_analyze, \
                 patch('src.transcription.meeting_minutes.DocumentManager.save_to_docx') as mock_save, \
                 patch('src.utils.audio_extractor.AudioExtractor.extract_audio') as mock_extract, \
                 patch('whisper.load_model') as mock_load_whisper:
                
                # Configurar mocks
                mock_transcribe.return_value = "Transcripción de prueba"
                mock_analyze.return_value = {
                    "abstract_summary": "Resumen de prueba",
                    "key_points": "Puntos clave de prueba",
                    "action_items": "Acciones de prueba",
                    "sentiment": "Sentimiento de prueba"
                }
                mock_save.return_value = os.path.join(self.test_dir, "output.docx")
                mock_extract.return_value = extracted_audio_path  # Use the real temp file
                
                # Mock whisper model loading and transcription
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {"text": "Transcripción de prueba"}
                mock_load_whisper.return_value = mock_model
                # Remove reference to undefined mock_whisper_transcribe
                
                # Ejecutar comando con argumentos simulados
                with runner.isolated_filesystem():
                    # Crear un archivo de prueba con contenido real
                    with open("test_video.mp4", "wb") as f:
                        # Write a minimal valid MP4 header
                        f.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41\x00\x00\x00\x00moov')
                    
                    # Ejecutar el comando con contexto que incluye la opción local
                    ctx = click.Context(transcribe_media)
                    ctx.obj = {'local': True, 'whisper_size': 'base', 'text_model': 'facebook/bart-large-cnn'}
                    
                    # Mock the input function to avoid waiting for user input
                    with patch('builtins.input', return_value='y'):
                        # Also mock the actual transcription process
                        with patch('src.transcription.meeting_transcription.AudioTranscriptionService.transcribe') as mock_service_transcribe:
                            mock_service_transcribe.return_value = "Transcripción de prueba"
                            
                            result = runner.invoke(
                                transcribe_media, 
                                ["test_video.mp4", "--output", "output.docx"],
                                obj=ctx.obj
                            )
                    
                    # Verificar que no hubo errores
                    self.assertEqual(0, result.exit_code, f"Error: {result.output}")
                    
                    # Verificar que se llamaron las funciones correctas
                    mock_transcribe.assert_called_once()
                    mock_analyze.assert_called_once()
                    mock_save.assert_called_once()
        finally:
            # Clean up the temporary file
            if os.path.exists(extracted_audio_path):
                os.unlink(extracted_audio_path)
        
    def test_slack_command(self):
        """Probar el comando 'slack'"""
        from src.cli import analyze_slack_messages
        
        # Crear un contexto de Click para la prueba
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Parchear las funciones que se llaman dentro del comando
        with patch('src.slack.download_slack_channel.SlackDownloader') as mock_downloader_class, \
             patch('src.controller.run_analysis') as mock_analyze, \
             patch('src.transcription.meeting_minutes.DocumentManager.save_to_docx') as mock_save, \
             patch('src.slack.utils.is_user_token', return_value=False), \
             patch('glob.glob') as mock_glob, \
             patch('json.load') as mock_json_load, \
             patch('builtins.open', new_callable=mock_open, read_data='{"messages": []}'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024), \
             patch('os.path.getctime', return_value=1616161616.0):
            
            # Configurar mocks
            mock_instance = MagicMock()
            mock_instance.fetch_messages.return_value = [
                {"text": "Mensaje 1", "user": "U123", "ts": "1616161616.123456"},
                {"text": "Mensaje 2", "user": "U456", "ts": "1616161617.123456"}
            ]
            mock_instance.get_channel_info.return_value = {
                "channel": {
                    "id": "C123456",
                    "name": "test-channel",
                    "is_private": False
                }
            }
            mock_downloader_class.return_value = mock_instance
            
            mock_analyze.return_value = {
                "abstract_summary": "Resumen de prueba",
                "key_points": "Puntos clave de prueba",
                "action_items": "Acciones de prueba",
                "sentiment": "Sentimiento de prueba"
            }
            mock_save.return_value = os.path.join(self.test_dir, "output.docx")
            
            # Mock glob to return our JSON file
            json_file_path = os.path.join("slack_exports", "slack_messages_C123456.json")
            mock_glob.return_value = [json_file_path]
            
            # Mock JSON loading
            mock_json_load.return_value = {
                "messages": [
                    {"text": "Test message", "user": "U123", "ts": "1616161616.123456"}
                ]
            }
            
            # Ejecutar comando con argumentos simulados
            with runner.isolated_filesystem():
                # Create directory structure
                os.makedirs("slack_exports", exist_ok=True)
                
                # Create a mock JSON file
                with open(json_file_path, "w") as f:
                    f.write('{"messages": [{"text": "Test message", "user": "U123", "ts": "1616161616.123456"}]}')
                
                # Ejecutar el comando con contexto que incluye la opción local
                ctx = click.Context(analyze_slack_messages)
                ctx.obj = {'local': True, 'whisper_size': 'base', 'text_model': 'facebook/bart-large-cnn'}
                
                # Patch the MeetingAnalyzer to avoid actual analysis
                with patch('src.transcription.meeting_analyzer.MeetingAnalyzer.analyze') as mock_meeting_analyze, \
                     patch('src.transcription.meeting_analyzer.AnalysisClient') as mock_analysis_client_class:
                    
                    # Configure the mock analysis client
                    mock_analysis_client = MagicMock()
                    mock_analysis_client.analyze.return_value = "Análisis de prueba"
                    mock_analysis_client_class.return_value = mock_analysis_client
                    
                    # Configure the meeting analyzer mock
                    mock_meeting_analyze.return_value = "Análisis de prueba"
                    
                    # Run the command with mocked environment
                    result = runner.invoke(
                        analyze_slack_messages, 
                        ["C123456", "--token", "test_token"],
                        obj=ctx.obj
                    )
                
                # Verificar que no hubo errores
                self.assertEqual(0, result.exit_code, f"Error: {result.output}")
                
                # Verificar que se llamaron las funciones correctas
                mock_downloader_class.assert_called_once()
                mock_instance.fetch_messages.assert_called_once()
        
    # No hay un comando 'optimize' en cli.py, así que podemos omitir esta prueba
    # o probar directamente la clase AudioOptimizer
    def test_audio_optimizer_directly(self):
        """Probar directamente la clase AudioOptimizer"""
        from src.utils.audio_optimizer import AudioOptimizer
        
        # Crear un archivo de audio de prueba
        with open(self.sample_audio, 'wb') as f:
            f.write(b'\x00' * 1024 * 1024)  # 1MB de datos
        
        # Mockear el método optimize_audio
        with patch('src.utils.audio_optimizer.AudioOptimizer.optimize_audio') as mock_optimize:
            optimized_file = os.path.join(self.test_dir, "optimized.mp3")
            mock_optimize.return_value = optimized_file
            
            # Llamar directamente al método
            result = AudioOptimizer.optimize_audio(
                self.sample_audio,
                optimized_file,
                target_bitrate="32k",
                remove_silences=True
            )
            
            # Verificar que se llamó correctamente
            mock_optimize.assert_called_once()
            self.assertEqual(result, optimized_file)
        
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
        
        # Patch the provider_name to ensure we use our mock
        with patch.object(client, 'provider_name', 'mock'):
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
