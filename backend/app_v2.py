from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import traceback
import base64

from speech import process_audio_to_text
from voice import process_text_to_audio
from text_to_sign_v2 import process_text_to_sign  # Updated to use video support
from camera import process_frame_for_sign

app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/text-to-sign", methods=["POST"])
def text_to_sign_api():
    try:
        data = request.json or {}
        text = data.get("text", "")
        result = process_text_to_sign(text)
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        print(f"Error in text-to-sign: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/voice-to-text", methods=["POST"])
def voice_to_text_api():
    try:
        if "audio" not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        text = process_audio_to_text(audio_file)
        return jsonify({"success": True, "text": text})

    except Exception as e:
        print(f"Error in voice-to-text: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/sign-to-text", methods=["POST"])
def sign_to_text_api():
    try:
        data = request.json
        if "image" not in data:
            return jsonify({"success": False, "error": "No image data provided"}), 400

        img_str = data["image"].split(",")[1] if "," in data["image"] else data["image"]
        img_data = base64.b64decode(img_str)
        text = process_frame_for_sign(img_data)

        if text:
            return jsonify({"success": True, "text": text})
        return jsonify({"success": True, "text": ""})

    except Exception as e:
        print(f"Error in sign-to-text: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/text-to-speech", methods=["POST"])
def text_to_speech_api():
    try:
        data = request.json
        text = data.get("text", "")

        if not text:
            return jsonify({"success": False, "error": "No text provided"}), 400

        audio_url = process_text_to_audio(text)
        return jsonify({"success": True, "audio_url": audio_url})

    except Exception as e:
        print(f"Error in text-to-speech: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
