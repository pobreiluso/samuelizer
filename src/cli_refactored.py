"""
Refactored CLI with improved structure and service layer separation.
This demonstrates the refactoring improvements while maintaining backward compatibility.
"""
import sys
import os
import click
from pathlib import Path

from src.config.command_configs import (
    MediaTranscriptionConfig,
    TextAnalysisConfig,
    SlackAnalysisConfig,
    AudioCaptureConfig
)
from src.config.provider_manager import ProviderConfigurationManager
from src.services.media_service import MediaTranscriptionService
from src.services.text_service import TextAnalysisService
from src.services.slack_service import SlackAnalysisService
from src.utils.error_handlers import handle_common_cli_errors, handle_slack_errors
from src.utils.logging_utils import setup_logging

# Configure logging
logger = setup_logging('cli_agent.log')


@click.group()
@click.option('--local', is_flag=True, help='Use local models instead of API-based ones')
@click.option('--offline', is_flag=True, help='Alias for --local, process completely offline')
@click.option('--whisper-size', default='base', help='Whisper model size when using --local/--offline')
@click.option('--text-model', default='facebook/bart-large-cnn', help='Text model when using --local/--offline')
@click.pass_context
def cli(ctx, local, offline, whisper_size, text_model):
    """Samuelizer - AI-powered summarization tool."""
    ctx.ensure_object(dict)
    ctx.obj['local'] = local or offline
    ctx.obj['whisper_size'] = whisper_size
    ctx.obj['text_model'] = text_model


@cli.command('media')
@click.argument('file_path')
@click.option('--api_key', help='API key for the selected provider.', 
              default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--drive_url', help='Google Drive URL to download media file.')
@click.option('--optimize', default='128k', help='Target bitrate for audio optimization')
@click.option('--output', help='Save results to a DOCX file', type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use')
@click.option('--diarization', is_flag=True, help='Enable speaker diarization')
@click.option('--no-cache', is_flag=True, help='Disable transcription caching')
@click.option('--provider', default='openai', help='AI provider to use')
@click.option('--model', default='whisper-1', help='Model ID to use for transcription')
@click.option('--keep-silence', is_flag=True, help='Do not remove long silences from audio')
@click.option('--max-size', default=100, help='Maximum audio file size in MB')
@click.option('--output-audio', help='Save optimized audio to a specific file', type=click.Path())
@click.pass_context
@handle_common_cli_errors
def transcribe_media(ctx, file_path, api_key, drive_url, optimize, output, template, 
                    diarization, no_cache, provider, model, keep_silence, max_size, output_audio):
    """
    Summarize and analyze any media file (video or audio).
    
    FILE_PATH: Path to media file
    Supported formats: mp4, avi, mkv, mov, wmv, flv, webm, mp3, wav, m4a, aac, ogg
    """
    # Create configuration object
    config = MediaTranscriptionConfig(
        file_path=file_path,
        drive_url=drive_url,
        optimize=optimize,
        output=Path(output) if output else None,
        template=template,
        diarization=diarization,
        no_cache=no_cache,
        provider=provider,
        model=model,
        api_key=api_key,
        keep_silence=keep_silence,
        max_size=max_size,
        output_audio=Path(output_audio) if output_audio else None
    )
    
    # Configure provider
    provider_config = ProviderConfigurationManager.configure_provider(
        ctx, config.provider, config.api_key, config.model
    )
    
    # Process media file using service
    service = MediaTranscriptionService(config)
    results = service.process_media_file(provider_config)
    
    # Display results
    _display_analysis_results(results, "Samuelization Summary")


@cli.command('text')
@click.argument('text')
@click.option('--api_key', help='OpenAI API key.', 
              default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use')
@click.option('--params', help='Additional template parameters in JSON format')
@click.option('--provider', default='openai', help='AI provider to use')
@click.option('--model', default='gpt-4', help='Model ID to use for analysis')
@click.pass_context
@handle_common_cli_errors
def summarize_text_command(ctx, text, api_key, output, template, params, provider, model):
    """
    Analyze and summarize a text.
    
    TEXT: Text to analyze
    """
    # Create configuration object
    config = TextAnalysisConfig(
        text=text,
        output=Path(output) if output else None,
        template=template,
        params=params,
        provider=provider,
        model=model,
        api_key=api_key
    )
    
    # Configure provider
    provider_config = ProviderConfigurationManager.configure_provider(
        ctx, config.provider, config.api_key, config.model
    )
    
    # Analyze text using service
    service = TextAnalysisService(config)
    results = service.analyze_text(provider_config)
    
    # Display results
    _display_analysis_results(results, "Text Summary")


@cli.command('slack')
@click.argument('channel_id_or_link', required=False)
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='Start date in YYYY-MM-DD format')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='End date in YYYY-MM-DD format')
@click.option('--output-dir', default='slack_exports', help='Directory to save messages')
@click.option('--token', help='Slack token', 
              default=lambda: os.environ.get('SLACK_TOKEN', None))
@click.option('--thread-ts', help='Thread timestamp to fetch replies from')
@click.option('--user-id', help='Filter messages by user ID')
@click.option('--only-threads', is_flag=True, help='Only fetch messages that have replies')
@click.option('--with-reactions', is_flag=True, help='Only fetch messages that have reactions')
@click.option('--api_key', help='OpenAI API key.', 
              default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use')
@click.option('--provider', default='openai', help='AI provider to use')
@click.option('--model', default='gpt-4', help='Model ID to use for analysis')
@click.option('--summary', is_flag=True, help='Generate a global summary of all Slack activity')
@click.option('--list-channels', is_flag=True, help='List all Slack channels')
@click.option('--include-private/--public-only', default=True, help='Include private channels and DMs')
@click.option('--include-archived/--active-only', default=False, help='Include archived channels')
@click.option('--max-channels', default=10, type=int, help='Maximum number of channels to analyze')
@click.option('--min-messages', default=5, type=int, help='Minimum number of messages in a channel')
@click.option('--workers', default=0, type=int, help='Number of parallel workers for downloading')
@click.option('--auto-join', is_flag=True, help='Automatically join channels before downloading')
@click.pass_context
@handle_common_cli_errors
@handle_slack_errors
def analyze_slack_messages(ctx, channel_id_or_link, start_date, end_date, output_dir, token, 
                          api_key, output, template, provider, model, thread_ts, user_id, 
                          only_threads, with_reactions, summary, list_channels, include_private, 
                          include_archived, max_channels, min_messages, workers, auto_join):
    """
    Analyze and summarize a Slack channel or thread.
    
    CHANNEL_ID_OR_LINK: Slack channel ID or Slack message link
    """
    # Create configuration object
    config = SlackAnalysisConfig(
        channel_id_or_link=channel_id_or_link,
        start_date=start_date,
        end_date=end_date,
        output_dir=output_dir,
        token=token,
        api_key=api_key,
        output=Path(output) if output else None,
        template=template,
        provider=provider,
        model=model,
        thread_ts=thread_ts,
        user_id=user_id,
        only_threads=only_threads,
        with_reactions=with_reactions,
        summary=summary,
        list_channels=list_channels,
        include_private=include_private,
        include_archived=include_archived,
        max_channels=max_channels,
        min_messages=min_messages,
        workers=workers,
        auto_join=auto_join
    )
    
    # Configure provider (only needed for analysis operations)
    provider_config = None
    if not config.list_channels:
        provider_config = ProviderConfigurationManager.configure_provider(
            ctx, config.provider, config.api_key, config.model
        )
    
    # Process Slack request using service
    service = SlackAnalysisService(config)
    result = service.process_slack_request(provider_config)
    
    # Display results based on operation type
    if config.list_channels:
        click.echo(result)
    elif config.summary:
        click.echo("\n=== Global Slack Summary ===")
        click.echo(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        click.echo("\n" + result)
    else:
        click.echo("\n=== Slack Channel Summary ===")
        click.echo("Messages exported and analyzed successfully.")


@cli.command('listen')
@click.option('--duration', type=int, help='Duration in seconds (0 for continuous)', default=0)
@click.option('--output-dir', default='recordings', help='Directory to save recordings')
@click.option('--api_key', help='API key for the selected provider.', 
              default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', type=click.Path())
@click.option('--template', default='summary', help='Analysis template to use')
@click.option('--no-cache', is_flag=True, help='Disable transcription caching')
@click.option('--provider', default='openai', help='AI provider to use')
@click.option('--model', default='whisper-1', help='Model ID to use for transcription')
@click.option('--keep-silence', is_flag=True, help='Do not remove long silences from audio')
@click.option('--optimize', default='128k', help='Target bitrate for audio optimization')
@click.option('--max-size', default=100, help='Maximum audio file size in MB')
@click.pass_context
@handle_common_cli_errors
def listen_command(ctx, duration, output_dir, api_key, output, template, no_cache, 
                  provider, model, keep_silence, optimize, max_size):
    """
    Listen and transcribe system audio in real-time.
    """
    try:
        from src.audio_capture.system_audio import SystemAudioCapture
        
        recorder = SystemAudioCapture()
        recorder.start_recording(output_dir)
        
        if duration > 0:
            click.echo(f"Recording for {duration} seconds...")
            import time
            time.sleep(duration)
        else:
            click.echo("Recording... Press Ctrl+C to stop")
            while True:
                import time
                time.sleep(1)
                
    except KeyboardInterrupt:
        click.echo("\nStopping recording...")
        audio_file = recorder.stop_recording()
        
        if api_key:
            click.echo("Transcribing recorded audio...")
            
            # Create configuration for transcription
            config = MediaTranscriptionConfig(
                file_path=audio_file,
                output=Path(output) if output else None,
                template=template,
                no_cache=no_cache,
                provider=provider,
                model=model,
                api_key=api_key,
                keep_silence=keep_silence,
                optimize=optimize,
                max_size=max_size
            )
            
            # Configure provider and process
            provider_config = ProviderConfigurationManager.configure_provider(
                ctx, config.provider, config.api_key, config.model
            )
            
            service = MediaTranscriptionService(config)
            results = service.process_media_file(provider_config)
            
            # Display results
            _display_analysis_results(results, "Recording Analysis")
        else:
            click.echo(f"Audio saved to: {audio_file}")


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
@handle_common_cli_errors
def clear_cache(confirm):
    """
    Clear all cached transcriptions.
    """
    if not confirm:
        if not click.confirm('Are you sure you want to clear all transcription cache?'):
            click.echo("Operation cancelled.")
            return
    
    from src.transcription.cache import FileCache, TranscriptionCacheService
    
    # Create cache service
    file_cache = FileCache()
    cache_service = TranscriptionCacheService(file_cache)
    
    # Clear all cache
    cache_service.clear_all_cache()
    
    click.echo("Transcription cache cleared successfully.")


def _display_analysis_results(results: dict, title: str) -> None:
    """
    Display analysis results in a consistent format.
    
    Args:
        results: Dictionary containing analysis results
        title: Title to display above the results
    """
    click.echo(f"\n=== {title} ===")
    for key, value in results.items():
        click.echo(f"\n{key.replace('_', ' ').title()}:")
        click.echo("-" * 40)
        click.echo(value)
        click.echo()


if __name__ == '__main__':
    try:
        cli(obj={})
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}")
        sys.exit(1)