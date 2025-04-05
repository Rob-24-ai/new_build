# ArtSensei API Integration Documentation

## Project Overview

We are building a system that integrates an image analysis API with ElevenLabs voice assistant. The system has the following components:

1. **Backend API (FastAPI)** - Hosted on Railway
2. **talk.artsensei.ai Prediction Service** - Hosted on DigitalOcean
3. **ElevenLabs Voice Agent** - To be configured later

## Current State

We have successfully built and deployed a FastAPI backend on Railway that sends image analysis requests to the talk.artsensei.ai prediction service. However, we are missing the required authentication credentials to make successful API calls to the prediction service.

## Railway Deployment

- Our FastAPI backend is deployed on Railway at: `https://newbuild-production.up.railway.app/`
- The deployment includes the following files:
  - `main.py` - The FastAPI application
  - `requirements.txt` - Dependencies
  - `Dockerfile` - Container configuration

## Code Implementation

The backend code has been modified to call the talk.artsensei.ai prediction API instead of using Google Gemini. Key parts:

```python
# Environment configuration with defaults
PREDICTION_API_BASE_URL = os.getenv("ARTSENSEI_API_BASE_URL", "https://talk.artsensei.ai")
PREDICTION_ID = os.getenv("ARTSENSEI_PREDICTION_ID", "default")
JWT_TOKEN = os.getenv("ARTSENSEI_JWT_TOKEN", "JWT")

# Construct the API URL
prediction_api_url = f"{PREDICTION_API_BASE_URL}/prediction/{PREDICTION_ID}"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}
```

The API accepts image URLs, converts them to base64, and sends them to the prediction API along with a prompt. The response is then processed and returned to the client.

## DigitalOcean Setup

The talk.artsensei.ai domain is hosted on DigitalOcean with DNS records pointing to server IP 167.99.0.237. The prediction service is running on this server.
The buffer memory is creating so much massive history that it's creating problems. What do I do here? ⁠
## Missing Credentials

We need to find or generate the following credentials to make the API work:

1. **ARTSENSEI_PREDICTION_ID** 
   - The ID that should be used in the prediction API URL path `/prediction/{id}`
   - Example in JavaScript code: `fetch('/prediction/{id}', {...})`

2. **ARTSENSEI_JWT_TOKEN**
   - The JWT token for authentication in the Authorization header
   - Example in JavaScript code: `"Authorization": "Bearer JWT"`

## Steps to Complete

1. **Find/Generate API Credentials**:
   - Check the code running on the DigitalOcean server at 167.99.0.237
   - Look for authentication configuration in server settings
   - Check for environment variables set on the server

2. **Configure Railway Environment**:
   - Add the API credentials as environment variables in Railway:
     - `ARTSENSEI_PREDICTION_ID`
     - `ARTSENSEI_JWT_TOKEN`

3. **Test the API Integration**:
   - Verify the API can successfully connect to the prediction service
   - Check if image analysis returns appropriate results

4. **ElevenLabs Integration (Future Phase)**:
   - Configure ElevenLabs to use our backend API as a tool
   - Set up voice assistant features

## GitHub Repository

The main application code is in a GitHub repository (`Rob-24-ai/new_build`). There is also a potentially related repository at https://github.com/Just-Hammad/artsensei that might contain frontend components, but it does not appear to contain the backend prediction API code.

## API Endpoints

Our backend provides the following endpoints:

- `GET /` - Root endpoint showing API status
- `GET /health` - Health check endpoint
- `POST /analyze-image/` - Main endpoint for image analysis

## Testing the API

Once credentials are properly set, you can test the API with:

```
curl -X POST https://newbuild-production.up.railway.app/analyze-image/ \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "user_id": "test-user",
    "prompt": "Describe this image in detail"
  }'
```

## Next Steps for Another LLM

1. Help identify the correct values for `ARTSENSEI_PREDICTION_ID` and `ARTSENSEI_JWT_TOKEN`.
2. Check the DigitalOcean server or suggest ways to retrieve/generate these credentials.
3. Update the Railway environment variables with these values.
4. Test the API to ensure it's correctly integrated with the talk.artsensei.ai prediction service.