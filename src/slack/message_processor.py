import re
from typing import Dict
from src.interfaces import MessageFormatterInterface, SlackServiceInterface

class MessageProcessor(MessageFormatterInterface):
    """
    Processes Slack messages to replace user mentions and other formatting
    """
    def __init__(self, slack_service: SlackServiceInterface):
        self.slack_service = slack_service
        
    def replace_user_mentions(self, text: str) -> str:
        """
        Replaces user mentions in the text with user names
        
        Args:
            text: Text containing user mentions in the format <@USER_ID>
            
        Returns:
            str: Text with user mentions replaced by @username
        """
        if not text:
            return text
            
        def replace_mention(match):
            user_id = match.group(1)
            return f"@{self.slack_service.get_user_info(user_id)}"
            
        return re.sub(r'<@([A-Z0-9]+)>', replace_mention, text)
        
    def format_message(self, message: Dict) -> Dict:
        """
        Format a message by applying all formatting operations
        
        Args:
            message: Slack message dictionary
            
        Returns:
            Dict: Processed message
        """
        if "text" in message:
            message["text"] = self.replace_user_mentions(message["text"])
        return message
