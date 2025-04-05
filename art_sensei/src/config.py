import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file from the parent directory relative to src/
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env` takes priority over `project.env`
        env_file=dotenv_path,
        extra='ignore' # Ignore extra fields from .env
    )
    google_api_key: str
    deepgram_api_key: str

    # Add other keys here later

settings = Settings()

# Basic check
if not settings.google_api_key:
    raise ValueError("GOOGLE_API_KEY must be set in the .env file")
if not settings.deepgram_api_key:
    raise ValueError("DEEPGRAM_API_KEY must be set in the .env file")

print(f"Loaded GOOGLE_API_KEY starting with: {settings.google_api_key[:4]}...") # Basic check
print(f"Loaded DEEPGRAM_API_KEY starting with: {settings.deepgram_api_key[:4]}...") # Basic check
