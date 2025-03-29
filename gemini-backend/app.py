from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import os
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "AlzaSyAnqUVoRXrE-hWTavT7TP32YByahRFVoE"))

@app.route('/ask', methods=['POST'])
def ask_gemini():
    data = request.json
    user_input = data.get("question", "")

    if not user_input:
        return jsonify({"error": "No question provided"}), 400

    # Use the older, more compatible API
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(user_input)
    
    return jsonify({"response": response.text})

@app.route('/ask-stream', methods=['POST'])
def ask_gemini_stream():
    data = request.json
    user_input = data.get("question", "")

    if not user_input:
        return jsonify({"error": "No question provided"}), 400

    model = genai.GenerativeModel('gemini-pro')
    
    def generate():
        response = model.generate_content(
            user_input,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield f"data: {chunk.text}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
