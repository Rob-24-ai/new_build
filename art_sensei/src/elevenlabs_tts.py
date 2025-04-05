import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings, play

# Load environment variables (for API key)
load_dotenv(dotenv_path='../.env') # Adjust path if .env is elsewhere relative to src

# Initialize ElevenLabs client
try:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables.")
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
except Exception as e:
    print(f"Error initializing ElevenLabs client: {e}")
    client = None # Set client to None if initialization fails

# Define the specific voice ID provided by the user
DEFAULT_VOICE_ID = "1SM7GgM6IMuvQlz2BwM3" # User provided voice ID (Mark)

async def text_to_speech_elevenlabs(text: str, voice_id: str = DEFAULT_VOICE_ID):
    """
    Generates audio from text using the ElevenLabs API and returns the audio bytes.

    Args:
        text: The text to synthesize.
        voice_id: The ElevenLabs voice ID to use.

    Returns:
        Bytes containing the generated audio data, or None if an error occurs.
    """
    if not client:
        print("ElevenLabs client not initialized. Cannot generate speech.")
        return None
    if not text:
        print("No text provided for TTS.")
        return None

    try:
        print(f"Generating audio for text: '{text[:50]}...' using voice {voice_id}")
        # Note: The SDK's generate function returns an iterator of audio chunks (bytes)
        audio_stream = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                # Settings can be customized further if needed
                # settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # Or another suitable model
        )

        # Concatenate the audio chunks into a single bytes object
        audio_bytes = b"".join([chunk for chunk in audio_stream])

        if not audio_bytes:
             print("ElevenLabs returned empty audio stream.")
             return None

        print(f"Generated audio bytes length: {len(audio_bytes)}")
        return audio_bytes

    except Exception as e:
        print(f"Error during ElevenLabs TTS generation: {e}")
        return None

# Example usage (for testing purposes, can be removed later)
if __name__ == '__main__':
    import asyncio

    async def test_tts():
        test_text = "Hello! This is a test of the ElevenLabs text-to-speech integration."
        audio_data = await text_to_speech_elevenlabs(test_text)
        if audio_data:
            print("TTS generation successful. Playing audio...")
            # The play function is blocking and useful for quick tests,
            # but we will stream bytes over WebSocket in the actual application.
            play(audio_data)
            print("Audio playback finished.")
        else:
            print("TTS generation failed.")

    # To run this test: python -m src.elevenlabs_tts
    asyncio.run(test_tts())
