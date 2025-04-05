import os
import io
import base64
import json
import copy
import logging
from typing import Dict, Any, Optional, List, Union

import requests
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field, validator
from PIL import Image
from dotenv import load_dotenv
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("artsensei-api")

# Load environment variables (for local development)
load_dotenv()

# Environment configuration with defaults
# Direct integration with OpenAI API
DEFAULT_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "180"))

# Log the configuration
logger.info(f"Using OpenAI API")

# Model definitions
class ImageUpload(BaseModel):
    type: str = "file"
    name: str
    data: str  # Base64 encoded image data with mime type prefix
    mime: str

class ConversationMessage(BaseModel):
    role: str
    content: str

class ImageAnalysisRequest(BaseModel):
    image_url: HttpUrl  # Use HttpUrl for basic URL validation
    user_id: str = Field(..., description="User ID to track conversation context")
    prompt: str = Field("Describe this image in detail", description="Prompt for the AI")
    
    @validator('user_id')
    def user_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('user_id must not be empty')
        return v

class PredictionRequest(BaseModel):
    question: str
    overrideConfig: Dict[str, Any] = {}
    history: List[ConversationMessage] = []
    uploads: List[ImageUpload] = []

class AnalysisResponse(BaseModel):
    status: str
    user_id: str
    input_url: str
    analysis: Dict[str, str]

# Create FastAPI application
app = FastAPI(
    title="ArtSensei Image Analysis API",
    description="API for analyzing images using OpenAI API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.datetime.now()
    response = await call_next(request)
    process_time = (datetime.datetime.now() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Process time: {process_time:.4f}s"
    )
    return response

# Define routes
@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    """Root endpoint with basic API information"""
    return {
        "message": "ArtSensei Image Analysis API",
        "version": "1.0.0",
        "prediction_api": "https://api.openai.com",
        "status": "operational"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    }

async def analyze_image_with_prediction_api(
    image_bytes: bytes, 
    prompt: str, 
    user_id: str
) -> str:
    """
    Analyze an image using the OpenAI API
    
    Args:
        image_bytes: The raw image bytes
        prompt: The text prompt to send with the image
        user_id: User identifier for tracking (not sent to OpenAI, but good for logs)
        
    Returns:
        The analysis result text
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    # Load OpenAI API Key from environment variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: OpenAI API Key missing."
        )
        
    try:
        # --- Image Processing (Stays the same) --- 
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            max_dimension = 512 # Restore original intended resize
            if max(img.width, img.height) > max_dimension:
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
            with io.BytesIO() as output:
                img.convert('RGB').save(output, format="JPEG", quality=80, optimize=True)
                image_bytes = output.getvalue()
            
            logger.debug(f"Compressed image size: {len(image_bytes) / 1024:.2f} KB")
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        # --- End Image Processing ---
        
        # Prepare the payload for OpenAI API
        payload = {
            "model": "gpt-4o", # Specify the model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                # OpenAI expects jpeg format hint here
                                "url": f"data:image/jpeg;base64,{base64_image}" 
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000 # Add max_tokens for the response
        }
        
        # OpenAI API endpoint
        openai_api_url = "https://api.openai.com/v1/chat/completions"
        
        # Headers including the OpenAI API Key
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}" 
        }
        
        # Log the request (excluding the actual image data for size reasons)
        redacted_payload = copy.deepcopy(payload)
        if "messages" in redacted_payload and len(redacted_payload["messages"]) > 0:
            for message in redacted_payload["messages"]:
                if "content" in message and isinstance(message["content"], list):
                    for content_item in message["content"]:
                        if content_item.get("type") == "image_url":
                            content_item["image_url"]["url"] = "[IMAGE_DATA_REDACTED]"
        logger.info(f"Sending request to OpenAI API for user {user_id} with prompt: {prompt}")
        logger.debug(f"Request payload (redacted): {json.dumps(redacted_payload)}")
        
        # Make the API request
        try:
            response = requests.post(
                openai_api_url,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            
            # Extract the response text
            response_data = response.json()
            analysis_result = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            if not analysis_result:
                 logger.error(f"OpenAI API returned empty content. Full response: {response_data}")
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OpenAI API returned empty content."
                 )
            
            logger.info(f"Received successful analysis from OpenAI for user {user_id}")
            logger.debug(f"OpenAI Response: {analysis_result}")
            return analysis_result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when connecting to OpenAI API")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OpenAI API request timed out"
            )
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to OpenAI API")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to OpenAI API"
            ) 
        except requests.exceptions.HTTPError as e:
            # Log the detailed error response from OpenAI if available
            error_details = "No details available."
            try:
                error_details = response.json()
            except json.JSONDecodeError:
                error_details = response.text
            logger.error(f"HTTP error from OpenAI API: {e} - Response: {error_details}")
            # Pass status code from OpenAI if possible, else default to 502
            status_code = response.status_code if response else status.HTTP_502_BAD_GATEWAY
            raise HTTPException(
                status_code=status_code, # Use OpenAI's status code
                detail=f"OpenAI API error: {error_details}" 
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during OpenAI API call: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {e}"
            )

    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error in analyze_image_with_prediction_api: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred."
        )

@app.post(
    "/analyze-image/", 
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK
)
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """
    Analyze an image from a URL using OpenAI API
    
    Args:
        request: The image analysis request containing URL, user_id and prompt
        
    Returns:
        Analysis results including description and metadata
    """
    # Extract request parameters
    image_url = str(request.image_url)
    user_id = request.user_id
    prompt = request.prompt
    
    # Log the request (for debugging)
    logger.info(f"Received analysis request from user {user_id} for image: {image_url}")
    
    try:
        # Fetch the image
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when fetching image from {image_url}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Image URL request timed out"
            )
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to image URL {image_url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not connect to the provided image URL"
            )
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error when fetching image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not retrieve image: HTTP error {response.status_code}"
            )
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            logger.warning(f"Non-image content type detected: {content_type}")
        
        # Pass to prediction API for analysis
        analysis_result = await analyze_image_with_prediction_api(
            response.content, 
            prompt,
            user_id
        )
        
        # Return response with analysis result
        return {
            "status": "success",
            "user_id": user_id,
            "input_url": image_url,
            "analysis": {
                "description": analysis_result
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred processing your request"
        )
