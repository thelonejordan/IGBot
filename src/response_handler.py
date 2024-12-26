import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import time
from dataclasses import dataclass

logger = logging.getLogger('instagram_webhook')

@dataclass
class QueuedResponse:
    recipient_id: str
    response: dict
    send_timestamp: float

class ResponseHandler:
    def __init__(self, instagram_api):
        self.instagram_api = instagram_api
        self.response_queue: List[QueuedResponse] = []
        self.is_running = False
        
    async def start(self):
        """Start the response handler loop"""
        self.is_running = True
        asyncio.create_task(self._process_queue())
        logger.info("Response handler started")
    
    async def stop(self):
        """Stop the response handler"""
        self.is_running = False
        logger.info("Response handler stopped")
    
    def queue_response(self, recipient_id: str, response: dict):
        """Add a response to the queue"""
        current_time = time.time()
        send_time = current_time + response.get("typing_duration", 0)
        
        queued_response = QueuedResponse(
            recipient_id=recipient_id,
            response=response,
            send_timestamp=send_time
        )
        
        self.response_queue.append(queued_response)
        logger.debug(f"Queued response for {recipient_id} to be sent at {send_time}")
    
    async def _process_queue(self):
        """Process the response queue at regular intervals"""
        while self.is_running:
            try:
                current_time = time.time()
                # Find responses that are ready to be sent
                ready_responses = [
                    resp for resp in self.response_queue 
                    if resp.send_timestamp <= current_time
                ]
                
                # Remove ready responses from queue
                self.response_queue = [
                    resp for resp in self.response_queue 
                    if resp.send_timestamp > current_time
                ]
                
                # Send ready responses
                for response in ready_responses:
                    try:
                        logger.debug(f"Sending queued response to {response.recipient_id}")
                        result = self.instagram_api.send_text_message(
                            response.recipient_id, 
                            response.response
                        )
                        
                        if result:
                            logger.info(f"Successfully sent queued response to {response.recipient_id}")
                        else:
                            logger.error(f"Failed to send queued response to {response.recipient_id}")
                            
                    except Exception as e:
                        logger.error(f"Error sending queued response: {str(e)}", exc_info=True)
                
                # Sleep for a short interval before next check
                await asyncio.sleep(5)  # Check queue every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in response queue processing: {str(e)}", exc_info=True)
                await asyncio.sleep(1)  # Wait longer on error 