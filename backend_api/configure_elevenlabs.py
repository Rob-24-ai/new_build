# /Users/robcolvin/ArtSensei/New Build/backend_api/configure_elevenlabs.py
import os
import json
import requests # Use requests for direct API calls
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# IMPORTANT: Update this if your ngrok URL changes!
BACKEND_API_URL = "https://cb99-2600-6c65-727f-8221-68d1-4c08-6aa8-d555.ngrok-free.app/analyze-image/" 
AGENT_VOICE_ID = "gx0ixYuz5JQ1lDnQXqXr" # Classic male narrator
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
# Corrected API endpoints based on research report (using /convai/ path)
TOOL_ENDPOINT = f"{ELEVENLABS_API_BASE}/convai/tools" 
AGENT_ENDPOINT = f"{ELEVENLABS_API_BASE}/convai/agents/create" # Note the /create suffix
AGENT_NAME = "ArtChat"
# --- End Configuration ---

if not ELEVENLABS_API_KEY:
    logger.error("ELEVENLABS_API_KEY not found in environment variables.")
    exit(1)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

# --- Tool Creation Function ---
def create_tool(api_key: str):
    """Creates the Image Analyzer tool using the provided API key."""
    logger.info(f"Defining Image Analyzer tool payload with backend URL: {BACKEND_API_URL}")
    tool_payload = {
        "tool_config": {
            "type": "webhook", # Corrected type based on 422 error message (expected: webhook, client, system)
            "name": "Image_Analyzer", # Corrected name to match pattern ^[a-zA-Z0-9_-]{1,64}$
            "description": "Analyzes image URLs using the backend API.", 
            "api_schema": {
                "url": BACKEND_API_URL, 
                "description": "Use this tool to analyze and describe any image from a given URL. It uses a powerful vision model to describe the contents of the image.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_url": {
                            "type": "string",
                            "description": "The URL of the image to analyze."
                        }
                    },
                    "required": ["image_url"]
                },
                "api_spec": {
                    "type": "rest",
                    "url": BACKEND_API_URL,
                    "method": "POST",
                    "headers": {}, # No auth needed for our backend
                    "body_template": {
                        "image_url": "${image_url}",
                        "user_id": "elevenlabs_agent_user",
                        "prompt": "Describe this artwork"
                    },
                    "response_path": "analysis.description" 
                }
            }
        }
    }

    logger.info(f"Sending POST request to {TOOL_ENDPOINT} to create the tool...")
    try:
        response = requests.post(TOOL_ENDPOINT, headers=headers, json=tool_payload)
        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        created_tool_data = response.json()
        created_tool_id = created_tool_data.get('id')
        if not created_tool_id:
            logger.error(f"Failed to get Tool ID from response: {created_tool_data}")
            return None
        logger.info(f"Successfully created Tool ID: {created_tool_id}")
        return {"tool_id": created_tool_id, "payload": tool_payload}
    except requests.exceptions.RequestException as e:
        logger.error(f"An HTTP error occurred: {e}")
        if e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            try:
                logger.error(f"Response body: {e.response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response body: {e.response.text}")
        return None

# --- Agent Creation Function ---
def create_agent(api_key: str, created_tool_id: str):
    """Creates the conversational agent using the provided tool ID."""
    logger.info(f"Defining the ArtChat agent payload with voice ID: {AGENT_VOICE_ID}")
    agent_payload = {
        "conversation_config": {
            "name": AGENT_NAME, 
            "voice_id": AGENT_VOICE_ID, 
            # Revert to original, more descriptive instructions
            "instructions": (
                "You are a helpful, conversational assistant named ArtChat who can talk about many topics. "
                "When the user mentions or shares an image URL, use the 'Image_Analyzer' tool to analyze it. "
                "Only use the tool when an image URL is provided. Otherwise, keep chatting normally."
            ),
            # Reference the created tool ID as a simple string array, per report (Section 6) interpretation for use_tool_ids=true
            "tools": [created_tool_id] 
        }
    }
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    agent_creation_url_with_param = f"{AGENT_ENDPOINT}?use_tool_ids=true"
    logger.info(f"Sending POST request to {agent_creation_url_with_param} to create the agent...")
    try:
        response = requests.post(agent_creation_url_with_param, headers=headers, json=agent_payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        agent_data = response.json()
        created_agent_id = agent_data.get('agent_id') 
        if not created_agent_id:
            logger.error(f"Failed to create agent. 'agent_id' not found in response: {agent_data}")
            return None
        return created_agent_id
    except requests.exceptions.RequestException as e:
        logger.error(f"An HTTP error occurred: {e}")
        if e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            try:
                logger.error(f"Response body: {e.response.json()}")
            except requests.exceptions.JSONDecodeError:
                logger.error(f"Response body: {e.response.text}")
        return None

# --- Main Execution ---
def main():
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment variables.")
        return

    tool_creation_result = create_tool(api_key)
    if not tool_creation_result:
        logger.error("Tool creation failed. Exiting.")
        exit(1)
        
    created_tool_id = tool_creation_result["tool_id"]

    if created_tool_id:
        created_agent_id = create_agent(api_key, created_tool_id)
        if created_agent_id:
            logger.info(f"Successfully created Agent ID: {created_agent_id}")
            logger.info("--- Setup Complete ---")
            logger.info(f"Agent '{AGENT_NAME}' (ID: {created_agent_id}) is configured with Tool 'Image_Analyzer' (ID: {created_tool_id}).")
        else:
            logger.error("Agent creation failed.")
            exit(1)

if __name__ == "__main__":
    main()
