import logging
from fastapi import APIRouter, Request, Response

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle Slack events including URL verification challenge
    """
    try:
        # Get the JSON body from the request
        payload = await request.json()
        logger.debug(f"Received Slack event: {payload.get('type')}")
        
        # Handle URL verification challenge
        if payload.get("type") == "url_verification":
            challenge = payload.get("challenge")
            logger.info("Responding to Slack URL verification challenge")
            return {"challenge": challenge}
            
        # Handle other event types if needed in the future
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Slack event: {str(e)}")
        return Response(content={"error": str(e)}, status_code=500)