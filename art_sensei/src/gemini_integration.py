import google.generativeai as genai
import requests
from .config import settings

genai.configure(api_key=settings.google_api_key)

# Use a model suitable for text generation (e.g., gemini-1.5-flash or gemini-pro)
# Using flash as it's generally faster and cheaper for simpler tasks
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def analyze_text_with_gemini(text: str) -> str:
    """Analyzes the given text using a Gemini text model."""
    try:
        response = model.generate_content(text)
        # Basic error check within response if needed (depends on library)
        if response.text:
            return response.text
        else:
            # Handle cases where response might be empty or blocked
            # Check response.prompt_feedback for safety ratings/blocks
            print(f"Gemini Warning/Error: {response.prompt_feedback}")
            return "Sorry, I couldn't process that request due to content restrictions."

    except Exception as e:
        print(f"Error interacting with Gemini API: {e}")
        # Consider raising a more specific exception or returning a standard error message
        return "Sorry, there was an error communicating with the analysis service."


def analyze_image_and_text_with_gemini(text: str, image_url: str) -> str:
    """Analyzes the given text and image URL using the Gemini Vision model."""
    try:
        # Gemini Vision API can often take URLs directly
        # If this fails, we might need to download the image bytes first
        image_part = {
            "mime_type": "image/jpeg", # Assuming JPEG based on URL, might need detection
            "data": requests.get(image_url, stream=True).content
        }
        # Construct the prompt content
        contents = [text, image_part]

        response = model.generate_content(contents)

        if response.text:
            return response.text
        else:
            print(f"Gemini Vision Warning/Error: {response.prompt_feedback}")
            return "Sorry, I couldn't analyze the image due to content restrictions or other issues."

    except Exception as e:
        print(f"Error interacting with Gemini Vision API: {e}")
        return "Sorry, there was an error communicating with the image analysis service."


def analyze_image_from_data_url(data_url: str) -> str:
    """Analyzes an image provided as a data URL using the Gemini Vision model."""
    try:
        # Extract data from the data URL - typical format: data:image/jpeg;base64,BASE64_DATA
        if not data_url.startswith('data:'):
            return "Invalid data URL format."
            
        # Simple extraction of mime type and data
        mime_type = data_url.split(';')[0].split(':')[1]
        
        # Extract the base64 data part after the comma
        base64_data = data_url.split(',')[1]
        
        # Import the base64 library here to avoid global import if not needed elsewhere
        import base64
        
        # Decode the base64 data
        image_data = base64.b64decode(base64_data)
        
        # Create the image part for Gemini
        image_part = {
            "mime_type": mime_type,
            "data": image_data
        }
        
        # Create a prompt asking for art analysis
        prompt = "Analyze this artwork. Describe the style, techniques used, possible period, and artistic elements you observe."
        
        # Send to Gemini
        contents = [prompt, image_part]
        response = model.generate_content(contents)
        
        if response.text:
            return response.text
        else:
            print(f"Gemini Vision Warning/Error: {response.prompt_feedback}")
            return "Sorry, I couldn't analyze the image due to content restrictions or other issues."
            
    except Exception as e:
        print(f"Error analyzing image from data URL: {e}")
        return f"Sorry, there was an error analyzing the image: {str(e)}"
