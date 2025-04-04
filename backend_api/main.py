from fastapi import FastAPI

# Create a minimal FastAPI application
app = FastAPI()

# Define a simple route for the root URL
@app.get("/")
async def read_root():
    return {"message": "Hello! Minimal API is running."}
