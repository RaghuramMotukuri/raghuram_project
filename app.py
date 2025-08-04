# app.py
import os
import json
from flask import Flask, request, jsonify, render_template
import openai
from google.cloud import texttospeech

# === 1. Setup API Keys ===
# Replace with your actual OpenAI key
openai.api_key = "your-openai-api-key-here"

# Set the path to your Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# === 2. Load Festival Data ===
with open('festivals.json', 'r', encoding='utf-8') as f:
    festivals_data = json.load(f)

# === 3. Initialize Flask App ===
app = Flask(__name__)

# === 4. Helper: Find Festival Info ===
def get_festival_info(query):
    query = query.lower()
    for festival in festivals_data:
        if query in festival['name'].lower() or query in festival['english_name'].lower():
            return festival['description']
    return None  # Not found

# === 5. AI Response Generator (OpenAI) ===
def generate_telugu_response(user_query):
    # First, check if the festival exists in our data
    fest_info = get_festival_info(user_query)
    
    if fest_info:
        # Use the stored description
        prompt = f"ఈ పండుగ గురించి వివరించండి: {fest_info}. సరళమైన తెలుగులో స్పందించండి."
    else:
        # If not found, let AI explain generally
        prompt = (
            f"భారతదేశంలోని పండుగల గురించి తెలుగులో వివరించండి. "
            f"ప్రశ్న: '{user_query}'. "
            "స్పష్టమైన, స్నేహపూర్వకమైన తెలుగులో సమాధానం ఇవ్వండి."
        )

    # Ask OpenAI to generate response
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "మీరు ఉత్సవ మిత్ర, భారతీయ పండుగల గురించి తెలుగులో సమాచారం ఇచ్చే AI సహాయకుడు."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7  # Creativity level
    )

    # Extract and return the AI's reply
    return response.choices[0].message.content.strip()

# === 6. Text-to-Speech (Google) ===
def text_to_speech_telugu(text):
    client = texttospeech.TextToSpeechClient()

    # Set the input text
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Choose Telugu voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="te-IN",
        name="te-IN-Standard-A",  # Female voice
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Output format
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Generate audio
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Save audio to file
    audio_path = "static/output.mp3"
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)

    # Return URL to access audio
    return "/static/output.mp3"

# === 7. Web Routes ===

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Chat API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('message', '')

    # 1. Generate Telugu text
    telugu_text = generate_telugu_response(user_query)

    # 2. Convert to audio
    audio_url = text_to_speech_telugu(telugu_text)

    # 3. Send back text and audio
    return jsonify({
        'text': telugu_text,
        'audio': audio_url
    })

# === 8. Run the App ===
if __name__ == '__main__':
    app.run(debug=True)
