import os
import io
import base64
import json
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
PREDICTION_API_BASE_URL = os.getenv("ARTSENSEI_API_BASE_URL", "https://talk.artsensei.ai")
PREDICTION_ID = os.getenv("ARTSENSEI_PREDICTION_ID", "default")
JWT_TOKEN = os.getenv("ARTSENSEI_JWT_TOKEN", "JWT")
DEFAULT_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "60"))

# Validate required environment variables
if PREDICTION_API_BASE_URL == "https://talk.artsensei.ai" and JWT_TOKEN == "JWT":
    logger.warning(
        "Using default placeholder values for ARTSENSEI_API_BASE_URL and ARTSENSEI_JWT_TOKEN. "
        "These should be configured properly for production use."
    )

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
    description="API for analyzing images using ArtSensei Prediction API",
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
        "prediction_api": PREDICTION_API_BASE_URL,
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
    Analyze an image using the ArtSensei Prediction API
    
    Args:
        image_bytes: The raw image bytes
        prompt: The text prompt to send with the image
        user_id: User identifier for tracking
        
    Returns:
        The analysis result text
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Process the image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert to PNG format
            with io.BytesIO() as output:
                img.save(output, format="PNG")
                image_bytes = output.getvalue()
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create the prediction request
        prediction_request = PredictionRequest(
            question=prompt,
            history=[
                ConversationMessage(
                    role="apiMessage",
                    content="Hello, how can I help you?"
                )
            ],
            uploads=[
                ImageUpload(
                    name="image.png",
                    data=f"data:image/png;base64,{base64_image}",
                    mime="image/png"
                )
            ]
        )
        
        # Construct the API URL
        prediction_api_url = f"{PREDICTION_API_BASE_URL}/prediction/{PREDICTION_ID}"
        
        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Log the request (excluding the actual image data for size reasons)
        redacted_request = prediction_request.dict()
        redacted_request["uploads"][0]["data"] = "[BASE64_IMAGE_DATA_REDACTED]"
        logger.info(f"Sending request to {prediction_api_url} with prompt: {prompt}")
        logger.debug(f"Request payload: {json.dumps(redacted_request)}")
        
        # Make the API request
        try:
            response = requests.post(
                prediction_api_url,
                headers=headers,
                json=prediction_request.dict(),
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when connecting to prediction API")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Prediction API request timed out"
            )
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to prediction API")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to prediction API"
            ) 
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from prediction API: {e} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Prediction API error: {response.status_code}"
            )
        
        # Parse and return the prediction result
        try:
            result = response.json()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from prediction API: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from prediction API"
            )
        
        # Log the response (for debugging)
        logger.info(f"Received prediction API response")
        logger.debug(f"Response: {json.dumps(result)}")
        
        # Extract the relevant part of the result
        # This will need to be adjusted based on the actual response format
        if isinstance(result, dict):
            if "content" in result:
                description = result["content"]
            elif "text" in result:
                description = result["text"]
            elif "message" in result and "content" in result["message"]:
                description = result["message"]["content"]
            else:
                # Fallback with full result
                description = str(result)
        else:
            description = str(result)
        
        return description
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during prediction API analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during image analysis"
        )

@app.post(
    "/analyze-image/", 
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK
)
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """
    Analyze an image from a URL using ArtSensei Prediction API
    
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
