# ElevenLabs Agent Setup Plan

This document outlines the steps to configure an ElevenLabs conversational agent that uses our custom FastAPI backend for image analysis.

## Prerequisites

1.  **Backend API Running:** The FastAPI server (`backend_api/main.py`) must be running locally.
    ```bash
    # In backend_api directory
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 
    ```
2.  **Public URL (ngrok):** The local API must be exposed via a public URL using ngrok.
    *   Ensure ngrok is installed (`brew install ngrok`).
    *   Run in a *separate* terminal:
        ```bash
        ngrok http 8001
        ```
    *   **Current Public URL (from Step 861):** `https://cb99-2600-6c65-727f-8221-68d1-4c08-6aa8-d555.ngrok-free.app` (Note: This URL may change if ngrok is restarted).
3.  **API Keys:** Required API keys must be present in `/Users/robcolvin/ArtSensei/New Build/backend_api/.env`:
    *   `OPENAI_API_KEY`: For the backend image analysis.
    *   `ELEVENLABS_API_KEY`: For interacting with the ElevenLabs API/SDK.

## Configuration Steps (Python Script)

We will create a Python script (`backend_api/configure_elevenlabs.py`) to perform the setup using the ElevenLabs SDK.

### 1. Add ELEVENLABS_API_KEY to `.env`

Ensure the following line exists in `/Users/robcolvin/ArtSensei/New Build/backend_api/.env`:

```env
ELEVENLABS_API_KEY="your_elevenlabs_key_here" 
```

### 2. Create `configure_elevenlabs.py` Script

This script will define and register the necessary components with ElevenLabs.

```python
# /Users/robcolvin/ArtSensei/New Build/backend_api/configure_elevenlabs.py
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.agent import ToolDefinition, AgentDefinition
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# Use the current public ngrok URL for the backend
BACKEND_API_URL = "https://cb99-2600-6c65-727f-8221-68d1-4c08-6aa8-d555.ngrok-free.app/analyze-image/" 
# Choose a voice ID (e.g., classic male narrator)
AGENT_VOICE_ID = "gx0ixYuz5JQ1lDnQXqXr" 
# --- End Configuration ---

if not ELEVENLABS_API_KEY:
    logger.error("ELEVENLABS_API_KEY not found in environment variables. Please add it to the .env file.")
    exit(1)

try:
    logger.info("Initializing ElevenLabs client...")
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # --- Define the Image Analyzer Tool ---
    logger.info(f"Defining Image Analyzer tool with backend URL: {BACKEND_API_URL}")
    tool_def = ToolDefinition(
        name="Image Analyzer",
        description="Use this tool to analyze and describe any image from a given URL. It uses a powerful vision model to describe the contents of the image.",
        input_schema={
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "The URL of the image to analyze."
                }
            },
            "required": ["image_url"]
        },
        api_spec={
            "type": "rest",
            "url": BACKEND_API_URL,
            "method": "POST",
            "headers": {}, # No auth needed for our backend
            "body_template": {
                "image_url": "${image_url}",
                "user_id": "elevenlabs_agent_user", # Static user ID for simplicity
                "prompt": "Describe this artwork" # Static prompt
            },
            # Path to extract the result from the backend's JSON response
            "response_path": "analysis.description" 
        }
    )

    # --- Create the Tool in ElevenLabs ---
    logger.info("Creating the tool via ElevenLabs API...")
    created_tool = client.tools.create(tool_def)
    logger.info(f"Successfully created Tool ID: {created_tool.id}")

    # --- Define the Conversational Agent ---
    logger.info(f"Defining the ArtChat agent with voice ID: {AGENT_VOICE_ID}")
    agent_def = AgentDefinition(
        name="ArtChat",
        voice_id=AGENT_VOICE_ID, 
        instructions=(
            "You are a helpful, conversational assistant named ArtChat who can talk about many topics. "
            "When the user mentions or shares an image URL, use the 'Image Analyzer' tool to analyze it. "
            "Only use the tool when an image URL is provided. Otherwise, keep chatting normally."
        ),
        tools=[created_tool.id] # Use the ID of the tool we just created
    )

    # --- Create the Agent in ElevenLabs ---
    logger.info("Creating the agent via ElevenLabs API...")
    created_agent = client.agents.create(agent_def)
    logger.info(f"Successfully created Agent ID: {created_agent.id}")
    logger.info("--- Setup Complete ---")
    logger.info(f"Agent 'ArtChat' (ID: {created_agent.id}) is configured with Tool 'Image Analyzer' (ID: {created_tool.id}).")

except Exception as e:
    logger.error(f"An error occurred during setup: {e}")
    exit(1)

```

### 3. Install Dependencies

Ensure the necessary Python libraries are installed:

```bash
pip install elevenlabs python-dotenv
```
*(You might already have `python-dotenv`)*

### 4. Run the Configuration Script

Execute the script from the `backend_api` directory:

```bash
cd /Users/robcolvin/ArtSensei/New\ Build/backend_api
python configure_elevenlabs.py
```

This script will register the tool and agent with ElevenLabs using your API key. Make note of the Agent ID printed at the end.

## Next Steps After Running Script

1.  **Verify in ElevenLabs UI:** Log in to your ElevenLabs account and check the "Agents" and "Tools" sections to confirm `ArtChat` and `Image Analyzer` were created.
2.  **Test the Agent:** Use the ElevenLabs UI or API to interact with the created agent (using its Agent ID). Try giving it an image URL and see if it calls your backend API (you should see activity in the ngrok terminal) and responds with the description.

