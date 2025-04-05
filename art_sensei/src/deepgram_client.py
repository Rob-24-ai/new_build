import asyncio
from dotenv import load_dotenv
import os
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

# Load environment variables (if using .env file)
load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

# URL for the realtime streaming audio endpoint
URL = "wss://api.deepgram.com/v1/listen"

class DeepgramConnection:
    def __init__(self, transcript_callback=None):
        self.config: DeepgramClientOptions = DeepgramClientOptions(
            verbose=False # Set to True for detailed logs from SDK
        )
        self.deepgram: DeepgramClient = DeepgramClient(API_KEY, self.config)
        self.dg_connection = None
        self.is_connected = False
        self.transcript_callback = transcript_callback # Store the callback

    async def connect(self):
        options: LiveOptions = LiveOptions(
            model="nova-2",
            language="en-US",
            # Add other options like encoding, channels, sample_rate if needed
            # encoding="linear16",
            # channels=1,
            # sample_rate=16000,
            # Add Transcription options like interim_results, punctuation, diarize
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            # Add other features like smart_format, etc.
            smart_format=True,
        )

        try:
            print("Attempting to connect to Deepgram...")
            self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")
            # Setup event listeners
            self.dg_connection.on(LiveTranscriptionEvents.Open, self.on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Metadata, self.on_metadata)
            self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)
            self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_close)

            # Start the connection
            await self.dg_connection.start(options)
            print("Deepgram connection established (waiting for Open event).")


        except Exception as e:
            print(f"Could not open Deepgram connection: {e}")
            self.is_connected = False

    async def on_open(self, *args, **kwargs):
        # print(f"\n\n-- Connection Open (Simplified) -- Args: {args}, Kwargs: {kwargs}\n\n")
        self.is_connected = True

    async def on_message(self, sender, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) == 0:
            return
        # print(f"Speaker: {sentence}")
        if self.transcript_callback:
            print(f"Sending transcript via callback: {sentence}")
            # Use await if the callback is an async function
            await self.transcript_callback(sentence) 
        else:
             print("Transcript received, but no callback set.")

    async def on_metadata(self, sender, metadata, **kwargs):
        print(f"\n\n-- Metadata --\nSender: {sender} Metadata: {metadata}\n\n")

    async def on_speech_started(self, sender, speech_started, **kwargs):
        print(f"\n\n-- Speech Started --\nSender: {sender} Data: {speech_started}\n\n")

    async def on_utterance_end(self, sender, utterance_end, **kwargs):
        print(f"\n\n-- Utterance End --\nSender: {sender} Data: {utterance_end}\n\n")

    async def on_error(self, sender, error, **kwargs):
        print(f"\n\n-- Error --\n{error}\n\n")
        self.is_connected = False # Assume connection is lost on error

    async def on_close(self, sender, **kwargs):
        print(f"\n\n-- Connection Closed --\nSender: {sender} Kwargs: {kwargs}\n\n")
        self.is_connected = False

    async def send_audio(self, audio_chunk):
        # If connection isn't active, try to reconnect
        if not self.is_connected or not self.dg_connection:
            print("Attempting to reconnect to Deepgram before sending audio...")
            await self.connect()
            # Give a moment for connection to establish
            await asyncio.sleep(0.5)
            
        # Check again after reconnection attempt
        if self.is_connected and self.dg_connection:
            try:
                await self.dg_connection.send(audio_chunk)
                return True
            except Exception as e:
                print(f"Error sending audio to Deepgram: {e}")
                self.is_connected = False
                return False
        else:
            print("Cannot send audio: Deepgram connection still not active after reconnection attempt.")
            return False

    async def finish(self):
        if self.dg_connection:
            await self.dg_connection.finish()
            print("Deepgram connection finished.")
        self.is_connected = False


async def start_deepgram_connection(transcript_callback=None):
    deepgram_conn = DeepgramConnection(transcript_callback)
    await deepgram_conn.connect()
    return deepgram_conn

async def stop_deepgram_connection(deepgram_conn):
    await deepgram_conn.finish()

async def send_audio_to_deepgram(deepgram_conn, audio_chunk):
    await deepgram_conn.send_audio(audio_chunk)

def is_deepgram_connected(deepgram_conn):
    return deepgram_conn.is_connected
