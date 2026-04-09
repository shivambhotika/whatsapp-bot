import os, tempfile, requests
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
def transcribe_audio(media_url, content_type):
    ext = ".ogg" if "ogg" in content_type else ".mp4"
    r = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=30)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(r.content); tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            return openai_client.audio.transcriptions.create(model="whisper-1", file=f).text
    finally:
        os.unlink(tmp_path)
@app.route("/webhook", methods=["POST"])
def webhook():
    twiml = MessagingResponse()
    if int(request.values.get("NumMedia", 0)) == 0:
        twiml.message("👋 Send me a voice note and I'll transcribe it! 🎙️")
        return Response(str(twiml), mimetype="text/xml")
    media_url = request.values.get("MediaUrl0", "")
    content_type = request.values.get("MediaContentType0", "")
    if "audio" not in content_type and "ogg" not in content_type:
        twiml.message("Please send an audio/voice note!")
        return Response(str(twiml), mimetype="text/xml")
    try:
        transcript = transcribe_audio(media_url, content_type)
        twiml.message(f"📝 *Transcription:*\n\n{transcript}" if transcript.strip() else "🔇 Audio too short.")
    except Exception as e:
        print(f"[ERROR] {e}"); twiml.message("⚠️ Could not transcribe. Please try again.")
    return Response(str(twiml), mimetype="text/xml")
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
