from flask import Flask, request, jsonify, render_template, send_file
import requests
import speech_recognition as sr
from gtts import gTTS


# Initialize the recognizer
app = Flask(__name__)

recognizer = sr.Recognizer()
# Rasa endpoint URL
rasa_url = "http://localhost:5005"

def send_to_rasa(text):
    endpoint = f"{rasa_url}/webhooks/rest/webhook"
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
    return render_template("flask.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    message = request.form["message"]
    rasa_response = send_to_rasa(message)
        
    tts = gTTS(text = rasa_response,lang = "ar")
    tts.save('Rasa_answer/answer.mp3')
    # return jsonify({"message": rasa_response})
        # Return the URL of the MP3 file
    return jsonify({"audio_url": "/stream_audio","message": rasa_response})

@app.route("/stream_audio")
def stream_audio():
    return send_file('Rasa_answer/answer.mp3', mimetype='audio/mpeg')


@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    # Check if the POST request has the file part
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'})
    
    audio_file = request.files['audio']
    
    # Check if the file is empty
    if audio_file.filename == '':
        return jsonify({'error': 'No selected audio file'})

    audio_file.save('uploads/recording.wav')
    
    with sr.AudioFile('uploads/recording.wav') as source:
        audio = recognizer.listen(source)
        # Recognize the speech with the chosen language
        rasa_response = recognizer.recognize_google(audio, language="ar-EG")

    # Return a success response
    return jsonify({'message': rasa_response})

if __name__ == "__main__":
    app.run(debug=True,host = '0.0.0.0')
