from flask import Flask, request, jsonify, render_template, send_file
import requests
import speech_recognition as sr
from gtts import gTTS

"""
This is a Flask application that interacts with a Rasa chatbot through HTTP requests.
"""

app = Flask(__name__)

recognizer = sr.Recognizer()
RASA_URL = "http://localhost:5005"







import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(
    api_key='25ac2695ad6b513ea9ad2b9467a8e30e',
)



def text_to_speech_file(text: str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2", # use the turbo model for low latency, for other languages use the `eleven_multilingual_v2`
        voice_settings=VoiceSettings(
            stability=0.4,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # uncomment the line below to play the audio back
    # play(response)

    # Generating a unique file name for the output MP3 file
    save_file_path = "Rasa_answer/answer.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    # Return the path of the saved audio file
    return save_file_path








def send_to_rasa(text):
    """
    Send a message to Rasa server and get the response.

    Args:
        text (str): The message to send to Rasa.

    Returns:
        str: The response from Rasa.
    """
    endpoint = f"{RASA_URL}/webhooks/rest/webhook"
    data = {"sender": "user", "message": text}

    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        rasa_response = response.json()

        if rasa_response and len(rasa_response) > 0:
            return rasa_response[0]["text"]
        else:
            return "Rasa did not provide a valid response."

    except requests.exceptions.RequestException as e:
        print("Error connecting to Rasa server:", e)
        return None

@app.route("/")
def index():
    """
    Render the index page.
    """
    return render_template("flask.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    """
    Handle sending message to Rasa server and returning the response.
    """
    message = request.form["message"]
    rasa_response = send_to_rasa(message)
    text_to_speech_file(rasa_response)

    
    # tts = gTTS(text=rasa_response, lang="ar")
    # tts.save('Rasa_answer/answer.mp3')
    return jsonify({"audio_url": "/stream_audio", "message": rasa_response})

@app.route("/stream_audio")
def stream_audio():
    """
    Stream the saved audio file.
    """
    return send_file('Rasa_answer/answer.mp3', mimetype='audio/mpeg')

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Handle uploading audio file, transcribing it, and returning the transcript.
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'})

    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({'error': 'No selected audio file'})

    audio_file.save('uploads/recording.wav')

    with sr.AudioFile('uploads/recording.wav') as source:
        audio = recognizer.listen(source)
        rasa_response = recognizer.recognize_google(audio, language="ar-EG")

    return jsonify({'message': rasa_response})


if __name__ == "__main__":
    app.run(debug=True,host = '0.0.0.0')
