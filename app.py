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
    tts = gTTS(text=rasa_response, lang="ar")
    tts.save('Rasa_answer/answer.mp3')
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
