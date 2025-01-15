from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query
from fastapi.security import APIKeyHeader
import hmac
import hashlib
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError
import os
from dotenv import load_dotenv
from src.instagram_api import InstagramAPI
from src.agents.agent_langgraph import AgentResponseGenerator
import logging
from datetime import datetime
import sys
import asyncio
from src.response_handler import ResponseHandler

load_dotenv()

app = FastAPI(title="Instagram Webhook Handler")

# Load from environment variables
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")
BOT_ID = os.getenv("INSTAGRAM_BOT_ID")  # This should be your bot's Instagram ID

# Models for webhook payloads
class AttachmentPayload(BaseModel):
    url: str

class MessageAttachment(BaseModel):
    type: str
    payload: AttachmentPayload

class Message(BaseModel):
    mid: str
    text: Optional[str] = None
    attachments: Optional[List[MessageAttachment]] = None

class Sender(BaseModel):
    id: str

class Recipient(BaseModel):
    id: str

class MessagingItem(BaseModel):
    sender: Sender
    recipient: Recipient
    timestamp: int
    message: Optional[Message] = None

class Entry(BaseModel):
    time: int
    id: str
    messaging: Optional[List[MessagingItem]] = None
    changes: Optional[List[Dict[str, Any]]] = None

class WebhookPayload(BaseModel):
    object: str
    entry: List[Entry]

async def verify_signature(request: Request) -> bool:
    """Verify that the payload was sent from Instagram"""
    body = await request.body()
    signature = request.headers.get('X-Hub-Signature-256')
    
    if not signature or not APP_SECRET:
        return False
    
    expected_signature = hmac.new(
        bytes(APP_SECRET, 'utf-8'),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Handle webhook verification from Instagram"""
    print(f"Received verification request: mode={hub_mode}, challenge={hub_challenge}, token={hub_verify_token}")
    
    # Verify all parameters are present
    if not all([hub_mode, hub_challenge, hub_verify_token]):
        print("Missing required parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # Verify token and mode
    if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
        try:
            # Convert challenge to integer and return it directly
            challenge_value = int(hub_challenge)
            print(f"Verification successful, returning challenge: {challenge_value}")
            return challenge_value
        except ValueError:
            print("Invalid challenge value")
            raise HTTPException(status_code=400, detail="Invalid challenge value")
    
    print("Verification failed: token mismatch")
    raise HTTPException(status_code=403, detail="Verification failed")

# Configure logging
def setup_logger():
    """Configure logging with custom format and multiple handlers"""
    # Clear any existing handlers to prevent duplicates
    logger = logging.getLogger('instagram_webhook')
    if logger.handlers:
        logger.handlers.clear()
    
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File Handlers
    # Debug log
    debug_handler = logging.FileHandler('logs/debug.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    
    # Error log
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Webhook payload log
    webhook_handler = logging.FileHandler('logs/webhook.log')
    webhook_handler.setLevel(logging.INFO)
    webhook_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)
    logger.addHandler(webhook_handler)
    
    return logger

# Initialize logger once
logger = setup_logger()

# Initialize components
instagram_api = InstagramAPI()
sofia = AgentResponseGenerator()
logger = setup_logger()
response_handler = ResponseHandler(instagram_api)

@app.on_event("startup")
async def startup_event():
    """Start the response handler when the app starts"""
    await response_handler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the response handler when the app shuts down"""
    await response_handler.stop()

@app.post("/webhook")
async def webhook_handler(
    request: Request
):
    """Handle incoming webhook events"""
    # Debug logging
    body = await request.body()
    headers = request.headers
    
    logger.debug("=== New Webhook Request ===")
    logger.debug(f"Headers: {dict(headers)}")
    logger.debug(f"Raw payload: {body.decode()}")
    
    try:
        # Parse the raw JSON first
        raw_payload = json.loads(body)
        logger.debug(f"Parsed JSON: {json.dumps(raw_payload, indent=2)}")
        
        # Then try to parse with Pydantic
        payload = WebhookPayload.parse_obj(raw_payload)
        
        if payload.object == 'instagram':
            for entry in payload.entry:
                if entry.messaging:
                    for messaging_item in entry.messaging:
                        await handle_message(messaging_item)
                
                if entry.changes:
                    for change in entry.changes:
                        await handle_change(change)
        
        logger.info("Successfully processed webhook payload")
        return {"status": "ok"}
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except ValidationError as e:
        logger.error(f"Validation Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_message(messaging_item: MessagingItem):
    """Handle incoming messages and reactions"""
    sender_id = messaging_item.sender.id
    recipient_id = messaging_item.recipient.id
    
    logger.debug(f"=== New Message Handler ===")
    logger.debug(f"Sender ID: {sender_id}")
    logger.debug(f"Recipient ID: {recipient_id}")
    logger.debug(f"Bot ID: {BOT_ID}")
    
    # Ignore messages sent by our bot
    if sender_id == BOT_ID:
        logger.debug(f"Ignoring message from our bot (ID: {sender_id})")
        return
    
    if sender_id == "1512552969452550":
        return # NOTE: only for testing (remove before production)

    logger.info(f"Processing message from sender {sender_id} to recipient {recipient_id}")
    
    if messaging_item.message:
        message = messaging_item.message
        
        # Handle text messages
        if message.text:
            logger.info(f"Received text message from {sender_id}: {message.text}")
            
            try:
                # Generate SOFIA's response with timing
                logger.debug("Generating SOFIA's response...")
                response = await sofia.generate_response(
                    user_message=message.text,
                    user_id=sender_id,
                    message_type="text"
                )
                logger.debug(f"Raw response from SOFIA: {response}")
                
                # Queue the response for delayed sending
                response_handler.queue_response(sender_id, response)
                logger.debug("Response queued for delayed sending")
                
            except Exception as e:
                logger.error(f"Error handling text message: {str(e)}", exc_info=True)
            
        # Handle attachments
        if message.attachments:
            for attachment in message.attachments:
                logger.info(f"Received {attachment.type} from {sender_id}")
                logger.debug(f"Attachment URL: {attachment.payload.url}")
                
                try:
                    # Generate response for image
                    if attachment.type == "image":
                        response = await sofia.generate_response(
                            user_message="[Image received]",
                            user_id=sender_id,
                            message_type="image"
                        )
                        logger.debug(f"Raw response from SOFIA for image: {response}")
                        
                        # Queue the response for delayed sending
                        response_handler.queue_response(sender_id, response)
                        logger.debug("Image response queued for delayed sending")

                except Exception as e:
                    logger.error(f"Error handling image: {str(e)}", exc_info=True)

async def handle_change(change: Dict[str, Any]):
    """Handle changes (comments, etc)"""
    logger.info(f"Processing change event: {change.get('field')}")
    logger.debug(f"Change details: {json.dumps(change, indent=2)}")
    
    field = change.get('field')
    value = change.get('value', {})
    
    if field == 'comments':
        logger.info(f"New comment: {value}")
        # Add your comment handling logic here
    elif field == 'messages':
        logger.info(f"Message change: {value}")
        # Add your message change handling logic here

# Add this to your InstagramAPI class in src/IG.py 