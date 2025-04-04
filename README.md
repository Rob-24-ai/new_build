# Build Plan

**Project Goal:** Build a web application integrating an ElevenLabs conversational AI agent with a custom image analysis backend API, allowing the agent to discuss images provided by the user either via file upload or direct camera capture.

**Core Components:**

1. **Frontend Web Application:** The user interface (UI) where the user interacts, including voice controls and mechanisms for uploading or capturing images.
2. **Backend Image Analysis API:** A web service (API) that receives image data (or a URL), runs your Python image analysis logic (based on `ArtSensei_Main`), and returns structured analysis results (JSON).
3. **ElevenLabs Conversational AI Agent:** Configured on the ElevenLabs platform to handle voice interaction and use the custom Backend API as a "tool".

**Revised Development Plan:**

**Phase 1: Develop the Backend Image Analysis API**

- **Objective:** Create a stable, deployable web API that exposes your image analysis functionality.
- **Technology:** Python with FastAPI or Flask.
- **Steps:**
    1. **Setup:** Python project, virtual environment, install dependencies (FastAPI/Flask, `uvicorn`, `requests`, `Pillow`, any `ArtSensei_Main` libraries), manage with `requirements.txt`.
    2. **Integrate Logic:** Adapt `ArtSensei_Main` Python code into callable functions that accept image input (URL, file path, or bytes) and return a Python dictionary with analysis results.
    3. **Define API Endpoint:**
        - Endpoint: e.g., `/analyze-image/`
        - Method: `POST`
        - Input: Primarily expect an image URL (e.g., `{"image_url": "https://.../image.jpg"}`). The frontend will be responsible for getting the image (from upload or camera) to a hosted URL first. Alternatively, design to accept Base64 encoded data if direct upload to the analysis API is preferred, though URL is often simpler for tool integration.
        - Processing: Fetch image from URL (or decode data), pass to analysis functions.
        - Output: Return a clearly defined JSON structure (e.g., `{"description": "...", "style": "...", "objects_detected": [...]}`). Document this structure.
    4. **Testing:** Test locally (e.g., Postman, `curl`, FastAPI docs).
    5. **Deployment:** Deploy to a cloud platform (Google Cloud Run, AWS Lambda + API Gateway, Heroku, etc.) ensuring a public HTTPS URL.

**Phase 2: Configure the ElevenLabs Agent**

- **Objective:** Set up the ElevenLabs agent to understand when and how to use your image analysis API.
- **Platform:** ElevenLabs Conversational AI interface.
- **Steps:**
    1. **Agent Setup:** Create/configure the voice agent (voice, personality).
    2. **Define Tool:**
        - Add a new tool (e.g., `image_analyzer`).
        - **Description:** Clearly explain its function (analyzes image from URL, returns description, etc.).
        - **API Endpoint URL:** The deployed URL from Phase 1.
        - **Method:** `POST`.
        - **Request Schema:** Define JSON input matching your API (e.g., `{"image_url": "string"}`).
        - **Response Schema:** Define JSON output matching your API's return structure.
    3. **Update Instructions:** Modify the agent's system prompt to guide it: "If the user provides an image URL and asks for analysis, use the `image_analyzer` tool with that URL."
    4. **Testing:** Use the ElevenLabs platform tester to verify tool invocation and response integration. Check backend API logs.

**Phase 3: Develop the Frontend Web Application**

- **Objective:** Build the user interface for voice interaction and image input via *both file upload and direct camera capture*.
- **Technology:** HTML, CSS, JavaScript (React, Vue, or Svelte recommended).
- **Steps:**
    1. **Setup:** Initialize web project structure.
    2. **UI Elements:**
        - **Voice Interaction:** Implement controls (record button, status display, audio playback) using ElevenLabs API/SDK for web. Handle authentication securely.
        - **Image Input:**
            - **File Upload:** Add `<input type="file" accept="image/*">`.
            - **Camera Capture:** Add a button to trigger `navigator.mediaDevices.getUserMedia`. Display live feed in `<video>`. Add a "Capture" button.
        - **Image Preview:** Area to show the selected/captured image thumbnail.
    3. **Frontend Logic:**
        - **File Upload Handling:** On file selection, read file (FileReader API), display preview. Upload file data to a designated storage (your own backend endpoint, or cloud service like S3/GCS) to get a stable URL. Store this URL.
        - **Camera Capture Handling:** On camera activation, request permission, stream to `<video>`. On capture, draw video frame to `<canvas>`, convert canvas to image data (e.g., `toDataURL` or `toBlob`), display preview. Upload this image data to storage to get a stable URL. Store this URL.
        - **Agent Interaction:**
            - User speaks/initiates interaction.
            - Frontend sends audio/text to ElevenLabs. Crucially, *include the stored image URL* in the context/prompt sent to the agent (e.g., append "Analyze the image at [stored_image_url]").
            - ElevenLabs processes, calls backend tool if triggered by prompt/instructions.
            - Backend API (Phase 1) analyzes image from URL, returns results to ElevenLabs.
            - ElevenLabs incorporates results into its spoken response.
            - Frontend receives and plays the agent's audio response.
    4. **State Management:** Manage application state (conversation history, image URL, loading indicators, camera status, permissions).
    5. **Styling:** Apply CSS for desired appearance and usability.

**Phase 4: Integration, Testing, and Deployment**

- **Objective:** Ensure all components work together reliably and deploy the full application.
- **Steps:**
    1. **End-to-End Testing:** Thoroughly test the complete workflow: image upload, camera capture, voice interaction triggering analysis, correct agent response based on analysis. Test on different devices/browsers if possible.
    2. **Error Handling:** Implement user feedback for errors (API failures, camera permission denied, invalid uploads, network issues).
    3. **Security Review:** Protect API keys (use environment variables), validate inputs, consider security of image storage.
    4. **Deployment:** Deploy frontend (Netlify, Vercel, GitHub Pages, etc.). Ensure backend API (Phase 1) is running and accessible.


# Build Part 1 
# New Build Phase 1: Image Analysis

Okay, let's break down **Phase 1: Develop the Backend Image Analysis API** into super simple, step-by-step instructions. We'll use Python and a framework called FastAPI because it's modern and helps create APIs relatively easily.

Imagine you're building a small, specialized website (an API) that only does one thing: analyze an image when asked.

Goal for Phase 1: Create a basic program running on your computer that can:

a) Receive a request containing a link (URL) to an image.

b) Fetch that image from a web-based camera or phone upload. 

c) Run your specific image analysis code on it.

d) Send back the analysis results.

**Tools You'll Need:**

- **Python:** A programming language. (Make sure Python 3 is installed. Open your Terminal or Command Prompt and type `python --version` or `python3 --version`. If not installed, download from [python.org](https://www.python.org/)).
- **Pip:** Python's package installer (usually comes with Python). Check with `pip --version` or `pip3 --version`.
- **A Code Editor:** A program to write code in. Visual Studio Code (VS Code) is free and excellent ([code.visualstudio.com](https://code.visualstudio.com/)). Notepad works, but a code editor is much better.
- **Terminal or Command Prompt:** The text-based window for running commands on your computer.

**Step-by-Step Guide for Phase 1:**

1. **Create a Project Folder:**
    - **Why?** To keep all the files for this API project organized in one place.
    - **How?** On your Desktop or Documents folder, create a new folder. Let's name it `ArtSensei_API`.
    - Open your Terminal or Command Prompt.
    - Navigate *into* that folder using the `cd` (change directory) command. Example: `cd Desktop/ArtSensei_API` (adjust path as needed). You'll run most future commands from *inside* this folder.
2. **Create a "Virtual Environment":**
    - **Why?** Think of it as a clean, isolated workspace *just for this project*. Any tools (packages) you install for this project won't mess up other Python projects on your computer, and vice-versa.
    - **How?** In your terminal (make sure you're inside the `ArtSensei_API` folder), run:
    Bash
    (Or `python3 -m venv venv` if `python` doesn't work). This creates a sub-folder named `venv` containing a copy of Python and Pip just for this project.
        
        ```bash
        python -m venv venv
        ```
        
    - **Activate it:** You need to "turn on" this environment each time you work on the project.
        - **Windows:** `.\venv\Scripts\activate`
        - **Mac/Linux:** `source venv/bin/activate`
    - **Check:** Your terminal prompt should now start with `(venv)`. If you see that, it's active!
3. **Install Necessary Python Packages:**
    - **Why?** These are pre-written pieces of code (libraries) that help you build things faster. We need tools for creating the API, running the server, handling images, and fetching images from URLs.
    - **How?** With your virtual environment active (`(venv)` showing), run these commands one by one in the terminal:
        
        ```bash
        pip install fastapi
        pip install "uvicorn[standard]"
        pip install Pillow
        pip install requests
        ```
        
        - `fastapi`: The main tool for building the API.
        - `uvicorn`: The server program that runs your FastAPI application. `[standard]` includes helpful extras.
        - `Pillow`: A library for working with images (opening, manipulating).
        - `requests`: A library for fetching data from URLs (like downloading the image).
4. **Create the Main API Code File:**
    - **Why?** This file will hold the instructions for your API.
    - **How?** Using your code editor (like VS Code), create a new file directly inside your `ArtSensei_API` folder. Save it as `main.py`.
5. **Write Extremely Basic API Code (in `main.py`):**
    - **Why?** Let's start simple to make sure things are working. This code just creates a "homepage" for your API.
    - **How?** Copy and paste this exact code into your `main.py` file:
        
        ```python
        from fastapi import FastAPI
        
        # Create an instance of the FastAPI application
        app = FastAPI()
        
        # Define a "route" for the main URL ("/")
        # When someone visits the base URL, this function runs
        @app.get("/")
        async def read_root():
            # Return a simple message as JSON
            return {"message": "Hello! Image Analysis API is waiting."}
        ```
        
6. **Run Your Basic API:**
    - **Why?** To test if the minimal code works and the server starts.
    - **How?** Go back to your terminal (still inside `ArtSensei_API`, with `(venv)` active). Run:
        
        ```bash
        uvicorn main:app --reload
        ```
        
        - `main`: Refers to your `main.py` file.
        - `app`: Refers to the `app = FastAPI()` object you created in the code.
        - `-reload`: Tells the server to automatically restart if you save changes to `main.py`.
    - **Check:** Look for lines saying something like `Uvicorn running on http://127.0.0.1:8000`. This means it's working locally!
    - **Verify:** Open a web browser and go to `http://127.0.0.1:8000`. You should see: `{"message": "Hello! Image Analysis API is waiting."}`. If you see that, success! You can leave `uvicorn` running.
7. **Prepare Your Image Analysis Logic:**
    - **Why?** You need the actual code that knows how to analyze an image (from your `ArtSensei_Main` project).
    - **How?**
        - Find the specific Python function(s) in your `ArtSensei_Main` code that perform the image analysis.
        - **Option A (Simpler):** If the analysis code is short, copy and paste the function(s) directly into `main.py`.
        - **Option B (Cleaner):** Create a *new file* in your `ArtSensei_API` folder named `analyzer.py`. Copy the analysis function(s) into this file. You'll then import them into `main.py` later using `from analyzer import your_function_name`.
        - **Modify the function:** Make sure the analysis function is set up to receive an image (ideally as a Pillow Image object, which we'll create in the next step) and return the results as a Python dictionary (e.g., `{'description': '...', 'colors': [...]}`).
        - **Check Dependencies:** If your analysis code needs *other* Python libraries that we haven't installed yet, install them now using `pip install library_name` and add them to a `requirements.txt` file (see step 12).
8. **Create the Real API Endpoint for Analysis (in `main.py`):**
    - **Why?** This is the specific part of your API that ElevenLabs will contact. It needs to accept the image URL, fetch the image, analyze it, and return the results.
    - **How?** Add the following code to your `main.py` file (below the `read_root` function). Read the comments carefully to understand each part:
        
        ```python
        # Add these imports at the top of main.py with the others
        from pydantic import BaseModel, HttpUrl # For defining expected input
        import requests # For fetching image from URL
        from PIL import Image # For opening the image
        import io # For handling image data in memory
        
        # If you used Option B in Step 7, import your function:
        # from analyzer import your_actual_analysis_function
        
        # Define what data structure we expect to receive in the request
        # It must be JSON with a key "image_url" containing a valid web address
        class ImageRequest(BaseModel):
            image_url: HttpUrl
        
        # Define the actual endpoint: accepts POST requests at /analyze-image/
        @app.post("/analyze-image/")
        async def analyze_image_endpoint(request: ImageRequest):
            """
            Receives an image URL, fetches the image, runs analysis (dummy for now),
            and returns the results.
            """
            try:
                # 1. Get the URL string from the incoming request
                the_url = str(request.image_url)
                print(f"Received request to analyze image URL: {the_url}") # Log to terminal
        
                # 2. Fetch the image content from the URL
                response = requests.get(the_url, stream=True)
                response.raise_for_status() # Important: Checks if the URL worked (no 404 etc.)
        
                # 3. Open the image data using Pillow
                # response.raw helps Pillow read the stream directly
                image_object = Image.open(response.raw)
                image_object.verify() # Check if it's a valid image file
                # Must re-open after verify for Pillow
                image_object = Image.open(response.raw)
        
                print(f"Successfully opened image from URL. Format: {image_object.format}, Size: {image_object.size}")
        
                # --- Replace this section with your ACTUAL analysis ---
                # 4. Call your image analysis function (using the 'image_object')
                # Example: analysis_results = your_actual_analysis_function(image_object)
        
                # For now, let's return dummy results:
                analysis_results = {
                    "status": "success",
                    "input_url": the_url,
                    "analysis": {
                        "description": "Dummy analysis: Image processed.",
                        "format_detected": image_object.format,
                        "width": image_object.size[0],
                        "height": image_object.size[1]
                    }
                }
                # --- End of placeholder analysis section ---
        
                print(f"Analysis complete. Returning results.")
                # 5. Return the results dictionary - FastAPI automatically converts it to JSON
                return analysis_results
        
            # Handle potential errors gracefully
            except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {e}")
                return {"status": "error", "message": f"Could not retrieve image from URL. Error: {e}"}
            except Image.UnidentifiedImageError:
                print(f"Error: URL did not point to a valid image.")
                return {"status": "error", "message": "The URL does not contain a valid image."}
            except Exception as e:
                # Catch any other unexpected problems
                print(f"An unexpected error occurred: {e}")
                return {"status": "error", "message": f"An unexpected error occurred: {e}"}
        ```
        
9. **Test Your New Endpoint:**
    - **Why?** To make sure the `/analyze-image/` part works correctly before connecting it to ElevenLabs.
    - **How?**
        - Make sure `uvicorn` is still running (or restart it: `uvicorn main:app --reload`).
        - Go back to your web browser and open `http://127.0.0.1:8000/docs`. This is FastAPI's automatic interactive documentation page.
        - You should now see your new endpoint listed: `POST /analyze-image/`. Click on it to expand.
        - Click the "Try it out" button.
        - In the "Request body" box, replace the example JSON with one containing a real image URL:
        (Use any public direct link to a JPG or PNG image).
            
            ```json
            {
              "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Felis_catus-cat_on_snow.jpg/1200px-Felis_catus-cat_on_snow.jpg"
            }
            ```
            
        - Click the "Execute" button.
        - Scroll down to the "Responses" section. If it worked, the "Response body" should show the JSON output from your code (the dummy results for now), and the "Code" should be `200`. If you get an error (like 4xx or 5xx code), check the response body and your `uvicorn` terminal output for error messages. Try different image URLs.
10. **Save Your Dependencies:**
    - **Why?** Creates a list of all the packages your project needs, making it easy for someone else (or a server) to install them all at once.
    - **How?** In your terminal (with `(venv)` active), run:
    Bash
    This creates a `requirements.txt` file listing `fastapi`, `uvicorn`, `Pillow`, `requests`, etc.
        
        `pip freeze > requirements.txt`
        

**Congratulations!** If you've reached this point and the `/docs` page lets you successfully "execute" the `/analyze-image/` endpoint with a test URL, you have completed the core goal of Phase 1. You have a basic API running locally that can accept an image URL, fetch the image, and (theoretically, using your placeholder/real function) analyze it.

The *next* major step (outside this detailed Phase 1 breakdown) would be **Deployment**: putting this code on a server online so ElevenLabs can reach it via a public HTTPS web address. But for now, you have the local foundation built.