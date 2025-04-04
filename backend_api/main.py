import os
import io
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Configure the Google AI client with minimal setup
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    print("Google Gemini API configured successfully")
else:
    print("Warning: GOOGLE_API_KEY not found in environment variables")

# Define request body model for the analysis endpoint
class ImageAnalysisRequest(BaseModel):
    image_url: HttpUrl  # Use HttpUrl for basic URL validation
    user_id: str  # User ID to track conversation context
    prompt: str = "Describe this image in detail"  # Default prompt if none provided

# Create a minimal FastAPI application
app = FastAPI()

# Define a simple route for the root URL with debug info
@app.get("/")
async def read_root():
    # Get all available environment variables (masking sensitive info)
    env_vars = {}
    for key in os.environ:
        if "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
            # Mask sensitive values
            value = "[MASKED]" if os.environ.get(key) else "None"
        else:
            value = os.environ.get(key) or "None"
        env_vars[key] = value
        
    # Look for variants of the Google API key name
    api_key_variants = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", "Not found") != "Not found",
        "GOOGLE_APIKEY": os.getenv("GOOGLE_APIKEY", "Not found") != "Not found",
        "GOOGLEAPI_KEY": os.getenv("GOOGLEAPI_KEY", "Not found") != "Not found",
        "GOOGLE_API_SECRET": os.getenv("GOOGLE_API_SECRET", "Not found") != "Not found"
    }
    
    return {
        "message": "Hello! Image Analysis API is running.",
        "port": os.getenv("PORT", "8000"),
        "api_key_configured": api_key is not None,
        "api_key_env_check": api_key_variants,
        "available_keys": [k for k in env_vars.keys() if "key" in k.lower()],
        "status": "ok"
    }

# Minimal image analysis function
async def analyze_image_with_gemini(image_bytes: bytes, prompt: str) -> str:
    """Minimal implementation to analyze an image using Gemini"""
    if not api_key:
        return "Error: Google API Key not configured"
    
    try:
        # Use the simplest path with minimal error handling
        img = Image.open(io.BytesIO(image_bytes))
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = await model.generate_content_async([prompt, img])
        return response.text
    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {e}")

# Basic endpoint for image analysis
@app.post("/analyze-image/")
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    # Extract request parameters
    image_url = str(request.image_url)
    user_id = request.user_id
    prompt = request.prompt
    
    # Log the request (for debugging)
    print(f"Received request from user {user_id} to analyze image URL: {image_url}")
    
    try:
        # Fetch the image with minimal error handling
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        
        # Pass to Gemini for analysis
        analysis_result = await analyze_image_with_gemini(response.content, prompt)
        
        # Return response with analysis result
        return {
            "status": "success",
            "user_id": user_id,
            "input_url": image_url,
            "analysis": {
                "description": analysis_result
            }
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Could not retrieve image: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
