from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import random
import string
import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables securely
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Check if the environment variables are loaded correctly
if not FIREBASE_CREDENTIALS or not GENAI_API_KEY or not GOOGLE_MAPS_API_KEY:
    raise ValueError("Missing required environment variables. Check your .env file.")

# Build the correct path to the firebase_credentials.json file
cred_path = os.path.join(os.getcwd(), FIREBASE_CREDENTIALS)
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Firebase credentials file not found at {cred_path}")

# Initialize Flask App
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure AI API (Gemini)
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize geolocator
geolocator = Nominatim(user_agent="emergency_alert_app")

# Log incoming requests
@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.url} - Data: {request.json}")


def generate_unique_id():
    """Generate a unique 12-character user ID."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))


@app.route("/register", methods=["POST"])
def register_user():
    """Register a new user and store data in Firestore."""
    data = request.json
    user_id = generate_unique_id()
    db.collection("users").document(user_id).set(data)
    return jsonify({"message": "User registered", "user_id": user_id})


@app.route("/send_alert", methods=["POST"])
def send_alert():
    """Send an alert to nearby responders."""
    data = request.json
    location = data.get("location")
    alert_message = data.get("message")

    if not location or not alert_message:
        return jsonify({"error": "Missing required fields"}), 400

    ai_message = get_ai_response(alert_message)
    responders = []
    users = db.collection("users").stream()

    for user in users:
        user_data = user.to_dict()
        if "location" in user_data and is_within_range(location, user_data["location"], 5):
            responders.append(user_data.get("contact"))
            send_push_notification(user_data.get("fcm_token"), ai_message)

    socketio.emit("new_alert", {"message": ai_message, "location": location})
    return jsonify({"message": ai_message, "responders_alerted": responders})


def get_ai_response(user_input):
    """Generate an AI-powered emergency response."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_input)
        return response.text if response else "No valid AI response generated."
    except Exception as e:
        logging.error(f"AI error: {e}")
        return f"AI error: {e}"


def is_within_range(origin, destination, max_distance_km):
    """Check if the responder is within the range of the alert."""
    try:
        distance = geodesic(origin, destination).km
        return distance <= max_distance_km
    except Exception as e:
        logging.error(f"Error calculating distance: {e}")
        return False


def send_push_notification(fcm_token, message):
    """Send a push notification to responders."""
    try:
        if not fcm_token:
            return
        message = messaging.Message(
            notification=messaging.Notification(
                title="Emergency Alert",
                body=message
            ),
            token=fcm_token
        )
        messaging.send(message)
    except Exception as e:
        logging.error(f"Error sending push notification: {e}")


if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, host="0.0.0.0", port=5000)
