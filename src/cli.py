import sys
import logging
import glob
import click
import os
import json
import openai
import time
from typing import Optional
from tqdm import tqdm
from src.transcription.meeting_minutes import (
    AudioTranscriptionService,
    MeetingAnalyzer, 
    DocumentManager,
    VideoDownloader
)
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.slack.http_client import RequestsClient
from src.slack.pagination import SlackPaginator
from src.slack.user_cache import SlackUserCache
from src.slack.filters import SlackMessageFilter
from src.slack.exceptions import SlackAPIError, SlackRateLimitError
from src.exporters.json_exporter import JSONExporter
from src.transcription.exceptions import MeetingMinutesError
from src.utils.audio_extractor import AudioExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cli_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@click.group()
@click.option('--local', is_flag=True, help='Use local models instead of API-based ones')
@click.option('--offline', is_flag=True, help='Alias for --local, process completely offline')
@click.option('--whisper-size', default='base', help='Whisper model size when using --local/--offline')
@click.option('--text-model', default='facebook/bart-large-cnn', help='Text model when using --local/--offline')
@click.pass_context
def cli(ctx, local, offline, whisper_size, text_model):
    """Samuelizer - AI-powered summarization tool."""
    # Guardar las opciones en el contexto para que estén disponibles en todos los comandos
    ctx.ensure_object(dict)
    ctx.obj['local'] = local or offline
    ctx.obj['whisper_size'] = whisper_size
    ctx.obj['text_model'] = text_model
    pass

@cli.command('media')
@click.argument('file_path')
@click.option('--api_key', help='API key for the selected provider.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--drive_url', required=False, help='Google Drive URL to download media file.')
@click.option('--optimize', default='128k', help='Target bitrate for audio optimization (e.g. 32k, 64k, 128k)')
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use (summary, executive, quick)')
@click.option('--diarization', is_flag=True, help='Enable speaker diarization')
@click.option('--no-cache', is_flag=True, help='Disable transcription caching')
@click.option('--provider', default='openai', help='AI provider to use (e.g., openai, local)')
@click.option('--model', default='whisper-1', help='Model ID to use for transcription')
@click.option('--keep-silence', is_flag=True, help='Do not remove long silences from audio')
@click.option('--max-size', default=100, help='Maximum audio file size in MB before applying more aggressive optimization')
@click.pass_context
def transcribe_media(ctx, file_path, api_key, drive_url, optimize, output, template, diarization, no_cache, provider, model, keep_silence, max_size):
    # Obtener las opciones globales del contexto
    local = ctx.obj.get('local', False)
    whisper_size = ctx.obj.get('whisper_size', 'base')
    text_model = ctx.obj.get('text_model', 'facebook/bart-large-cnn')
    
    # Si se especifica --local, usar el proveedor local
    if local:
        provider = "local"
        model = whisper_size
        # No se necesita API key para modelos locales
        api_key = None
        logger.info("Usando modelos locales para procesamiento (modo offline)")
    elif not api_key and provider == "openai":
        api_key = click.prompt('OpenAI API key', hide_input=True)
    
    # Expandir la ruta del usuario
    file_path = os.path.expanduser(file_path)
    
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        sys.exit(1)
    """
    Summarize and analyze any media file (video or audio).

    FILE_PATH: Path to media file
    Supported formats: mp4, avi, mkv, mov, wmv, flv, webm, mp3, wav, m4a, aac, ogg
    
    The file will be:
    1. Optimized for processing (if needed)
    2. Transcribed to text
    3. Analyzed to extract:
       - Abstract summary
       - Key points
       - Action items
       - Sentiment analysis
    """
    supported_formats = AudioExtractor.get_supported_formats()
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext not in supported_formats:
        logger.error(f"Unsupported file format. Supported formats: {', '.join(supported_formats)}")
        sys.exit(1)
    try:
        # Configurar el proveedor de IA
        if provider.lower() == 'openai':
            if not api_key:
                logger.error("OpenAI API key not provided")
                sys.exit(1)
            os.environ["OPENAI_API_KEY"] = api_key
            if hasattr(openai, 'api_key'):
                openai.api_key = api_key
            
        if drive_url:
            video_file = VideoDownloader.download_from_google_drive(drive_url)
            file_path = video_file

        # Check if file is already MP3
        if file_path.lower().endswith('.mp3'):
            audio_file = file_path
        else:
            # Extract audio from video and optimize it
            from src.utils.audio_optimizer import AudioOptimizer
            
            audio_file = AudioExtractor.extract_audio(
                file_path, 
                target_bitrate=optimize,
                remove_silences=not keep_silence,
                max_size_mb=max_size
            )
        
        # Transcribe audio
        logger.info(f"Starting file transcription: {audio_file}")
        try:
            # Pass the no_cache flag and provider info to the transcription service
            use_cache = not no_cache
            
            # Importar las clases necesarias
            from src.transcription.meeting_transcription import TranscriptionClient, AudioTranscriptionService
            from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
            
            # Crear el cliente de transcripción con el proveedor seleccionado
            transcription_client = TranscriptionClient(
                provider_name=provider,
                api_key=api_key
            )
            
            # Configurar el servicio de transcripción
            service = AudioTranscriptionService(
                transcription_client=transcription_client,
                diarization_service=SpeakerDiarization(),
                audio_file_handler=AudioFileHandler(),
                file_writer=TranscriptionFileWriter(),
                model_id=model,
                provider_name=provider,
                api_key=api_key
            )
            
            transcription = service.transcribe(
                audio_file, 
                diarization=diarization, 
                use_cache=use_cache
            )
            logger.info(f"Transcription completed. Text length: {len(transcription)} characters")
            
            # Save transcription to a text file if not already done by the service
            output_txt = os.path.splitext(audio_file)[0] + "_transcription.txt"
            if not os.path.exists(output_txt):
                with open(output_txt, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                logger.info(f"Transcription saved to: {output_txt}")
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise
        
        # Crear el cliente de análisis con el proveedor seleccionado
        from src.transcription.meeting_analyzer import AnalysisClient
        analysis_client = AnalysisClient(
            provider_name=provider,
            api_key=api_key,
            model_id=model
        )
        
        analyzer = MeetingAnalyzer(
            transcription=transcription,
            analysis_client=analysis_client
        )
        
        if template == 'all':
            meeting_info = {}
            with tqdm(total=4, desc="Analyzing content", unit="task") as pbar:
                meeting_info['abstract_summary'] = analyzer.summarize()
                pbar.update(1)
                meeting_info['key_points'] = analyzer.extract_key_points()
                pbar.update(1)
                meeting_info['action_items'] = analyzer.extract_action_items()
                pbar.update(1)
                meeting_info['sentiment'] = analyzer.analyze_sentiment()
                pbar.update(1)
        else:
            result = analyzer.analyze(template)
            meeting_info = {template: result}

        # Display results in CLI
        click.echo("\n=== Samuelization Summary ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Save to docx if requested
        if output:
            DocumentManager.save_to_docx(meeting_info, output)
            logger.info(f"Document saved: {output}")

    except MeetingMinutesError as e:
        logger.error(f"Error transcribing video: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@cli.command('text')
@click.argument('text')
@click.option('--api_key', help='OpenAI API key.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use')
@click.option('--params', help='Additional template parameters in JSON format')
@click.option('--provider', default='openai', help='AI provider to use (e.g., openai, local)')
@click.option('--model', default='gpt-4', help='Model ID to use for analysis')
@click.pass_context
def summarize_text_command(ctx, text, api_key, output, template, params, provider, model):
    # Obtener las opciones globales del contexto
    local = ctx.obj.get('local', False)
    text_model = ctx.obj.get('text_model', 'facebook/bart-large-cnn')
    
    # Si se especifica --local, usar el proveedor local
    if local:
        provider = "local"
        model = text_model
        # No se necesita API key para modelos locales
        api_key = None
        logger.info("Usando modelos locales para procesamiento (modo offline)")
    elif not api_key and provider == "openai" and not list_channels:
        api_key = click.prompt('OpenAI API key', hide_input=True)
    
    # Verificar que se proporcionó un token de Slack
    if not token:
        token = click.prompt('Slack Token', hide_input=True)
    
    # Manejar el comando --list-channels
    if list_channels:
        try:
            from src.slack.channel_lister import SlackChannelLister
            from src.slack.http_client import RequestsClient
            
            # Crear el cliente HTTP y el listador de canales
            http_client = RequestsClient()
            channel_lister = SlackChannelLister(token, http_client)
            
            # Obtener la lista de canales
            logging.info("Obteniendo lista de canales de Slack...")
            channels = channel_lister.list_channels(
                include_private=include_private,
                include_archived=include_archived
            )
            
            # Enriquecer la información de los canales
            enriched_channels = channel_lister.get_channel_details(channels)
            
            # Formatear para mostrar
            formatted_text = channel_lister.format_channels_for_display(enriched_channels)
            
            # Mostrar en la consola
            click.echo(formatted_text)
            
            # Guardar en archivo si se especificó
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(formatted_text)
                logging.info(f"Resultados guardados en: {output}")
                
                # También guardar versión JSON para uso programático
                import json
                json_output = f"{os.path.splitext(output)[0]}.json"
                with open(json_output, 'w', encoding='utf-8') as f:
                    json.dump(enriched_channels, f, ensure_ascii=False, indent=2)
                logging.info(f"Datos JSON guardados en: {json_output}")
            
            return
            
        except Exception as e:
            logging.error(f"Error al listar canales de Slack: {str(e)}")
            sys.exit(1)
    
    # Manejar el comando --summary
    elif summary:
        if not start_date or not end_date:
            logger.error("Para generar un resumen global se requieren --start-date y --end-date")
            sys.exit(1)
            
        try:
            # Importar las clases necesarias
            from src.slack.channel_lister import SlackChannelLister
            from src.slack.http_client import RequestsClient
            from src.slack.download_slack_channel import SlackDownloader, SlackConfig
            from src.slack.filters import SlackMessageFilter
            from src.exporters.json_exporter import JSONExporter
            from src.transcription.meeting_analyzer import AnalysisClient, MeetingAnalyzer
            from src.transcription.templates import PromptTemplates
            
            # Configurar el proveedor de IA
            if provider.lower() == 'openai':
                if not api_key:
                    logger.error("OpenAI API key not provided")
                    sys.exit(1)
                os.environ["OPENAI_API_KEY"] = api_key
                if hasattr(openai, 'api_key'):
                    openai.api_key = api_key
            
            # Crear el cliente HTTP
            http_client = RequestsClient()
            
            # Paso 1: Listar todos los canales accesibles
            logger.info("Obteniendo lista de canales de Slack...")
            channel_lister = SlackChannelLister(token, http_client)
            channels = channel_lister.list_channels(include_private=include_private, include_archived=False)
            
            # Enriquecer la información de los canales
            enriched_channels = channel_lister.get_channel_details(channels)
            
            # Filtrar solo canales donde el bot es miembro
            member_channels = [c for c in enriched_channels if c.get('is_member', False)]
            
            # Limitar el número de canales si se especificó
            if max_channels > 0 and len(member_channels) > max_channels:
                logger.info(f"Limitando análisis a {max_channels} canales (de {len(member_channels)} disponibles)")
                member_channels = member_channels[:max_channels]
            
            logger.info(f"Analizando {len(member_channels)} canales en el rango de fechas: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            
            # Crear directorio de salida si no existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Paso 2: Descargar mensajes de todos los canales en el rango de fechas
            all_messages = []
            channel_messages = {}
            exporter = JSONExporter()
            
            with click.progressbar(member_channels, label='Descargando mensajes de canales') as channels_bar:
                for channel in channels_bar:
                    channel_id = channel['id']
                    channel_name = channel['name']
                    
                    # Configuración para este canal
                    slack_config = SlackConfig(
                        token=token,
                        channel_id=channel_id,
                        start_date=start_date,
                        end_date=end_date,
                        output_dir=output_dir
                    )
                    
                    # Crear el descargador
                    downloader = SlackDownloader(slack_config, http_client)
                    
                    try:
                        # Descargar mensajes
                        messages = downloader.fetch_messages()
                        
                        # Filtrar por fecha
                        messages = SlackMessageFilter.by_date_range(messages, start_date, end_date)
                        
                        # Solo incluir canales con suficientes mensajes
                        if len(messages) >= min_messages:
                            # Añadir información del canal a cada mensaje
                            for msg in messages:
                                msg['_channel_id'] = channel_id
                                msg['_channel_name'] = channel_name
                            
                            # Guardar mensajes
                            all_messages.extend(messages)
                            channel_messages[channel_id] = {
                                'name': channel_name,
                                'message_count': len(messages),
                                'messages': messages
                            }
                            
                            # Exportar mensajes de este canal
                            exporter.export_messages(
                                messages,
                                channel_id,
                                output_dir,
                                start_date=start_date,
                                end_date=end_date
                            )
                            
                            logger.info(f"Canal {channel_name} ({channel_id}): {len(messages)} mensajes")
                        else:
                            logger.info(f"Canal {channel_name} ({channel_id}): solo {len(messages)} mensajes (mínimo: {min_messages})")
                            
                    except Exception as e:
                        logger.warning(f"Error al descargar mensajes del canal {channel_name} ({channel_id}): {str(e)}")
            
            if not all_messages:
                logger.error("No se encontraron mensajes en el rango de fechas especificado.")
                sys.exit(1)
                
            logger.info(f"Total de mensajes descargados: {len(all_messages)}")
            
            # Paso 3: Preparar datos para análisis
            
            # Ordenar todos los mensajes por timestamp
            all_messages.sort(key=lambda x: float(x.get('ts', 0)))
            
            # Exportar todos los mensajes juntos
            combined_output = os.path.join(output_dir, f"slack_global_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json")
            with open(combined_output, 'w', encoding='utf-8') as f:
                json.dump({
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'channel_count': len(channel_messages),
                    'message_count': len(all_messages),
                    'channels': channel_messages
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Datos combinados guardados en: {combined_output}")
            
            # Paso 4: Analizar mensajes
            
            # Crear cliente de análisis
            analysis_client = AnalysisClient(
                provider_name=provider,
                api_key=api_key,
                model_id=model
            )
            
            # Registrar plantilla personalizada para resumen global
            templates = PromptTemplates()
            if not hasattr(templates, 'templates') or 'global_summary' not in templates.templates:
                templates.add_custom_template('global_summary', {
                    'system': """Eres un asistente especializado en analizar conversaciones de Slack y generar resúmenes ejecutivos detallados. 
                    Tu tarea es identificar temas importantes, patrones de comunicación, interdependencias entre canales y extraer información clave.""",
                    'template': """
                    Analiza las siguientes conversaciones de Slack que ocurrieron entre {start_date} y {end_date} en {channel_count} canales diferentes.
                    
                    Tu objetivo es crear un resumen global que:
                    1. Identifique los temas principales discutidos en todos los canales
                    2. Destaque las conversaciones más importantes y sus conclusiones
                    3. Identifique patrones de comunicación entre canales (temas que aparecen en múltiples canales)
                    4. Reconozca a los participantes clave y sus contribuciones principales
                    5. Extraiga decisiones importantes y elementos de acción
                    6. Identifique cualquier problema o desafío recurrente
                    
                    Organiza tu resumen en estas secciones:
                    - RESUMEN EJECUTIVO: Una visión general concisa de toda la actividad
                    - TEMAS PRINCIPALES: Los temas más discutidos y su importancia
                    - DECISIONES CLAVE: Decisiones importantes tomadas durante este período
                    - ELEMENTOS DE ACCIÓN: Tareas y responsabilidades asignadas
                    - PROBLEMAS Y DESAFÍOS: Problemas identificados que requieren atención
                    - PARTICIPANTES DESTACADOS: Personas que tuvieron contribuciones significativas
                    - ANÁLISIS DE CANALES: Breve resumen de la actividad en cada canal principal
                    
                    Conversaciones a analizar:
                    
                    {text}
                    """,
                    'parameters': {
                        'max_length': 2000,
                        'style': 'executive',
                        'format': 'structured'
                    }
                })
            
            # Preparar texto para análisis
            # Limitamos a un número manejable de mensajes para evitar exceder límites de tokens
            max_messages_for_analysis = 1000
            if len(all_messages) > max_messages_for_analysis:
                logger.warning(f"Limitando análisis a {max_messages_for_analysis} mensajes (de {len(all_messages)} totales)")
                # Seleccionar mensajes distribuidos uniformemente
                step = len(all_messages) // max_messages_for_analysis
                selected_messages = all_messages[::step]
            else:
                selected_messages = all_messages
            
            # Formatear mensajes para análisis
            formatted_messages = []
            for msg in selected_messages:
                channel_name = msg.get('_channel_name', 'desconocido')
                user_name = msg.get('user_info', msg.get('user', 'desconocido'))
                text = msg.get('text', '')
                ts = float(msg.get('ts', 0))
                date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
                
                formatted_msg = f"[{date_str}] #{channel_name} - {user_name}: {text}"
                formatted_messages.append(formatted_msg)
            
            analysis_text = "\n".join(formatted_messages)
            
            # Crear analizador
            analyzer = MeetingAnalyzer(
                transcription=analysis_text,
                analysis_client=analysis_client
            )
            
            # Realizar análisis con parámetros adicionales
            template_params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'channel_count': len(channel_messages)
            }
            
            logger.info("Generando resumen global...")
            result = analyzer.analyze('global_summary', **template_params)
            
            # Mostrar resultados
            click.echo("\n=== Resumen Global de Slack ===")
            click.echo(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            click.echo(f"Canales analizados: {len(channel_messages)}")
            click.echo(f"Total de mensajes: {len(all_messages)}")
            click.echo("\n" + result)
            
            # Guardar resultados en DOCX si se solicitó
            if output:
                from src.transcription.meeting_minutes import DocumentManager
                DocumentManager.save_to_docx({'global_summary': result}, output)
                logger.info(f"Resumen guardado en: {output}")
            
            return
            
        except KeyboardInterrupt:
            logger.info("Proceso interrumpido por el usuario.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    # Comportamiento normal del comando slack (análisis de un canal específico)
    else:
        if not channel_id_or_link:
            logger.error("Se requiere un ID de canal o enlace para analizar mensajes de Slack")
            sys.exit(1)
    """
    Analyze and summarize a text.

    TEXT: Text to analyze
    
    The text will be analyzed to extract:
    - Abstract summary
    - Key points
    - Action items
    - Sentiment analysis
    """
    try:
        # Configurar el proveedor de IA
        if provider.lower() == 'openai':
            if not api_key:
                logger.error("OpenAI API key not provided")
                sys.exit(1)
            os.environ["OPENAI_API_KEY"] = api_key
            if hasattr(openai, 'api_key'):
                openai.api_key = api_key
                
        template_params = json.loads(params) if params else {}
        
        # Crear el cliente de análisis con el proveedor seleccionado
        from src.transcription.meeting_analyzer import AnalysisClient
        analysis_client = AnalysisClient(
            provider_name=provider,
            api_key=api_key,
            model_id=model
        )
        
        analyzer = MeetingAnalyzer(
            transcription=text,
            analysis_client=analysis_client
        )
        
        if template == 'all':
            meeting_info = {
                'abstract_summary': analyzer.summarize(**template_params),
                'key_points': analyzer.extract_key_points(**template_params),
                'action_items': analyzer.extract_action_items(**template_params),
                'sentiment': analyzer.analyze_sentiment(**template_params)
            }
        else:
            result = analyzer.analyze(template, **template_params)
            meeting_info = {template: result}

        # Display results in CLI
        click.echo("\n=== Text Summary ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Save to docx if requested
        if output:
            DocumentManager.save_to_docx(meeting_info, output)
            logger.info(f"Document saved: {output}")
    except MeetingMinutesError as e:
        logger.error(f"Error summarizing text: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI Authentication Error: {e}")
        sys.exit(1)
    except openai.APIError as e:
        logger.error(f"OpenAI API Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@cli.command('slack')
@click.argument('channel_id_or_link', required=False)
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date in YYYY-MM-DD format')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date in YYYY-MM-DD format')
@click.option('--output-dir', default='slack_exports', help='Directory to save messages')
@click.option('--token', help='Slack token. Can also use SLACK_TOKEN env var', default=lambda: os.environ.get('SLACK_TOKEN', None))
@click.option('--thread-ts', help='Thread timestamp to fetch replies from a specific thread')
@click.option('--user-id', help='Filter messages by user ID')
@click.option('--only-threads', is_flag=True, help='Only fetch messages that have replies')
@click.option('--with-reactions', is_flag=True, help='Only fetch messages that have reactions')
@click.option('--api_key', help='OpenAI API key.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use (summary, executive, quick)')
@click.option('--provider', default='openai', help='AI provider to use (e.g., openai, local)')
@click.option('--model', default='gpt-4', help='Model ID to use for analysis')
@click.option('--summary', is_flag=True, help='Generate a global summary of all Slack activity in a date range')
@click.option('--list-channels', is_flag=True, help='List all Slack channels accessible with the provided token')
@click.option('--include-private/--public-only', default=True, help='Include private channels and DMs')
@click.option('--include-archived/--active-only', default=False, help='Include archived channels')
@click.option('--max-channels', default=0, type=int, help='Maximum number of channels to analyze (0 for all)')
@click.option('--min-messages', default=5, type=int, help='Minimum number of messages in a channel to include it')
@click.pass_context
def analyze_slack_messages(ctx, channel_id_or_link, start_date, end_date, output_dir, token, api_key, output, template, provider, model, 
                          thread_ts, user_id, only_threads, with_reactions, summary, list_channels, include_private, include_archived,
                          max_channels, min_messages):
    # Obtener las opciones globales del contexto
    local = ctx.obj.get('local', False)
    text_model = ctx.obj.get('text_model', 'facebook/bart-large-cnn')
    
    # Si se especifica --local, usar el proveedor local
    if local:
        provider = "local"
        model = text_model
        # No se necesita API key para modelos locales
        api_key = None
        logger.info("Usando modelos locales para procesamiento (modo offline)")
    elif not api_key and provider == "openai":
        api_key = click.prompt('OpenAI API key', hide_input=True)
    """
    Analyze and summarize a Slack channel or thread.

    CHANNEL_ID_OR_LINK: Slack channel ID (e.g., C01234567) or a Slack message link
    
    You can use:
    1. Channel ID (e.g., C01234567)
    2. Slack link to a channel (https://workspace.slack.com/archives/C01234567)
    3. Slack link to a message or thread (https://workspace.slack.com/archives/C01234567/p1234567890123456)
    
    The channel messages will be:
    1. Downloaded and saved as JSON
    2. Analyzed to extract:
       - Abstract summary
       - Key points
       - Action items
       - Sentiment analysis
    3. Results saved as DOCX
    
    Required:
    - SLACK_TOKEN or --token: Slack Bot User OAuth Token
    - OPENAI_API_KEY or --api_key: OpenAI API key
    """
    try:
        # Importar la función para parsear enlaces de Slack
        from src.slack.utils import parse_slack_link
        
        # Verificar si es un enlace de Slack o un ID de canal
        if channel_id_or_link.startswith('http'):
            # Es un enlace de Slack, extraer el ID del canal y posiblemente el timestamp
            channel_id, link_thread_ts = parse_slack_link(channel_id_or_link)
            if not channel_id:
                logging.error("Enlace de Slack inválido. No se pudo extraer el ID del canal.")
                sys.exit(1)
            
            # Si se encontró un timestamp en el enlace y no se especificó --thread-ts, usarlo
            if link_thread_ts and not thread_ts:
                thread_ts = link_thread_ts
                logging.info(f"Usando timestamp del enlace: {thread_ts}")
        else:
            # Es un ID de canal directamente
            channel_id = channel_id_or_link
        
        # Create configuration
        slack_config = SlackConfig(
            token=token,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_dir
        )
        
        # Create services with dependency injection
        http_client = RequestsClient()
        downloader = SlackDownloader(slack_config, http_client)
        exporter = JSONExporter()
        
        try:
            # Download messages
            if thread_ts:
                messages = downloader.fetch_thread_messages(thread_ts)
                logging.info(f"Downloaded {len(messages)} messages from thread {thread_ts}")
            else:
                messages = downloader.fetch_messages()
                logging.info(f"Downloaded {len(messages)} messages from channel {channel_id}")
            
            # Apply filters if specified
            if user_id:
                messages = SlackMessageFilter.by_user(messages, user_id)
                logging.info(f"Filtered to {len(messages)} messages from user {user_id}")
            
            if only_threads:
                messages = SlackMessageFilter.by_has_replies(messages)
                logging.info(f"Filtered to {len(messages)} messages with thread replies")
            
            if with_reactions:
                messages = SlackMessageFilter.by_has_reactions(messages)
                logging.info(f"Filtered to {len(messages)} messages with reactions")
            
            # Apply date filters if specified
            if start_date or end_date:
                messages = SlackMessageFilter.by_date_range(messages, start_date, end_date)
        
            # Export messages to JSON
            output_file = exporter.export_messages(
                messages,
                slack_config.channel_id,
                slack_config.output_dir,
                start_date=slack_config.start_date,
                end_date=slack_config.end_date
            )
        except SlackRateLimitError as e:
            logging.error(f"Rate limit exceeded: {e}")
            logging.info(f"Waiting {e.retry_after} seconds before retrying...")
            time.sleep(e.retry_after or 60)
            messages = downloader.fetch_messages()
            
            # Export messages to JSON
            output_file = exporter.export_messages(
                messages,
                slack_config.channel_id,
                slack_config.output_dir,
                start_date=slack_config.start_date,
                end_date=slack_config.end_date
            )
        except SlackAPIError as e:
            logging.error(f"Slack API error: {e}")
            sys.exit(1)
        
        # Find the latest JSON file
        json_files = glob.glob(os.path.join(output_dir, f"slack_messages_{channel_id}*.json"))
        if not json_files:
            logging.error("No JSON message files found.")
            sys.exit(1)
        
        latest_file = max(json_files, key=os.path.getctime)
        logging.info(f"Latest message file: {latest_file}")
        
        # Load messages from the JSON file
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        if not messages:
            logging.info("No messages to summarize.")
            sys.exit(0)
        
        # Prepare text for analysis
        transcription_text = "\n".join([msg.get('text', '') for msg in messages])
        
        # Configurar el proveedor de IA
        if provider.lower() == 'openai':
            if not api_key:
                logger.error("OpenAI API key not provided")
                sys.exit(1)
            os.environ["OPENAI_API_KEY"] = api_key
            if hasattr(openai, 'api_key'):
                openai.api_key = api_key
        
        # Crear el cliente de análisis con el proveedor seleccionado
        from src.transcription.meeting_analyzer import AnalysisClient
        analysis_client = AnalysisClient(
            provider_name=provider,
            api_key=api_key
        )
        
        # Analyze the messages
        analyzer = MeetingAnalyzer(
            transcription=transcription_text,
            analysis_client=analysis_client
        )
        
        if template == 'all':
            result = analyzer.analyze('default')
            meeting_info = {'default': result}
        else:
            result = analyzer.analyze(template)
            meeting_info = {template: result}
        
        # Display results in CLI
        click.echo("\n=== Slack Channel Summary ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Save to docx if requested
        if output:
            DocumentManager.save_to_docx(meeting_info, output)
            logger.info(f"Document saved: {output}")
    
    except MeetingMinutesError as e:
        logging.error(f"Error processing Slack messages: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error while summarizing Slack messages: {e}")
        sys.exit(1)

@cli.command('listen')
@click.option('--duration', type=int, help='Duration in seconds (0 for continuous)', default=0)
@click.option('--output-dir', default='recordings', help='Directory to save recordings')
@click.option('--api_key', help='API key for the selected provider.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use (summary, executive, quick)')
@click.option('--no-cache', is_flag=True, help='Disable transcription caching')
@click.option('--provider', default='openai', help='AI provider to use (e.g., openai)')
@click.option('--model', default='whisper-1', help='Model ID to use for transcription')
@click.option('--keep-silence', is_flag=True, help='Do not remove long silences from audio')
@click.option('--optimize', default='128k', help='Target bitrate for audio optimization (e.g. 32k, 64k, 128k)')
@click.option('--max-size', default=100, help='Maximum audio file size in MB before applying more aggressive optimization')
@click.pass_context
def listen_command(ctx, duration, output_dir, api_key, output, template, no_cache, provider, model, keep_silence, optimize, max_size):
    # Obtener las opciones globales del contexto
    local = ctx.obj.get('local', False)
    whisper_size = ctx.obj.get('whisper_size', 'base')
    
    # Si se especifica --local, usar el proveedor local
    if local:
        provider = "local"
        model = whisper_size
        # No se necesita API key para modelos locales
        api_key = None
        logger.info("Usando modelos locales para procesamiento (modo offline)")
    elif not api_key and provider == "openai":
        api_key = click.prompt('OpenAI API key', hide_input=True)
    """
    Listen and transcribe system audio in real-time.
    
    This will capture all system audio, including:
    - Video calls (Google Meet, Teams, Zoom)
    - System sounds
    - Microphone input
    - Audio from headphones
    """
    try:
        from src.audio_capture.system_audio import SystemAudioCapture
        
        recorder = SystemAudioCapture()
        recorder.start_recording(output_dir)
        
        if duration > 0:
            click.echo(f"Recording for {duration} seconds...")
            time.sleep(duration)
        else:
            click.echo("Recording... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        click.echo("\nStopping recording...")
        audio_file = recorder.stop_recording()
        
        if api_key:
            click.echo("Transcribing recorded audio...")
            # Importar las clases necesarias aquí para asegurar que estén disponibles
            from src.transcription.meeting_transcription import TranscriptionClient, AudioTranscriptionService
            from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
            
            ctx = click.get_current_context()
            ctx.invoke(transcribe_media, 
                      file_path=audio_file,
                      api_key=api_key,
                      drive_url=None,
                      optimize=optimize,
                      output=output,
                      template=template,
                      diarization=False,
                      no_cache=no_cache,
                      provider=provider,
                      model=model,
                      keep_silence=keep_silence,
                      max_size=max_size)
        else:
            click.echo(f"Audio saved to: {audio_file}")
            
    except Exception as e:
        logger.error(f"Error during recording: {e}")
        sys.exit(1)

@cli.command()
def version():
    """Displays the CLI agent version."""
    click.echo("samuelizer version 1.1.0")
    
@cli.command('providers')
def list_providers():
    """Lists available AI providers and their models."""
    from src.config.providers import get_available_providers
    
    providers = get_available_providers()
    
    click.echo("\n=== Available AI Providers ===")
    for provider_id, provider_info in providers.items():
        click.echo(f"\n{provider_info['name']} ({provider_id}):")
        click.echo(f"  Description: {provider_info['description']}")
        click.echo(f"  Environment variable: {provider_info['env_var']}")
        
        click.echo("\n  Transcription models:")
        for model in provider_info['transcription_models']:
            default = " (default)" if model == provider_info.get('default_transcription_model') else ""
            click.echo(f"    - {model}{default}")
            
        click.echo("\n  Analysis models:")
        for model in provider_info['analysis_models']:
            default = " (default)" if model == provider_info.get('default_analysis_model') else ""
            click.echo(f"    - {model}{default}")

@cli.command('clear-cache')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clear_cache(confirm):
    """
    Clear all cached transcriptions.
    
    This command removes all cached transcriptions to ensure fresh results
    on subsequent transcription requests.
    """
    if not confirm:
        if not click.confirm('¿Estás seguro de que quieres borrar toda la caché de transcripciones?'):
            click.echo("Operación cancelada.")
            return
    
    try:
        from src.transcription.cache import FileCache, TranscriptionCacheService
        
        # Crear el servicio de caché
        file_cache = FileCache()
        cache_service = TranscriptionCacheService(file_cache)
        
        # Limpiar toda la caché
        cache_service.clear_all_cache()
        
        click.echo("Caché de transcripciones borrada correctamente.")
    except Exception as e:
        logger.error(f"Error al limpiar la caché: {e}")
        sys.exit(1)






if __name__ == '__main__':
    try:
        cli(obj={})
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}")
        sys.exit(1)
