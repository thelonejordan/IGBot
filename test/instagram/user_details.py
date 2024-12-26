from src.instagram_api import InstagramAPI


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