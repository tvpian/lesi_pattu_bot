from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import subprocess, urllib.parse, os, re
import lyricsgenius
import requests
from bs4 import BeautifulSoup
from random import choice
import subprocess



app = Flask(__name__)
GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    skip_non_songs=True,
    remove_section_headers=True,
    timeout=15
)

def yt_search_title(song):
    q = urllib.parse.quote_plus(song)
    lines = subprocess.check_output(
        ["yt-dlp", f"ytsearch1:{q}", "--print", "%(id)s|%(title)s"],
        text=True
    ).strip()
    vid, title = lines.split("|", 1)
    return title, f"https://www.youtube.com/watch?v={vid}"

# Detect Malayalam script in input
def is_malayalam(text):
    return bool(re.search(r'[\u0D00-\u0D7F]', text))

# Scraper: filmsonglyrics.wordpress.com (Works reliably) :contentReference[oaicite:1]{index=1}
def fetch_from_filmsonglyrics(query):
    try:
        url = f"https://filmsonglyrics.wordpress.com/?s={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("h2.entry-title > a")
        if not a:
            return None
        page = requests.get(a['href'], timeout=10)
        sp = BeautifulSoup(page.text, "html.parser")
        paras = sp.select("div.entry-content p")
        lyrics = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))
        return lyrics.strip() or None
    except Exception:
        return None

# Scraper: mallulyrics.angelfire.com (Largest Malayalam lyrics archive) :contentReference[oaicite:2]{index=2}
def fetch_from_mallulyrics(query):
    try:
        url = f"https://mallulyrics.angelfire.com/search?q={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("a")
        if not a or not a['href']:
            return None
        page = requests.get(a['href'], timeout=10)
        return page.text.strip() or None
    except Exception:
        return None

def fetch_malayalam_lyrics(query):
    lyrics = fetch_from_filmsonglyrics(query)
    if lyrics:
        return lyrics
    return fetch_from_mallulyrics(query) or None

def yt_top_link(song):
    q = urllib.parse.quote_plus(song)
    vid = subprocess.check_output(["yt-dlp", f"ytsearch1:{q}", "--get-id"], text=True).strip()
    return f"https://www.youtube.com/watch?v={vid}"

def fetch_lyrics(song_name):
    try:
        song = genius.search_song(song_name)
        return song.lyrics if song else None
    except Exception:
        return None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    text = request.values.get("Body", "").strip()
    lowered = text.lower()
    resp = MessagingResponse()

    if lowered == "help":
        resp.message(
            "🎶 Commands:\n"
            "- Send a song name → YouTube link\n"
            "- 'suggest' → random song\n"
            "- 'lyrics <song>' → lyrics"
        )
    elif lowered == "suggest":
        song = choice(["Shape of You","Tum Hi Ho","Apna Bana Le","Tera Ban Jaunga"])
        resp.message(f"{song}\n{yt_top_link(song)}")
    elif lowered.startswith("lyrics "):
        user_query = text[7:].strip()

        # 1️⃣ Step: Get YouTube-corrected title and link
        yt_title, yt_link = yt_search_title(user_query)

        # 2️⃣ Try Genius first with original
        lyrics = fetch_lyrics(user_query)

        # 3️⃣ If no lyrics or detecting Malayalam, retry with yt_title
        if not lyrics or is_malayalam(user_query):
            lyrics = fetch_malayalam_lyrics(yt_title)

        # 4️⃣ Final fallback logic
        if not lyrics:
        # Always respond with YouTube link
            resp.message(f"🎥 Couldn't fetch lyrics, but here's the song:\n{yt_link}")
        else:
            resp.message(f"🎵 {yt_title} Lyrics:\n\n{lyrics[:1200]}")

    else:
        try:
            resp.message(yt_top_link(text))
        except Exception:
            resp.message("Sorry, I couldn’t find that song.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

