from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import urllib.parse, os, re
import lyricsgenius
import yt_dlp
import requests
from bs4 import BeautifulSoup
from random import choice

app = Flask(__name__)
GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    skip_non_songs=True,
    remove_section_headers=True,
    timeout=15
)

def is_malayalam(text):
    return bool(re.search(r'[\u0D00-\u0D7F]', text))

def fetch_from_filmsonglyrics(query):
    try:
        url = f"https://filmsonglyrics.wordpress.com/?s={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("h2.entry-title > a")
        if not a: return None
        page = requests.get(a['href'], timeout=10)
        sp = BeautifulSoup(page.text, "html.parser")
        paras = sp.select("div.entry-content p")
        return "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True)) or None
    except:
        return None

def fetch_from_mallulyrics(query):
    try:
        url = f"https://mallulyrics.angelfire.com/search?q={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("a[href]")
        if not a: return None
        page = requests.get(a['href'], timeout=10)
        return page.text.strip() or None
    except:
        return None

def fetch_malayalam_lyrics(query):
    lyrics = fetch_from_filmsonglyrics(query)
    if lyrics:
        return lyrics
    return fetch_from_mallulyrics(query)

def fetch_lyrics(song_name):
    try:
        song = genius.search_song(song_name)
        return song.lyrics if song else None
    except:
        return None

def yt_search_title(query):
    opts = {'quiet': True, 'skip_download': True, 'format': 'best', 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            data = ydl.extract_info(f"ytsearch3:{query}", download=False)
            for entry in data.get('entries', []):
                if entry and not entry.get('is_private') and not entry.get('was_live', False) and not entry.get('is_unavailable', False):
                    return entry['title'], f"https://www.youtube.com/watch?v={entry['id']}"
    except Exception:
        pass
    return None, None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    text = request.values.get("Body", "").strip()
    lowered = text.lower()
    resp = MessagingResponse()

    if lowered == "help":
        resp.message("🎶 Commands:\n- Song name → YouTube link\n- suggest → random song\n- lyrics <song> → lyrics")
    elif lowered == "suggest":
        song = choice(["Shape of You", "Tum Hi Ho", "Apna Bana Le", "Tera Ban Jaunga"])
        resp.message(f"{song}\n{yt_search_title(song)[1] or ''}")
    elif lowered.startswith("lyrics "):
        query = text[7:].strip()
        yt_title, yt_link = yt_search_title(query)
        lyrics = fetch_lyrics(query)

        if not lyrics or is_malayalam(query):
            fallback_query = yt_title if yt_title else query
            lyrics = fetch_malayalam_lyrics(fallback_query)

        if lyrics:
            title = yt_title or query.title()
            resp.message(f"🎵 {title} Lyrics:\n\n{lyrics[:1200]}")
        else:
            if yt_link:
                resp.message(f"🎥 Couldn't find lyrics.\nHere’s the song: {yt_link}")
            else:
                resp.message("😔 Sorry, couldn't find the song or lyrics.")

    else:
        title, link = yt_search_title(text)
        resp.message(link or "Sorry, I couldn't find that song on YouTube.")

    return str(resp)

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
