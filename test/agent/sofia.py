import asyncio
from src.agents.agent_letta import AgentResponseGenerator

from dotenv import load_dotenv

load_dotenv()

async def test_sofia_manually():
    sofia = AgentResponseGenerator()
    
    # Test messages
    test_messages = [
        "Hey Sofia! I'm visiting LA next week. Any recommendations?",
        # "I love Indian food but never cooked it. Where should I start?",
        # "Your workout routine is so inspiring! How do you stay motivated?",
        # "That outfit is amazing! Where do you shop for Indo-western fusion?",
        # "How do you maintain your cultural identity in LA?"
    ]
    
    print("\n=== Testing SOFIA's Responses ===\n")
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = await sofia.generate_response(message, "test_user_123", "text")
        print(f"SOFIA: {response}")
        print("-" * 50)
    
    # Test image response
    print("\n=== Testing Image Response ===\n")
    image_scenario = "User sent a picture of themselves at the gym"
    response = await sofia.generate_response(image_scenario, "test_user_123", "image")
    print(f"Scenario: {image_scenario}")
    print(f"SOFIA: {response}")

if __name__ == "__main__":
    asyncio.run(test_sofia_manually())
