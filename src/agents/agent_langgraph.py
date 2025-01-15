import json
import os
import logging
import asyncio
import random
from typing import Set, ClassVar

from src.agents.langgraph_helpers import create_app, send_image, get_app_config
from src.prompts.sofia_prompt import (
    SOFIA_SYSTEM_PROMPT,
    SOFIA_FALLBACKS,
    SOFIA_TIMING
)

logger = logging.getLogger('instagram_webhook')

MODEL_CONFIG = dict(
    model=os.getenv("LETTA_LLM_MODEL"),  # https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo#gpt-4-turbo-and-gpt-4
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=150,
    temperature=0.7,
)

class AgentResponseGenerator:
    thread_ids: ClassVar[Set[str]] = set()

    def __init__(self):
        self.system_prompt = SOFIA_SYSTEM_PROMPT
        self.client = create_app(MODEL_CONFIG, self.system_prompt, tools=[send_image])

        # Load timing settings
        self.char_per_minute = SOFIA_TIMING["char_per_minute"]
        self.thinking_time_range = SOFIA_TIMING["thinking_time_range"]
        self.typing_variation = SOFIA_TIMING["typing_variation"]

    def create_agent_name(self, agent_name: str, user_id: str):
        return agent_name + "_" + str(user_id)

    @classmethod
    def add_new_thread(cls, thread_id: str):
        cls.thread_ids.add(thread_id)

    async def generate_response(self, user_message: str, user_id: str, message_type: str = "text") -> dict:
        """
        Generate SOFIA's response to a user message
        
        Args:
            user_message: The message from the user
            user_id: The user's ID for context tracking
            message_type: Type of message ("text" or "image")
        """
        try:
            context = self._get_context_for_message_type(message_type, user_message)

            # check if SOFIA_user_id is already created
            agent_name = self.create_agent_name("sofia", user_id)
            if agent_name not in self.thread_ids:
                self.add_new_thread(agent_name)
                # TODO: populate with older messages if any

            config = get_app_config(agent_name)

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.invoke(
                    {"messages": context},
                    config=config,
                )
            )

            # handle the tool call message
            response_text = response["messages"][-1].content

            if response_text is None:
                response_text = SOFIA_FALLBACKS.get(message_type, SOFIA_FALLBACKS["text"])
            duration = self._calculate_response_timing(response_text)

            return {
                "text": response_text,
                "typing_duration": 0 # duration
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return {
                "text": SOFIA_FALLBACKS.get(message_type, SOFIA_FALLBACKS["text"]),
                "typing_duration": 0 # 2
            }

    def _get_context_for_message_type(self, message_type: str, user_message: str) -> str:
        """Get appropriate context based on message type"""
        if message_type == "image":
            return "User sent an image. Respond enthusiastically and ask about it!"
        return f"{user_message}"

    def _calculate_response_timing(self, response: str) -> float:
        """Calculate realistic timing for the response"""
        # Calculate base typing time (chars per second)
        char_per_second = self.char_per_minute / 60
        base_typing_time = len(response) / char_per_second

        # Add random variation
        variation = random.uniform(-self.typing_variation, self.typing_variation)
        typing_duration = base_typing_time * (1 + variation)

        # Add thinking time
        thinking_duration = random.uniform(*self.thinking_time_range)

        # Return total duration
        return  thinking_duration + typing_duration
