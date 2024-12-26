import requests
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class InstagramAPI:
    BASE_URL = "https://graph.instagram.com/v21.0"
    
    def __init__(self):
        load_dotenv()
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        
        if not self.access_token:
            raise ValueError("Missing required environment variable. Please set INSTAGRAM_ACCESS_TOKEN")

    def get_conversations(self, user_id=None):
        """
        Get a list of conversations
        Args:
            user_id (str, optional): Filter conversations with a specific user
        """
        try:
            endpoint = f"{self.BASE_URL}/me/conversations"
            params = {
                'access_token': self.access_token,
                'platform': 'instagram',
                'fields': 'participants,messages{id,from,to,message,created_time}'
            }
            
            if user_id:
                params['user_id'] = user_id
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data:
                print(f"Unexpected API response: {data}")
                return []
            
            return data['data']
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching conversations: {str(e)}")
            return []

    def get_conversation_messages(self, conversation_id):
        """
        Get messages for a specific conversation
        Args:
            conversation_id (str): ID of the conversation
        """
        try:
            endpoint = f"{self.BASE_URL}/{conversation_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'messages'
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            conversation_data = response.json()
            messages = conversation_data.get('messages', {}).get('data', [])
            
            # Get details for each message
            detailed_messages = [self.get_message_details(msg['id']) for msg in messages[:20]]  # Limited to 20 most recent messages
            
            return {
                'id': conversation_id,
                'messages': detailed_messages
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching conversation messages: {str(e)}")
            return None

    def get_message_details(self, message_id):
        """
        Get detailed information about a specific message
        Args:
            message_id (str): ID of the message
        """
        try:
            endpoint = f"{self.BASE_URL}/{message_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'id,created_time,from,to,message'
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching message details: {str(e)}")
            return None

    def send_text_message(self, recipient_id, text):
        """
        Send a text message to a user
        Args:
            recipient_id (str): Instagram-scoped ID (IGSID) of the recipient
            text (str): Text message (must be UTF-8 and <= 1000 bytes)
        """
        try:
            endpoint = f"{self.BASE_URL}/me/messages"
            
            # Extract text from response object if needed
            message_text = text["text"] if isinstance(text, dict) else text
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
            }
            
            logger.debug(f"Sending message to endpoint: {endpoint}")
            logger.debug(f"With payload: {payload}")
            
            response = requests.post(
                endpoint,
                json=payload,
                params={"access_token": self.access_token}
            )
            
            logger.debug(f"API Response status: {response.status_code}")
            logger.debug(f"API Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending text message: {str(e)}")
            logger.error(f"Failed payload: {payload if 'payload' in locals() else 'No payload constructed'}")
            return None

    def send_media_message(self, recipient_id, media_url, media_type):
        """
        Send media (image, video, audio, GIF) message
        Args:
            recipient_id (str): Instagram-scoped ID (IGSID) of the recipient
            media_url (str): URL of the media file
            media_type (str): Type of media ('image', 'video', 'audio')
        """
        try:
            endpoint = f"{self.BASE_URL}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": media_type,
                        "payload": {
                            "url": media_url
                        }
                    }
                }
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                params={"access_token": self.access_token}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending media message: {str(e)}")
            return None

    def send_post(self, recipient_id, post_id):
        """
        Share an Instagram post in a message
        Args:
            recipient_id (str): Instagram-scoped ID (IGSID) of the recipient
            post_id (str): ID of the Instagram post to share
        """
        try:
            endpoint = f"{self.BASE_URL}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "MEDIA_SHARE",
                        "payload": {
                            "id": post_id
                        }
                    }
                }
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                params={"access_token": self.access_token}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending post: {str(e)}")
            return None

    def send_reaction(self, recipient_id, message_id, reaction="love", remove=False):
        """
        React to a message
        Args:
            recipient_id (str): Instagram-scoped ID (IGSID) of the recipient
            message_id (str): ID of the message to react to
            reaction (str): Type of reaction (currently only 'love' is supported)
            remove (bool): If True, removes the reaction instead of adding it
        """
        try:
            endpoint = f"{self.BASE_URL}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "sender_action": "unreact" if remove else "react",
                "payload": {
                    "message_id": message_id
                }
            }
            
            if not remove:
                payload["payload"]["reaction"] = reaction
            
            response = requests.post(
                endpoint,
                json=payload,
                params={"access_token": self.access_token}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending reaction: {str(e)}")
            return None

    def send_heart_sticker(self, recipient_id):
        """
        Send a heart sticker
        Args:
            recipient_id (str): Instagram-scoped ID (IGSID) of the recipient
        """
        try:
            endpoint = f"{self.BASE_URL}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "like_heart"
                    }
                }
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                params={"access_token": self.access_token}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending heart sticker: {str(e)}")
            return None

    def get_user_details(self, fields=None):
        """
        Get details about the authenticated user
        Args:
            fields (list, optional): List of fields to request. Defaults to basic fields.
        """
        try:
            if fields is None:
                fields = [
                    'id', 'username', 'name', 'account_type',
                    'profile_picture_url', 'followers_count',
                    'follows_count', 'media_count'
                ]
                
            endpoint = f"{self.BASE_URL}/me"
            params = {
                'access_token': self.access_token,
                'fields': ','.join(fields)
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user details: {str(e)}")
            return None

    def get_user_media(self, limit=None):
        """
        Get media objects for the authenticated user
        Args:
            limit (int, optional): Number of media objects to return
        """
        try:
            endpoint = f"{self.BASE_URL}/me/media"
            params = {
                'access_token': self.access_token,
                'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username'
            }
            
            if limit:
                params['limit'] = limit
                
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user media: {str(e)}")
            return []

def main():
    try:
        api = InstagramAPI()
        
        # Get user details
        print("\nFetching user details...")
        user_details = api.get_user_details()
        if user_details:
            print(f"Username: {user_details.get('username')}")
            print(f"Account Type: {user_details.get('account_type')}")
            print(f"Followers: {user_details.get('followers_count')}")
            print(f"Following: {user_details.get('follows_count')}")
            print(f"Media Count: {user_details.get('media_count')}")
        
        # Get recent media
        print("\nFetching recent media...")
        media_items = api.get_user_media(limit=5)  # Get 5 most recent items
        for item in media_items:
            print(f"\nMedia ID: {item.get('id')}")
            print(f"Type: {item.get('media_type')}")
            print(f"Caption: {item.get('caption', 'No caption')}")
            print(f"URL: {item.get('permalink')}")
            print(f"Posted at: {item.get('timestamp')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
