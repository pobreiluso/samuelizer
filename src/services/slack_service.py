"""
Slack analysis service.
Extracted from cli.py to reduce complexity and improve maintainability.
"""
import os
import json
import time
import logging
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm

from src.config.command_configs import SlackAnalysisConfig
from src.config.provider_manager import ProviderConfigurationManager
from src.utils.error_handlers import ErrorContext, handle_slack_errors
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.slack.http_client import RequestsClient
from src.slack.filters import SlackMessageFilter
from src.slack.channel_lister import SlackChannelLister
from src.slack.utils import parse_slack_link, is_user_token
from src.slack.exceptions import SlackAPIError
from src.exporters.json_exporter import JSONExporter
from src.transcription.meeting_analyzer import MeetingAnalyzer
from src.transcription.meeting_minutes import DocumentManager

logger = logging.getLogger(__name__)


class SlackAnalysisService:
    """Service for handling Slack channel analysis operations."""
    
    def __init__(self, config: SlackAnalysisConfig):
        """
        Initialize the Slack analysis service.
        
        Args:
            config: Configuration for Slack analysis
        """
        self.config = config
        self.provider_manager = ProviderConfigurationManager()
        self.http_client = RequestsClient()
    
    def process_slack_request(self, provider_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Process a Slack analysis request based on configuration.
        
        Args:
            provider_config: Provider configuration (optional for list-only operations)
            
        Returns:
            Optional path to output file if generated
        """
        if self.config.list_channels:
            return self._list_channels()
        elif self.config.summary:
            if not provider_config:
                raise ValueError("Provider configuration required for summary generation")
            return self._generate_global_summary(provider_config)
        else:
            if not provider_config:
                raise ValueError("Provider configuration required for channel analysis")
            return self._analyze_specific_channel(provider_config)
    
    def _list_channels(self) -> str:
        """List all accessible Slack channels."""
        with ErrorContext("listing Slack channels"):
            channel_lister = SlackChannelLister(self.config.token, self.http_client)
            
            logger.info("Retrieving Slack channel list...")
            channels = channel_lister.list_channels(
                include_private=self.config.include_private,
                include_archived=self.config.include_archived
            )
            
            # Enrich channel information
            enriched_channels = channel_lister.get_channel_details(channels)
            
            # Log information about channel count
            total_channels = len(enriched_channels)
            if total_channels > 100:
                logger.info(f"Found {total_channels} channels. Use --max-channels 0 to analyze all")
            
            # Format for display
            formatted_text = channel_lister.format_channels_for_display(enriched_channels)
            
            # Save to file if requested
            output_path = None
            if self.config.output:
                output_path = str(self.config.output)
                self._save_channel_list(formatted_text, enriched_channels, output_path)
            
            return formatted_text
    
    def _save_channel_list(self, formatted_text: str, channels: List[Dict], output_path: str) -> None:
        """Save channel list to files."""
        # Save formatted text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        logger.info(f"Results saved to: {output_path}")
        
        # Save JSON version
        json_output = f"{os.path.splitext(output_path)[0]}.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON data saved to: {json_output}")
    
    def _generate_global_summary(self, provider_config: Dict[str, Any]) -> str:
        """Generate a global summary of Slack activity."""
        if not self.config.start_date or not self.config.end_date:
            raise ValueError("Start and end dates required for global summary")
        
        with ErrorContext("generating global Slack summary", log_traceback=True):
            # Get accessible channels
            accessible_channels = self._get_accessible_channels()
            
            # Download messages from all channels
            all_messages, channel_messages = self._download_messages_from_channels(
                accessible_channels
            )
            
            if not all_messages:
                raise ValueError("No messages found in the specified date range")
            
            # Save combined data
            self._save_combined_messages(all_messages, channel_messages)
            
            # Generate analysis
            analysis_result = self._analyze_global_messages(all_messages, provider_config)
            
            # Save results if requested
            output_path = None
            if self.config.output:
                output_path = str(self.config.output)
                DocumentManager.save_to_docx({'global_summary': analysis_result}, output_path)
                logger.info(f"Summary saved to: {output_path}")
            
            return analysis_result
    
    def _get_accessible_channels(self) -> List[Dict]:
        """Get list of accessible channels based on token type and configuration."""
        channel_lister = SlackChannelLister(self.config.token, self.http_client)
        
        try:
            channels = channel_lister.list_channels(
                include_private=self.config.include_private,
                include_archived=False
            )
        except SlackAPIError as e:
            if "invalid_auth" in str(e):
                logger.error("Slack authentication error. Please verify your token.")
                raise
            raise
        
        # Enrich channel information
        enriched_channels = channel_lister.get_channel_details(channels)
        
        # Filter channels based on token type and configuration
        is_user = is_user_token(self.config.token)
        
        if is_user:
            member_channels = enriched_channels
            logger.info(f"Using user token: access to {len(member_channels)} channels")
        else:
            if self.config.max_channels > 10:
                member_channels = enriched_channels
                logger.info(f"Using bot token with --max-channels {self.config.max_channels}: "
                          f"including all {len(member_channels)} available channels")
            else:
                member_channels = [c for c in enriched_channels if c.get('is_member', False)]
                logger.info(f"Using bot token: access to {len(member_channels)} channels "
                          f"where bot is member")
        
        # Limit number of channels if specified
        if self.config.max_channels > 0 and len(member_channels) > self.config.max_channels:
            logger.info(f"Limiting analysis to {self.config.max_channels} channels "
                       f"(of {len(member_channels)} available)")
            return member_channels[:self.config.max_channels]
        
        logger.info(f"Analyzing all {len(member_channels)} available channels")
        return member_channels
    
    def _download_messages_from_channels(
        self, 
        channels: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, Dict]]:
        """Download messages from multiple channels in parallel."""
        all_messages = []
        channel_messages = {}
        exporter = JSONExporter()
        
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Determine number of workers
        max_workers = self.config.workers if self.config.workers > 0 else min(32, os.cpu_count() * 4)
        logger.info(f"Downloading messages in parallel with {max_workers} workers")
        
        # Download messages in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_channel = {
                executor.submit(self._download_channel_messages, channel): channel 
                for channel in channels
            }
            
            with tqdm(total=len(future_to_channel), desc="Downloading messages", unit="channel") as pbar:
                for future in concurrent.futures.as_completed(future_to_channel):
                    result = future.result()
                    self._process_channel_result(result, all_messages, channel_messages, exporter)
                    pbar.update(1)
        
        logger.info(f"Total messages downloaded: {len(all_messages)}")
        return all_messages, channel_messages
    
    @handle_slack_errors
    def _download_channel_messages(self, channel: Dict) -> Dict:
        """Download messages from a single channel."""
        channel_id = channel['id']
        channel_name = channel['name']
        
        # Create channel-specific configuration
        channel_config = SlackConfig(
            token=self.config.token,
            channel_id=channel_id,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            output_dir=self.config.output_dir,
            auto_join=self.config.auto_join
        )
        
        # Create downloader and fetch messages
        downloader = SlackDownloader(channel_config, self.http_client)
        
        try:
            messages = downloader.fetch_messages()
            
            # Filter by date range
            messages = SlackMessageFilter.by_date_range(
                messages, 
                self.config.start_date, 
                self.config.end_date
            )
            
            # Add channel information to messages
            for msg in messages:
                msg['_channel_id'] = channel_id
                msg['_channel_name'] = channel_name
            
            return {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'messages': messages,
                'success': True
            }
            
        except SlackAPIError as e:
            error_str = str(e)
            if "not_in_channel" in error_str:
                logger.warning(f"Cannot access channel {channel_name} ({channel_id}): not a member")
            else:
                logger.warning(f"Error downloading from {channel_name} ({channel_id}): {error_str}")
            
            return {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'messages': [],
                'success': False,
                'error': error_str
            }
        except Exception as e:
            logger.warning(f"Unexpected error with {channel_name} ({channel_id}): {str(e)}")
            return {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'messages': [],
                'success': False,
                'error': str(e)
            }
    
    def _process_channel_result(
        self, 
        result: Dict, 
        all_messages: List[Dict],
        channel_messages: Dict[str, Dict],
        exporter: JSONExporter
    ) -> None:
        """Process the result from a channel message download."""
        channel_id = result['channel_id']
        channel_name = result['channel_name']
        messages = result['messages']
        
        # Only include channels with sufficient messages
        if len(messages) >= self.config.min_messages:
            all_messages.extend(messages)
            channel_messages[channel_id] = {
                'name': channel_name,
                'message_count': len(messages),
                'messages': messages
            }
            
            # Export messages for this channel
            exporter.export_messages(
                messages,
                channel_id,
                self.config.output_dir,
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            
            logger.info(f"Channel {channel_name} ({channel_id}): {len(messages)} messages")
        else:
            logger.info(f"Channel {channel_name} ({channel_id}): only {len(messages)} messages "
                       f"(minimum: {self.config.min_messages})")
    
    def _save_combined_messages(self, all_messages: List[Dict], channel_messages: Dict) -> str:
        """Save combined messages to a JSON file."""
        # Sort messages by timestamp
        all_messages.sort(key=lambda x: float(x.get('ts', 0)))
        
        # Create combined output file
        combined_output = os.path.join(
            self.config.output_dir,
            f"slack_global_{self.config.start_date.strftime('%Y%m%d')}_"
            f"{self.config.end_date.strftime('%Y%m%d')}.json"
        )
        
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump({
                'start_date': self.config.start_date.strftime('%Y-%m-%d'),
                'end_date': self.config.end_date.strftime('%Y-%m-%d'),
                'channel_count': len(channel_messages),
                'message_count': len(all_messages),
                'channels': channel_messages
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Combined data saved to: {combined_output}")
        return combined_output
    
    def _analyze_global_messages(self, all_messages: List[Dict], provider_config: Dict[str, Any]) -> str:
        """Analyze all messages to generate a global summary."""
        # Limit messages for analysis to avoid token limits
        max_messages_for_analysis = 1000
        if len(all_messages) > max_messages_for_analysis:
            logger.warning(f"Limiting analysis to {max_messages_for_analysis} messages "
                          f"(of {len(all_messages)} total)")
            step = len(all_messages) // max_messages_for_analysis
            selected_messages = all_messages[::step]
        else:
            selected_messages = all_messages
        
        # Format messages for analysis
        formatted_messages = []
        for msg in selected_messages:
            channel_name = msg.get('_channel_name', 'unknown')
            user_name = msg.get('user_info', msg.get('user', 'unknown'))
            text = msg.get('text', '')
            ts = float(msg.get('ts', 0))
            date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            
            formatted_msg = f"[{date_str}] #{channel_name} - {user_name}: {text}"
            formatted_messages.append(formatted_msg)
        
        analysis_text = "\n".join(formatted_messages)
        
        # Create analyzer
        analysis_client = self.provider_manager.create_analysis_client(
            provider_config['provider'],
            provider_config['api_key'],
            provider_config['model_id']
        )
        
        analyzer = MeetingAnalyzer(
            transcription=analysis_text,
            analysis_client=analysis_client
        )
        
        # Perform analysis with template parameters
        template_params = {
            'start_date': self.config.start_date.strftime('%Y-%m-%d'),
            'end_date': self.config.end_date.strftime('%Y-%m-%d'),
            'channel_count': len(self.config.output_dir)  # This should be channel_messages count
        }
        
        logger.info("Generating global summary...")
        return analyzer.analyze('global_summary', **template_params)
    
    def _analyze_specific_channel(self, provider_config: Dict[str, Any]) -> str:
        """Analyze a specific Slack channel."""
        # Parse channel ID from link if needed
        channel_id = self._parse_channel_identifier()
        
        # Create Slack configuration
        slack_config = SlackConfig(
            token=self.config.token,
            channel_id=channel_id,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            output_dir=self.config.output_dir,
            auto_join=self.config.auto_join
        )
        
        # Download and filter messages
        messages = self._download_and_filter_messages(slack_config)
        
        # Export messages
        exporter = JSONExporter()
        output_file = exporter.export_messages(
            messages,
            channel_id,
            self.config.output_dir,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )
        
        # Analyze messages
        analysis_result = self._analyze_channel_messages(messages, provider_config)
        
        # Save results if requested
        if self.config.output:
            DocumentManager.save_to_docx(analysis_result, str(self.config.output))
            logger.info(f"Document saved: {self.config.output}")
        
        return output_file
    
    def _parse_channel_identifier(self) -> str:
        """Parse channel ID from various input formats."""
        if not self.config.channel_id_or_link:
            raise ValueError("Channel ID or link is required")
        
        if self.config.channel_id_or_link.startswith('http'):
            # Parse Slack link
            channel_id, link_thread_ts = parse_slack_link(self.config.channel_id_or_link)
            if not channel_id:
                raise ValueError("Invalid Slack link. Could not extract channel ID.")
            
            # Use thread timestamp from link if not specified
            if link_thread_ts and not self.config.thread_ts:
                self.config.thread_ts = link_thread_ts
                logger.info(f"Using thread timestamp from link: {link_thread_ts}")
            
            return channel_id
        else:
            # Direct channel ID
            return self.config.channel_id_or_link
    
    @handle_slack_errors
    def _download_and_filter_messages(self, slack_config: SlackConfig) -> List[Dict]:
        """Download and filter messages based on configuration."""
        downloader = SlackDownloader(slack_config, self.http_client)
        
        # Download messages (thread or channel)
        if self.config.thread_ts:
            messages = downloader.fetch_thread_messages(self.config.thread_ts)
            logger.info(f"Downloaded {len(messages)} messages from thread {self.config.thread_ts}")
        else:
            messages = downloader.fetch_messages()
            logger.info(f"Downloaded {len(messages)} messages from channel")
        
        # Apply filters
        if self.config.user_id:
            messages = SlackMessageFilter.by_user(messages, self.config.user_id)
            logger.info(f"Filtered to {len(messages)} messages from user {self.config.user_id}")
        
        if self.config.only_threads:
            messages = SlackMessageFilter.by_has_replies(messages)
            logger.info(f"Filtered to {len(messages)} messages with thread replies")
        
        if self.config.with_reactions:
            messages = SlackMessageFilter.by_has_reactions(messages)
            logger.info(f"Filtered to {len(messages)} messages with reactions")
        
        # Apply date filters
        if self.config.start_date or self.config.end_date:
            messages = SlackMessageFilter.by_date_range(
                messages, 
                self.config.start_date, 
                self.config.end_date
            )
        
        return messages
    
    def _analyze_channel_messages(self, messages: List[Dict], provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze messages from a specific channel."""
        if not messages:
            logger.info("No messages to analyze.")
            return {}
        
        # Prepare text for analysis
        transcription_text = "\n".join([msg.get('text', '') for msg in messages])
        
        # Create analyzer
        analysis_client = self.provider_manager.create_analysis_client(
            provider_config['provider'],
            provider_config['api_key'],
            provider_config['model_id']
        )
        
        analyzer = MeetingAnalyzer(
            transcription=transcription_text,
            analysis_client=analysis_client
        )
        
        # Perform analysis
        if self.config.template == 'all':
            result = analyzer.analyze('default')
            return {'default': result}
        else:
            result = analyzer.analyze(self.config.template)
            return {self.config.template: result}