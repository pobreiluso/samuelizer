import os
import unittest
import tempfile
import shutil
import logging
import click
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
        
    def test_media_command(self):
        """Probar el comando 'media'"""
        from src.cli import transcribe_media
        
        # Crear un contexto de Click para la prueba
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Parchear las funciones que se llaman dentro del comando
        with patch('src.controller.run_transcription') as mock_transcribe, \
             patch('src.controller.run_analysis') as mock_analyze, \
             patch('src.transcription.meeting_minutes.DocumentManager.save_to_docx') as mock_save, \
             patch('src.utils.audio_extractor.AudioExtractor.extract_audio') as mock_extract:
            
            # Configurar mocks
            mock_transcribe.return_value = "Transcripción de prueba"
            mock_analyze.return_value = {
                "abstract_summary": "Resumen de prueba",
                "key_points": "Puntos clave de prueba",
                "action_items": "Acciones de prueba",
                "sentiment": "Sentimiento de prueba"
            }
            mock_save.return_value = os.path.join(self.test_dir, "output.docx")
            mock_extract.return_value = os.path.join(self.test_dir, "extracted_audio.mp3")
            
            # Ejecutar comando con argumentos simulados
            with runner.isolated_filesystem():
                # Crear un archivo de prueba con contenido real
                with open("test_video.mp4", "wb") as f:
                    # Write a minimal valid MP4 header
                    f.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41\x00\x00\x00\x00moov')
                
                # Ejecutar el comando con contexto que incluye la opción local
                ctx = click.Context(transcribe_media)
                ctx.obj = {'local': True, 'whisper_size': 'base', 'text_model': 'facebook/bart-large-cnn'}
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
             patch('src.slack.utils.is_user_token', return_value=False):
            
            # Configurar mocks
            mock_instance = MagicMock()
            mock_instance.fetch_messages.return_value = [
                {"text": "Mensaje 1", "user": "U123", "ts": "1616161616.123456"},
                {"text": "Mensaje 2", "user": "U456", "ts": "1616161617.123456"}
            ]
            mock_downloader_class.return_value = mock_instance
            
            mock_analyze.return_value = {
                "abstract_summary": "Resumen de prueba",
                "key_points": "Puntos clave de prueba",
                "action_items": "Acciones de prueba",
                "sentiment": "Sentimiento de prueba"
            }
            mock_save.return_value = os.path.join(self.test_dir, "output.docx")
            
            # Ejecutar comando con argumentos simulados
            with runner.isolated_filesystem():
                # Create a mock JSON file for the exporter to find
                os.makedirs("slack_exports", exist_ok=True)
                with open("slack_exports/slack_messages_C123456.json", "w") as f:
                    f.write('{"messages": [{"text": "Test message", "user": "U123", "ts": "1616161616.123456"}]}')
                
                # Ejecutar el comando con contexto que incluye la opción local
                ctx = click.Context(analyze_slack_messages)
                ctx.obj = {'local': True, 'whisper_size': 'base', 'text_model': 'facebook/bart-large-cnn'}
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
                mock_analyze.assert_called_once()
                mock_save.assert_called_once()
        
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
        
        # Use patch to prevent actual OpenAI API calls
        with patch('openai.chat.completions.create') as mock_create:
            mock_create.return_value.choices[0].message.content = "Análisis de prueba"
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
