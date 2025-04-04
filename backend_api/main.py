import os
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

# Define request body model for the analysis endpoint
class ImageAnalysisRequest(BaseModel):
    image_url: HttpUrl  # Use HttpUrl for basic URL validation
    user_id: str  # User ID to track conversation context
    prompt: str = "Describe this image in detail"  # Default prompt if none provided

# Create a minimal FastAPI application
app = FastAPI()

# Define a simple route for the root URL
@app.get("/")
async def read_root():
    return {
        "message": "Hello! Minimal API is running.",
        "port": os.getenv("PORT", "8000"),
        "status": "ok"
    }

# Basic endpoint structure for image analysis (no actual analysis yet)
@app.post("/analyze-image/")
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    # Extract request parameters
    image_url = str(request.image_url)
    user_id = request.user_id
    prompt = request.prompt
    
    # Log the request (for debugging)
    print(f"Received request from user {user_id} to analyze image URL: {image_url}")
    print(f"Using prompt: {prompt}")
    
    # Return a placeholder response
    return {
        "status": "success",
        "user_id": user_id,
        "input_url": image_url,
        "analysis": {
            "description": "[This is a placeholder. Actual image analysis not implemented yet.]"
        }
    }
