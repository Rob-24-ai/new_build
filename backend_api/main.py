import os
import io
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Google AI client
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
    # You might want to raise an error here in a real application
    # raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)

# --- Define request body model for the analysis endpoint ---
class ImageAnalysisRequest(BaseModel):
    image_url: HttpUrl # Use HttpUrl for basic URL validation
    user_id: str # User ID to track conversation context
    prompt: str = "Describe this image in detail" # Default prompt if none provided

# Create an instance of the FastAPI class
app = FastAPI()

# --- Image Analysis Function using Gemini ---
async def analyze_image_with_gemini(image_bytes: bytes, prompt: str) -> str:
    """Analyzes an image using the Google Gemini Pro Vision model."""
    if not api_key:
        return "Error: Google API Key not configured."
    
    try:
        # Prepare the image for the API
        img = Image.open(io.BytesIO(image_bytes))
        
        # Select the Gemini model (gemini-pro-vision is now gemini-1.5-flash)
        # Using 1.5 Flash as it's generally faster and cheaper for many vision tasks
        # model = genai.GenerativeModel('gemini-pro-vision') # Old model
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        # Make the API call
        print(f"Sending image to Gemini with prompt: '{prompt}'") # Log prompt
        response = await model.generate_content_async([prompt, img], stream=False)
        
        # Ensure the response has finished and get the text
        # response.resolve() # Not needed for async non-streaming
        
        # Handle potential safety blocks or empty responses
        if not response.parts:
             print("Warning: Gemini response was empty or blocked.")
             if response.prompt_feedback.block_reason:
                 print(f"Block Reason: {response.prompt_feedback.block_reason.name}")
                 return f"Error: Analysis blocked due to safety settings ({response.prompt_feedback.block_reason.name})."
             else:
                 return "Error: Received an empty response from the analysis model."
        
        print("Received response from Gemini.")
        return response.text

    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        # Consider more specific error handling based on genai exceptions
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {e}")

# Define a simple route for the root URL ("/")
# When someone visits the base URL, this function runs
@app.get("/")
async def read_root():
    # Return a simple message as JSON
    return {"message": "Hello! Image Analysis API is waiting."}

# --- Real API Endpoint for Analysis ---
@app.post("/analyze-image/")
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """Receives an image URL, fetches it, and analyzes it using Gemini."""
    the_url = str(request.image_url) # Get URL from request body
    user_id = request.user_id # Get user ID for tracking
    prompt = request.prompt # Get analysis prompt
    print(f"Received request from user {user_id} to analyze image URL: {the_url}")

    try:
        # 1. Fetch the image from the URL
        headers = {'User-Agent': 'ArtSensei Analysis Bot 1.0'} # Be a good net citizen
        response = requests.get(the_url, stream=True, timeout=15, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # Check content type - basic check
        content_type = response.headers.get('content-type')
        if not content_type or not content_type.startswith('image/'):
            print(f"Warning: URL content type is '{content_type}', not definitively an image.")
            # raise HTTPException(status_code=400, detail=f"URL content type ('{content_type}') doesn't appear to be an image.")
            # Allow proceeding but log warning
            
        image_bytes = response.content # Read image data
        print(f"Successfully fetched image from URL ({len(image_bytes)} bytes).")

        # 2. Call the Gemini analysis function
        analysis_result_text = await analyze_image_with_gemini(image_bytes, prompt)

        # 3. Return the results dictionary
        print(f"Analysis complete. Returning results.")
        return {
            "status": "success",
            "user_id": user_id,
            "input_url": the_url,
            "analysis": {
                "description": analysis_result_text
            }
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        raise HTTPException(status_code=400, detail=f"Could not retrieve image from URL. Error: {e}")
    except HTTPException as e: # Re-raise HTTPExceptions from analysis function
        raise e
    except Exception as e:
        # Catch any other unexpected problems during fetch or processing
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")

# If running this script directly (optional, good for simple testing)
# if __name__ == "__main__":
#     import uvicorn
#     print("Starting server directly with uvicorn...")
#     # Ensure GOOGLE_API_KEY is set before running this way
#     if not api_key:
#         print("ERROR: GOOGLE_API_KEY environment variable must be set to run directly.")
#     else:
#         uvicorn.run(app, host="127.0.0.1", port=8000)
