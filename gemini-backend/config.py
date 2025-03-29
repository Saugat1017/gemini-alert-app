import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase credentials path
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
