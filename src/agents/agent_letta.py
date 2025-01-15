import json, os, logging, asyncio, random

from letta.client.client import create_client
from letta.schemas.memory import ChatMemory
from src.prompts.sofia_prompt import (
    SOFIA_SYSTEM_PROMPT,
    SOFIA_FALLBACKS,
    SOFIA_TIMING
)

logger = logging.getLogger('instagram_webhook')

class AgentResponseGenerator:
    def __init__(self):
        self.client = create_client(base_url=os.getenv("LETTA_SERVER", "http://localhost:8283"))

        self.system_prompt = SOFIA_SYSTEM_PROMPT

        self.llm_config, self.embedding_config = None, None
        for lc in self.client.list_llm_configs():
            if lc.model == "gpt-4o-mini": self.llm_config = lc
        for ec in self.client.list_embedding_configs():
            if ec.embedding_model == "text-embedding-ada-002": self.embedding_config = ec
        self.memory = ChatMemory(human="", persona=SOFIA_SYSTEM_PROMPT, limit=9500)
        assert self.llm_config is not None
        assert self.embedding_config is not None


        
        # Load timing settings
        self.char_per_minute = SOFIA_TIMING["char_per_minute"]
        self.thinking_time_range = SOFIA_TIMING["thinking_time_range"]
        self.typing_variation = SOFIA_TIMING["typing_variation"]

    def create_agent_name(self, agent_name: str, user_id: str):
        return agent_name + "_" + user_id

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
            agent_id = self.client.get_agent_id(agent_name)
            agent_state = None
            if agent_id is not None:
                agent_state = self.client.get_agent(agent_id)
            else:
                agent_state = self.client.create_agent(
                    name=agent_name,
                    memory=self.memory,
                    embedding_config=self.embedding_config,
                    llm_config=self.llm_config
                )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.send_message(
                    message=context,
                    role="user",
                    agent_id=agent_state.id,
                )
            )

            # handle the tool call message
            response_text = None
            for message in response.messages:
                if message.message_type == "tool_call_message" and message.tool_call.name == "send_message":
                    response_text = json.loads(message.tool_call.arguments).get("message")
                    

            
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