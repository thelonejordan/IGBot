import os
from src.instagram_api import InstagramAPI


def main():
    try:
        api = InstagramAPI()
        
        # Get test user ID from environment
        test_user_id = os.getenv('TEST_TARGET_USER_ID')
        if not test_user_id:
            raise ValueError("Missing TEST_TARGET_USER_ID in environment variables")
        
        # Send text message
        print("\nSending text message...")
        api.send_text_message(test_user_id, "Hello! This is a test message.")
        
        # Send image
        print("\nSending image...")
        api.send_media_message(
            test_user_id,
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/1200px-Google_2015_logo.svg.png",
            "image"
        )
        
        # Send heart sticker
        print("\nSending heart sticker...")
        api.send_heart_sticker(test_user_id)
        
        # React to a message
        message_id = "aWdfZAG1faXRlbToxOklHTWVzc2FnZAUlEOjE3ODQxNDcwOTI3NzMyOTQ4OjM0MDI4MjM2Njg0MTcxMDMwMTI0NDI1OTY1Nzg3OTAyNjg1NTg5NTozMTk5NjgxMTI3Mzg2ODY1ODM3NDU3MjE0Nzc1MTI1NjA2NAZDZD"  # ID of message to react to
        print("\nSending reaction...")
        api.send_reaction(test_user_id, message_id)
        
        # Share a post
        post_id = "17995626404719919"  # ID of your Instagram post
        print("\nSharing post...")
        api.send_post(test_user_id, post_id)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()