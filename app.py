from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import subprocess
import urllib.parse
import os
import lyricsgenius
from random import choice

app = Flask(__name__)

# Load Genius API key from environment variable
GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    skip_non_songs=True,
    remove_section_headers=True,
    timeout=15
)

# ----------- YouTube Search Function -----------
def yt_top_link(song):
    query = urllib.parse.quote_plus(song)
    result = subprocess.check_output(
        ["yt-dlp", f"ytsearch1:{query}", "--get-id"],
        text=True
    ).strip()
    return f"https://www.youtube.com/watch?v={result}"

# ----------- Lyrics Fetch Function -----------
def fetch_lyrics(song_name):
    try:
        song = genius.search_song(song_name)
        if song:
            return song.lyrics
        else:
            return "Lyrics not found."
    except Exception:
        return "Couldn't fetch lyrics."

# ----------- WhatsApp Endpoint -----------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    text = request.values.get("Body", "").strip()
    lowered = text.lower()
    resp = MessagingResponse()

    # Help Command
    if lowered == "help":
        resp.message(
            "🎶 WhatsApp Song Bot Commands:\n"
            "- Type any song name to get a YouTube link\n"
            "- Type 'suggest' for a random song\n"
            "- Type 'lyrics <song>' to get lyrics"
        )

    # Suggest Command
    elif lowered == "suggest":
        songs = ["Shape of You", "Tum Hi Ho", "Blinding Lights", "Apna Bana Le", "Tera Ban Jaunga"]
        suggestion = choice(songs)
        link = yt_top_link(suggestion)
        resp.message(f"Try this: {suggestion}\n{link}")

    # Lyrics Command
    elif lowered.startswith("lyrics "):
        song_query = text[7:].strip()
        lyrics = fetch_lyrics(song_query)
        resp.message(f"🎵 Lyrics for {song_query.title()}:\n\n{lyrics[:1200]}")

    # Fallback: YouTube search
    else:
        try:
            link = yt_top_link(text)
            resp.message(link)
        except:
            resp.message("Sorry, I couldn’t find that song.")

    return str(resp)

# ----------- Run Server (Render-compatible) -----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

