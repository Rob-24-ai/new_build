import os
import io
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import datetime

# Load environment variables (for local development)
load_dotenv()

# Configure the Google AI client with minimal setup - try multiple possible env var names
def get_api_key():
    # Try to get the API key with different possible names
    key_names = ["GOOGLE_API_KEY", "google_api_key", "GOOGLEAPI_KEY", "RAILWAY_SHARED_GOOGLE_API_KEY"]
    
    for name in key_names:
        key = os.getenv(name)
        if key:
            print(f"Found API key using environment variable: {name}")
            return key
    
    return None

api_key = get_api_key()

if api_key:
    genai.configure(api_key=api_key)
    print("Google Gemini API configured successfully")
else:
    print("Warning: Could not find Google API Key in any expected environment variables")

# Define request body model for the analysis endpoint
class ImageAnalysisRequest(BaseModel):
    image_url: HttpUrl  # Use HttpUrl for basic URL validation
    user_id: str  # User ID to track conversation context
    prompt: str = "Describe this image in detail"  # Default prompt if none provided

# Create a minimal FastAPI application
app = FastAPI()

# Define a simple route for the root URL with enhanced debug info
@app.get("/")
async def read_root():
    # Get all available environment variables
    all_env_vars = dict(os.environ)
    
    # Try to find the API key using various names
    api_key_value = None
    key_names_to_check = ["GOOGLE_API_KEY", "google_api_key", "GOOGLEAPI_KEY", "RAILWAY_SHARED_GOOGLE_API_KEY", "RAILWAY_GOOGLE_API_KEY"]
    found_key_name = "None"
    for name in key_names_to_check:
        key_value = all_env_vars.get(name)
        if key_value:
            api_key_value = key_value
            found_key_name = name
            break

    api_key_configured_runtime = api_key_value is not None

    return {
        "message": "Hello! Image Analysis API running.",
        "port": all_env_vars.get("PORT", "8000"),
        "api_key_configured_at_startup": api_key is not None, # Checks if genai.configure() was called
        "api_key_found_in_env_now": api_key_configured_runtime,
        "api_key_variable_name_found": found_key_name,
        "all_environment_keys": sorted(list(all_env_vars.keys())),
        "status": "ok"
    }

# Add a simple test endpoint that doesn't need the API key
@app.get("/test-endpoint")
async def test_endpoint():
    return {
        "message": "This is a simple test endpoint that works without the API key",
        "timestamp": str(datetime.datetime.now())
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
