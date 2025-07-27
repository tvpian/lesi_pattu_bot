from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import subprocess, urllib.parse

app = Flask(__name__)

def yt_top_link(song):
    query = urllib.parse.quote_plus(song)
    result = subprocess.check_output(
        ["yt-dlp", f"ytsearch1:{query}", "--get-id"],
        text=True
    ).strip()
    return f"https://www.youtube.com/watch?v={result}"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    song_name = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    try:
        link = yt_top_link(song_name)
        resp.message(link)
    except Exception as e:
        resp.message("Sorry, could not find that song.")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)

