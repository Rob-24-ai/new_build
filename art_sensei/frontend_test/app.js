const connectButton = document.getElementById('connectButton');
const disconnectButton = document.getElementById('disconnectButton');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const statusDiv = document.getElementById('status');
const transcriptionDiv = document.getElementById('transcription'); // Get transcription display area
const transcriptDiv = document.getElementById('transcript');

// Image analysis elements
const imageUploadInput = document.getElementById('imageUpload');
const analyzeImageBtn = document.getElementById('analyzeImageBtn');
const imagePreviewDiv = document.getElementById('imagePreview');

let websocket = null;
let mediaRecorder = null;
let audioChunks = [];
let lastTranscript = ''; // Store last transcript for deduplication
const WS_URL = 'ws://localhost:8000/ws'; // Your FastAPI WebSocket URL

function updateStatus(message) {
    statusDiv.textContent = `Status: ${message}`;
}

function updateTranscript(message) {
    // NOTE: Backend currently prints transcript, doesn't send back.
    // This is placeholder for future enhancement.
    // transcriptDiv.textContent = `Transcript: ${message}`;
    console.log("Server message (raw):", message); // Log raw messages for now
}

// Function to display received transcripts
function displayTranscription(message) {
    // Skip exact duplicates
    if (message === lastTranscript) {
        console.log('Skipping duplicate transcript:', message);
        return;
    }
    
    // Skip partial transcripts (when the new message is contained in the last one)
    if (lastTranscript.includes(message)) {
        console.log('Skipping partial transcript:', message);
        return;
    }
    
    // Skip if this message is just an extension of the previous one
    // (When the last message is contained in the new one)
    if (message.includes(lastTranscript) && lastTranscript.length > 3) {
        console.log('Replacing with more complete transcript');
        // Remove the last message from display
        if (transcriptionDiv && transcriptionDiv.lastChild) {
            transcriptionDiv.removeChild(transcriptionDiv.lastChild);
        }
    }
    
    // Store this message as the last one seen
    lastTranscript = message;
    
    const p = document.createElement('p');
    p.textContent = message;
    p.style.color = '#0066cc'; // Blue color for user messages
    if (transcriptionDiv) {
        transcriptionDiv.appendChild(p);
        // Auto-scroll
        transcriptionDiv.scrollTop = transcriptionDiv.scrollHeight;
    }
}

// Function to display AI responses
function displayAIResponse(message) {
    const p = document.createElement('p');
    p.textContent = message;
    p.style.color = '#006600'; // Green color for AI messages
    p.style.fontWeight = 'bold';
    if (transcriptionDiv) {
        transcriptionDiv.appendChild(p);
        // Auto-scroll
        transcriptionDiv.scrollTop = transcriptionDiv.scrollHeight;
    }
}

// Function to display error messages
function displayError(message) {
    const p = document.createElement('p');
    p.textContent = message;
    p.style.color = '#cc0000'; // Red color for errors
    if (transcriptionDiv) {
        transcriptionDiv.appendChild(p);
        // Auto-scroll
        transcriptionDiv.scrollTop = transcriptionDiv.scrollHeight;
    }
}

connectButton.onclick = () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        updateStatus('Already connected.');
        return;
    }

    websocket = new WebSocket(WS_URL);
    updateStatus('Connecting...');
    
    // Check if the element exists before trying to clear it
    if (transcriptionDiv) {
        transcriptionDiv.innerHTML = ''; // Clear previous transcription on new connection
    }

    websocket.onopen = () => {
        updateStatus('Connected. Ready to Record.');
        connectButton.disabled = true;
        disconnectButton.disabled = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        
        // Enable image upload controls when connected
        imageUploadInput.disabled = false;
        analyzeImageBtn.disabled = true; // Will be enabled when an image is uploaded
    };

    websocket.onmessage = (event) => {
        console.log('Message received from server:', event.data);
        if (typeof event.data === 'string') {
            try {
                const messageData = JSON.parse(event.data);
                
                if (messageData.type === 'transcription') {
                    // User's transcribed speech
                    console.log('Transcription:', messageData.text);
                    displayTranscription('You: ' + messageData.text);
                } 
                else if (messageData.type === 'ai_response') {
                    // AI's response
                    console.log('AI Response:', messageData.text);
                    displayAIResponse('ArtSensei: ' + messageData.text);
                } 
                else if (messageData.type === 'ai_audio') {
                    // Handle incoming audio data
                    console.log("Received AI audio data.");
                    try {
                        // Decode Base64 string to binary data
                        const audioBytes = Uint8Array.from(atob(messageData.audio_base64), c => c.charCodeAt(0));
                        // Create a Blob from the bytes (assuming mp3 audio, adjust MIME type if necessary)
                        const audioBlob = new Blob([audioBytes], { type: 'audio/mpeg' });
                        // Create an object URL for the Blob
                        const audioUrl = URL.createObjectURL(audioBlob);
                        
                        // Stop any currently playing audio before starting new audio
                        if (window.currentAudio) {
                            console.log("Stopping previous audio...");
                            window.currentAudio.pause();
                            window.currentAudio.onended = null; // Remove previous event listener
                            URL.revokeObjectURL(window.currentAudio.src); // Clean up previous URL
                        }
                        
                        // Create an Audio object and play it
                        const audio = new Audio(audioUrl);
                        window.currentAudio = audio; // Store reference to current audio
                        
                        console.log("Playing AI audio...");
                        audio.play();
                        
                        // Optional: Revoke the object URL after playback finishes to free memory
                        audio.onended = () => {
                            URL.revokeObjectURL(audioUrl);
                            console.log("AI audio finished playing and URL revoked.");
                            window.currentAudio = null;
                        };
                        audio.onerror = (e) => {
                            console.error("Error playing audio:", e);
                            URL.revokeObjectURL(audioUrl); // Clean up URL on error too
                            window.currentAudio = null;
                        };

                    } catch (error) {
                        console.error("Error processing or playing AI audio:", error);
                    }
                }
                else if (messageData.type === 'error') {
                    console.error('Error from server:', messageData.text);
                    displayError('Error: ' + messageData.text);
                }
                else if (messageData.type === 'command') {
                    // Handle server commands
                    console.log('Command from server:', messageData.action);
                    if (messageData.action === 'enable_analyze_button') {
                        analyzeImageBtn.disabled = false;
                        
                        // Ensure recording status is maintained after image analysis
                        if (mediaRecorder && mediaRecorder.state === 'recording') {
                            updateStatus('Recording... (Image analysis complete)');
                        } else if (websocket && websocket.readyState === WebSocket.OPEN) {
                            updateStatus('Connected. Ready to record or analyze another image.');
                        }
                    }
                }
                else {
                    // For backward compatibility with plain text messages
                    displayTranscription(event.data);
                }
            } catch (error) {
                // For backward compatibility with plain text messages
                console.log('Received plain text message:', event.data);
                displayTranscription(event.data);
            }
        } else {
            console.warn("Received non-string message:", event.data);
            // Handle binary data if needed
        }
    };

    websocket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        updateStatus('Connection Error.');
        alert('WebSocket error. Check console.');
        // Reset UI potentially
        connectButton.disabled = false;
        disconnectButton.disabled = true;
        startButton.disabled = true;
        stopButton.disabled = true;
    };

    websocket.onclose = (event) => {
        console.log('WebSocket Closed:', event.code, event.reason);
        updateStatus(`Disconnected (${event.code})`);
        websocket = null;
        connectButton.disabled = false;
        disconnectButton.disabled = true;
        startButton.disabled = true;
        stopButton.disabled = true;
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
        mediaRecorder = null;
    };
};

disconnectButton.onclick = () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close(1000, 'User disconnected'); // Normal closure
    }
    updateStatus('Disconnecting...');
};

startButton.onclick = async () => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        alert('Connect to WebSocket first.');
        return;
    }
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        updateStatus('Already recording.');
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = []; // Clear previous chunks
        console.log("MediaRecorder created and ready.");

        mediaRecorder.ondataavailable = (event) => {
            console.log(`ondataavailable triggered. Data size: ${event.data.size}`);
            if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
                // Send the audio chunk as binary data
                websocket.send(event.data);
                console.log(`Sent audio chunk: ${event.data.size} bytes`);
            } else {
                if (event.data.size <= 0) console.log("Skipping empty audio chunk.");
                if (!websocket || websocket.readyState !== WebSocket.OPEN) console.log("WebSocket not open, cannot send.");
            }
        };

        mediaRecorder.onstop = () => {
            updateStatus('Recording stopped. Ready to Record.');
            startButton.disabled = false;
            stopButton.disabled = true;
            stream.getTracks().forEach(track => track.stop()); // Release microphone
        };

        mediaRecorder.onerror = (error) => {
            console.error('MediaRecorder Error:', error);
            alert('Error during recording. Check console.');
            updateStatus('Recording Error.');
            startButton.disabled = false;
            stopButton.disabled = true;
        };

        // Start recording and send chunks frequently (e.g., every 250ms)
        mediaRecorder.start(250); // Slice recording into chunks
        updateStatus('Recording...');
        console.log("MediaRecorder started.");
        startButton.disabled = true;
        stopButton.disabled = false;

    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('Could not access microphone. Please grant permission.');
        updateStatus('Microphone access denied or error.');
    }
};

stopButton.onclick = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    // Status update happens in mediaRecorder.onstop
};

// Image upload preview handling
imageUploadInput.onchange = () => {
    const file = imageUploadInput.files[0];
    if (file) {
        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => {
            // Clear previous preview
            imagePreviewDiv.innerHTML = '';
            
            // Create image element
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.maxWidth = '100%';
            imagePreviewDiv.appendChild(img);
            
            // Enable the analyze button
            analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    } else {
        imagePreviewDiv.innerHTML = '';
        analyzeImageBtn.disabled = true;
    }
};

// Image analysis button click handler
analyzeImageBtn.onclick = async () => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        alert('WebSocket connection is not open. Please reconnect.');
        return;
    }
    
    const file = imageUploadInput.files[0];
    if (!file) {
        alert('Please select an image first.');
        return;
    }
    
    // Store the current recording state so we can restore it
    const wasRecording = mediaRecorder && mediaRecorder.state === 'recording';
    
    try {
        // Show that we're processing
        updateStatus('Analyzing image...');
        analyzeImageBtn.disabled = true;
        
        // We could directly upload the image via WebSocket, but for simplicity,
        // let's convert it to a data URL and send that
        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUrl = e.target.result;
            
            // Create a message to send to the server
            const message = {
                type: 'analyze_image',
                dataUrl: dataUrl
            };
            
            // Send the message as a string
            websocket.send(JSON.stringify(message));
            
            // Display a message in the transcription area
            displayTranscription('You: [Image uploaded for analysis]');
            
            // The response will come back through the regular websocket.onmessage handler
            
            // If voice recording was active, make sure it stays active
            if (wasRecording) {
                updateStatus('Analyzing image while continuing to listen...');
            }
        };
        reader.readAsDataURL(file);
    } catch (error) {
        console.error('Error analyzing image:', error);
        updateStatus('Error analyzing image');
        analyzeImageBtn.disabled = false;
        displayError('Error: Failed to analyze image');
        
        // If recording was active, ensure it's still active
        if (wasRecording && (!mediaRecorder || mediaRecorder.state !== 'recording')) {
            startButton.click(); // Restart recording
        }
    }
};

// Initial state
updateStatus('Not Connected');
