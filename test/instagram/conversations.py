from datetime import datetime
from src.instagram_api import InstagramAPI
import os
from dotenv import load_dotenv

class ConversationManager:
    def __init__(self):
        load_dotenv()
        self.api = InstagramAPI()
        self.test_user_id = os.getenv('TEST_TARGET_USER_ID')
        if not self.test_user_id:
            raise ValueError("Missing TEST_TARGET_USER_ID in environment variables")

    def display_all_conversations(self):
        """Display all conversations"""
        print("\nFetching all conversations...")
        conversations = self.api.get_conversations()
        
        if not conversations:
            print("No conversations found")
            return
            
        print("\nAll Instagram Conversations:")
        self._display_conversations(conversations)

    def display_user_conversations(self, user_id):
        """Display conversations with specific user"""
        print(f"\nFetching conversations with user {user_id}...")
        conversations = self.api.get_conversations(user_id)
        
        if not conversations:
            print(f"No conversations found with user {user_id}")
            return
            
        print(f"\nConversations with user {user_id}:")
        self._display_conversations(conversations)

    def _display_conversations(self, conversations):
        """Helper method to display conversations"""
        for conv in conversations:
            print(f"\nConversation ID: {conv['id']}")
            
            if 'messages' in conv and 'data' in conv['messages']:
                print("Messages:")
                for msg in conv['messages']['data']:
                    self._display_message(msg)
            else:
                print("No messages in this conversation")

    def _display_message(self, msg):
        """Helper method to display a single message"""
        try:
            from_user = msg['from']['username'] if 'from' in msg else 'Unknown'
            message_text = msg.get('message', 'No message content')
            created_time = msg.get('created_time', 'No timestamp')
            message_id = msg.get('id', 'No ID')
            
            if created_time != 'No timestamp':
                created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            
            print(f"- [{created_time}] {from_user}: {message_text} (ID: {message_id})")
            
        except Exception as e:
            print(f"Error displaying message: {e}")

def main():
    try:
        manager = ConversationManager()
        
        # Example 1: Display all conversations
        manager.display_all_conversations()
        
        # Example 2: Display conversations with specific user
        print(f"\nFetching conversations with test user...")
        manager.display_user_conversations(manager.test_user_id)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 