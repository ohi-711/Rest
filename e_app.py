from dotenv import load_dotenv
from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    data = request.get_json()
    user_text = data['text']

    prompt = f"Analyze the following text for simple emotions such as happy, scared, angry. If no real emotion, then neutral: \"{user_text}\""
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a emotion therapist."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )

    analysis = response.choices[0].message['content'].strip()

    emotion = "neutral"

    if any(keyword in analysis for keyword in ["sad", "down", "unhappy"]):
        emotion = "sadness"
    elif any(keyword in analysis for keyword in ["stressed", "anxious", "overwhelmed"]):
        emotion = "stressed"
    elif any(keyword in analysis for keyword in ["happy", "joyful", "excited"]):
        emotion = "happy"
    elif any(keyword in analysis for keyword in ["angry", "mad", "furious"]):
        emotion = "anger"
    elif any(keyword in analysis for keyword in ["scared", "fearful", "afraid"]):
        emotion = "fear"
    elif any(keyword in analysis for keyword in ["surprised", "amazed", "astonished"]):
        emotion = "surprise"

    neutral_keywords = ["regular", "boring", "uneventful","nothing"]
    if emotion == "neutral" and all(keyword in user_text.lower() for keyword in neutral_keywords):
        emotion = "neutral"

    return jsonify({"emotion": emotion})

if __name__ == '__main__':
    app.run(debug=True)