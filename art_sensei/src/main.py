import asyncio
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import base64
from dotenv import load_dotenv
load_dotenv()

from .gemini_integration import analyze_text_with_gemini, analyze_image_and_text_with_gemini, analyze_image_from_data_url
from .deepgram_client import DeepgramConnection
from .conversation_context import ConversationContext
from .elevenlabs_tts import text_to_speech_elevenlabs

app = FastAPI()

class TextAnalysisRequest(BaseModel):
    text: str

class ImageAnalysisRequest(BaseModel):
    text: str
    image_url: str

class TextAnalysisResponse(BaseModel):
    analysis: str

@app.get("/")
def read_root():
    return {"message": "ArtSensei Backend is running"}

@app.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text_endpoint(request: TextAnalysisRequest):
    """Receives text and returns Gemini's analysis."""
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        analysis_result = analyze_text_with_gemini(request.text)
        return TextAnalysisResponse(analysis=analysis_result)
    except Exception as e:
        # Catch potential errors from the gemini module if not handled there
        print(f"Error during text analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@app.post("/analyze-image", response_model=TextAnalysisResponse)
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """Receives text and an image URL, returns Gemini's analysis."""
    if not request.text or not request.image_url:
        raise HTTPException(status_code=400, detail="Text and image_url cannot be empty")

    # Basic URL validation (can be improved)
    if not request.image_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid image_url format")

    try:
        analysis_result = analyze_image_and_text_with_gemini(request.text, request.image_url)
        return TextAnalysisResponse(analysis=analysis_result)
    except Exception as e:
        print(f"Error during image analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during image analysis")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("\n\n*** NEW WEBSOCKET CLIENT CONNECTING ***\n\n")
    await websocket.accept()
    print(f"\n\n*** WEBSOCKET CLIENT CONNECTED: {websocket.client} ***\n\n")
    
    # Create a conversation context for this client
    conversation = ConversationContext()

    # Track the last complete transcript for this session to avoid duplicates
    last_transcript = ""
    
    async def send_transcript_to_client(transcript: str):
        nonlocal last_transcript
        try:
            print(f"Received transcription from Deepgram: {transcript}")
            # Send the transcription to the client - frontend will handle display deduplication
            await websocket.send_text(json.dumps({"type": "transcription", "text": transcript}))
            
            # Only add to conversation context if this appears to be a complete thought
            # Check for sentence-ending punctuation or if it's at least 3 words longer than last transcript
            is_complete = any(transcript.rstrip().endswith(p) for p in ['.', '?', '!']) or \
                         (len(transcript.split()) >= len(last_transcript.split()) + 3)
            
            # Check for duplicates more thoroughly
            # It's a duplicate if:
            # 1. It's identical to the last transcript (case-insensitive).
            # 2. It starts with the last transcript and only adds 1-2 words (likely an extension).
            starts_with_last = last_transcript and transcript.lower().startswith(last_transcript.lower())
            word_diff = len(transcript.split()) - len(last_transcript.split()) if last_transcript else len(transcript.split())

            is_duplicate = transcript.lower() == last_transcript.lower() or \
                          (starts_with_last and word_diff <= 2 and word_diff > 0)

            if is_complete and not is_duplicate:
                # This seems like a complete thought that's worth responding to
                print(f"Adding to conversation context: {transcript}")
                
                # Add the transcript to conversation context
                conversation.add_user_message(transcript)
                last_transcript = transcript
                
                # Get AI response to the transcript using conversation context
                try:
                    contextual_prompt = conversation.get_prompt_with_context(transcript)
                    ai_response = analyze_text_with_gemini(contextual_prompt)
                    print(f"AI response: {ai_response}")
                    
                    # Add AI response to conversation context
                    conversation.add_ai_response(ai_response)
                    
                    # Send AI response (text) back to client for captions
                    await websocket.send_text(json.dumps({"type": "ai_response", "text": ai_response}))

                    # --- Generate and send AI audio response --- 
                    try:
                        print("Attempting to generate TTS audio...")
                        audio_bytes = await text_to_speech_elevenlabs(ai_response)
                        if audio_bytes:
                            print(f"TTS audio generated ({len(audio_bytes)} bytes). Encoding and sending...")
                            # Encode audio bytes to Base64 string for JSON transport
                            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                            # Send audio data to client
                            await websocket.send_text(json.dumps({
                                "type": "ai_audio", 
                                "audio_base64": audio_base64
                            }))
                            print("AI audio sent to client.")
                        else:
                            print("TTS generation failed or returned empty audio.")
                    except Exception as tts_error:
                        print(f"Error during TTS generation or sending: {tts_error}")
                    # --- End TTS section ---

                except Exception as e:
                    print(f"Error generating AI response: {e}")
                    await websocket.send_text(json.dumps({"type": "error", "text": "Error generating AI response"}))
            else:
                print(f"Skipping incomplete or duplicate transcript: {transcript}")
                
        except WebSocketDisconnect:
            print(f"Client {websocket.client} disconnected before transcript could be sent.")
        except Exception as e:
            print(f"Error sending transcript to client {websocket.client}: {e}")

    dg_connection = DeepgramConnection(transcript_callback=send_transcript_to_client)
    
    try:
        print(f"Establishing Deepgram connection for {websocket.client}...")
        await dg_connection.connect() 

        await asyncio.sleep(0.5) 

        if not dg_connection.is_connected:
             print(f"Deepgram connection failed for {websocket.client}. Closing WebSocket.")
             await websocket.close(code=1011, reason="Failed to connect to transcription service")
             return # Exit the endpoint

        print(f"Deepgram connection ready for {websocket.client}.")

        while True:
            # Receive data from the client - could be audio bytes or a text message
            message = await websocket.receive()
            
            # Handle JSON messages (for image analysis)
            if "text" in message:
                try:
                    text_data = message["text"]
                    json_data = json.loads(text_data)
                    
                    # Check if this is an image analysis request
                    if json_data.get("type") == "analyze_image" and "dataUrl" in json_data:
                        print(f"Received image analysis request from {websocket.client}")
                        data_url = json_data["dataUrl"]
                        
                        try:
                            # Add the image to the conversation context
                            conversation.add_image_message(data_url)
                            
                            # Process the image with Gemini API using our new function
                            analysis_result = analyze_image_from_data_url(data_url)
                            print(f"Image analysis result: {analysis_result[:100]}...")

                            # Add AI response to conversation context
                            conversation.add_ai_response(analysis_result)

                            # Send analysis result (text) back to client for captions
                            await websocket.send_text(json.dumps({"type": "ai_response", "text": analysis_result}))

                            # --- Generate and send AI audio response for image analysis ---
                            try:
                                print("Attempting to generate TTS audio for image analysis...")
                                audio_bytes = await text_to_speech_elevenlabs(analysis_result)
                                if audio_bytes:
                                    print(f"TTS audio generated ({len(audio_bytes)} bytes). Encoding and sending...")
                                    # Encode audio bytes to Base64 string for JSON transport
                                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                                    # Send audio data to client
                                    await websocket.send_text(json.dumps({
                                        "type": "ai_audio",
                                        "audio_base64": audio_base64
                                    }))
                                    print("AI audio for image analysis sent to client.")
                                else:
                                    print("TTS generation failed or returned empty audio for image analysis.")
                            except Exception as tts_error:
                                print(f"Error during TTS generation or sending for image analysis: {tts_error}")
                            # --- End TTS section for image analysis ---

                        except Exception as e:
                            print(f"Error processing image analysis request: {e}")
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "text": f"Error analyzing image: {str(e)}"
                            }))
                except Exception as e:
                    print(f"Error processing text message: {e}")
            
            # Handle audio data (for speech transcription)
            elif "bytes" in message:
                data = message["bytes"]
                print(f"Received audio chunk of size {len(data)} bytes from {websocket.client}")
                await dg_connection.send_audio(data)

    except WebSocketDisconnect:
        print(f"WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        print(f"An error occurred in WebSocket endpoint for {websocket.client}: {e}")
        await websocket.close(code=1011, reason=f"Server error: {e}") 
    finally:
        print(f"Closing Deepgram connection for {websocket.client}...")
        await dg_connection.finish()
        print(f"Resources cleaned up for {websocket.client}.")
