# ArtSensei - Conversational Art Assistant

## Project Overview

ArtSensei is a web application designed to act as a conversational AI assistant focused on art. It integrates real-time voice transcription and image analysis, allowing users to speak with the AI and discuss images they upload.

The primary interaction model is voice-to-voice (though text-to-speech output is pending), with the AI capable of understanding spoken queries and analyzing visual content provided by the user within the same conversational context.

## Core Features

*   **Real-time Voice Transcription:** Uses Deepgram's streaming API via WebSockets to transcribe user speech in real-time.
*   **AI Text Analysis:** Integrates with Google Gemini API to understand and respond to user queries.
*   **Image Analysis:** Leverages Google Gemini Vision model to analyze images uploaded by the user.
*   **Integrated Conversation Context:** Maintains a shared context between voice interactions and image analysis, allowing users to ask follow-up questions about previously discussed images.
*   **WebSocket Communication:** Facilitates real-time, bidirectional communication between the frontend and backend.

## Technology Stack

*   **Backend:** Python, FastAPI
*   **Real-time Audio:** Deepgram API
*   **AI / Vision:** Google Gemini API
*   **WebSockets:** FastAPI WebSockets
*   **Frontend:** HTML, CSS, JavaScript (minimalist test frontend)

## Development Plan & Next Steps

This project follows an iterative development process, prioritizing core functionality and testability at each stage (Minimalist Implementation Rule).

**Completed Milestones:**

1.  **Backend Foundation:** Established a FastAPI backend with WebSocket support (`src/main.py`).
2.  **Real-time Transcription:** Integrated Deepgram for streaming speech-to-text (`src/deepgram_client.py`).
3.  **AI Text Analysis:** Integrated Google Gemini for understanding user queries (`src/gemini_integration.py`).
4.  **Image Analysis:** Added Gemini Vision capabilities for analyzing uploaded images (`src/gemini_integration.py`, `frontend_test/app.js`).
5.  **Context Integration:** Implemented a conversation manager (`src/conversation_context.py`) to maintain context between voice queries and image analysis.
6.  **Basic Frontend:** Created a simple HTML/JS frontend for testing core functionalities (`frontend_test/`).

**Current Focus / Next Steps:**

1.  **Text-to-Speech (TTS) & Captions:** Implement audio playback for AI responses (via TTS API or browser built-in `SpeechSynthesis`) to achieve full voice-to-voice interaction. Simultaneously, display the AI's text response as on-screen captions.
2.  **Frontend Enhancement (Mobile-First & Camera):** Refine the frontend UI with a mobile-first responsive design. Integrate camera access, specifically targeting the rear (environment-facing) camera, allowing users to capture images directly within the app as an alternative to file upload.
3.  **Error Handling & Robustness:** Improve error handling and user feedback on both frontend and backend for scenarios like API failures, permission denials (mic/camera), or network issues.
4.  **Deployment:** Plan and execute deployment to a suitable cloud platform.

## Project Structure

```
/Users/robcolvin/ArtSensei/New Build/
├── art_sensei/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── conversation_context.py  # Manages conversation history
│   │   ├── deepgram_client.py       # Handles Deepgram connection
│   │   ├── gemini_integration.py    # Handles Gemini API calls
│   │   └── main.py                  # FastAPI application, WebSocket endpoint
│   ├── frontend_test/
│   │   ├── index.html               # Main HTML page
│   │   └── app.js                   # Frontend JavaScript logic
│   └── requirements.txt           # Backend Python dependencies
├── .env                           # Environment variables (API Keys)
├── .gitignore
└── README.md                      # This file
```

## Setup and Installation

1.  **Clone the Repository:** (Assuming you have the code)
2.  **Create Environment Variables:**
    *   Create a `.env` file in the root directory (`/Users/robcolvin/ArtSensei/New Build/.env`).
    *   Add your API keys:
        ```dotenv
        DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        ```
3.  **Install Backend Dependencies:**
    *   Navigate to the `art_sensei` directory: `cd "/Users/robcolvin/ArtSensei/New Build/art_sensei"`
    *   Create and activate a Python virtual environment (recommended):
        ```bash
        python -m venv venv
        source venv/bin/activate  # Mac/Linux
        # venv\Scripts\activate  # Windows
        ```
    *   Install requirements:
        ```bash
        pip install -r requirements.txt
        ```

## Running the Application

1.  **Start the Backend Server:**
    *   Ensure you are in the `/Users/robcolvin/ArtSensei/New Build/art_sensei` directory with the virtual environment activated.
    *   Run the FastAPI server:
        ```bash
        python -m src.main
        ```
    *   The server will typically start on `http://127.0.0.1:8000`.
2.  **Open the Frontend:**
    *   Open the `art_sensei/frontend_test/index.html` file in your web browser.
    *   The frontend will attempt to connect to the WebSocket endpoint (`ws://localhost:8000/ws`).

## Usage

1.  Click "Connect" to establish the WebSocket connection.
2.  Click "Start Recording" to begin streaming audio to Deepgram for transcription.
3.  Speak your query.
4.  Transcriptions and AI responses will appear in the text area.
5.  To analyze an image, click "Choose File", select an image, and click "Submit".
6.  The image analysis result will appear, and the conversation context will include the image.
7.  You can then ask follow-up questions about the image via voice.
8.  Click "Stop Recording" to end the audio stream.