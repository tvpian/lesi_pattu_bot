from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import urllib.parse, os, re
import lyricsgenius
import requests
from bs4 import BeautifulSoup
from random import choice
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import logging

app = Flask(__name__)
GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
YT_API_KEY = os.getenv("YOUTUBE_API_KEY")
genius = lyricsgenius.Genius(GENIUS_TOKEN, skip_non_songs=True, remove_section_headers=True, timeout=15)
yt = build('youtube', 'v3', developerKey=YT_API_KEY)

logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def health_check():
    return "✅ WhatsApp Lyrics Bot is running!"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(Exception))
def yt_search_title(query):
    resp = yt.search().list(q=query, part="snippet", maxResults=1, type="video").execute()
    items = resp.get('items', [])
    if not items:
        return None, None
    item = items[0]
    return item['snippet']['title'], f"https://www.youtube.com/watch?v={item['id']['videoId']}"

def is_malayalam(text):
    return bool(re.search(r'[\u0D00-\u0D7F]', text))

def fetch_from_filmsonglyrics(query):
    try:
        url = f"https://filmsonglyrics.wordpress.com/?s={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("h2.entry-title > a")
        if not a: return None
        sp = BeautifulSoup(requests.get(a['href'], timeout=10).text, "html.parser")
        paras = sp.select("div.entry-content p")
        return "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))
    except Exception as e:
        logging.error(f"[filmsonglyrics] {e}")
        return None

def fetch_from_mallulyrics(query):
    try:
        url = f"https://mallulyrics.angelfire.com/search?q={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("a[href]")
        if not a: return None
        return requests.get(a['href'], timeout=10).text.strip()
    except Exception as e:
        logging.error(f"[mallulyrics] {e}")
        return None

def fetch_malayalam_lyrics(query):
    return fetch_from_filmsonglyrics(query) or fetch_from_mallulyrics(query)

def fetch_lyrics(song_name):
    try:
        song = genius.search_song(song_name)
        return song.lyrics if song else None
    except Exception as e:
        logging.error(f"[genius] {e}")
        return None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    text = request.values.get("Body", "").strip()
    lowered = text.lower()
    resp = MessagingResponse()

    try:
        if lowered == "help":
            resp.message("🎶 Commands:\n- Song → YouTube link\n- suggest\n- lyrics <song>")
        elif lowered == "suggest":
            song = choice(["Shape of You", "Tum Hi Ho"])
            title, link = yt_search_title(song)
            resp.message(f"{song}\n{link or ''}")
        elif lowered.startswith("lyrics "):
            query = text[7:].strip()
            title, link = yt_search_title(query)
            lyrics = fetch_lyrics(query)
            if not lyrics or is_malayalam(query):
                lyrics = fetch_malayalam_lyrics(title or query)
            if lyrics:
                resp.message(f"🎵 {title or query} Lyrics:\n\n{lyrics[:1200]}")
            else:
                if link:
                    resp.message(f"🎥 Couldn't find lyrics. But here’s the song:\n{link}")
                else:
                    resp.message("😔 Sorry, song not found.")
        else:
            title, link = yt_search_title(text)
            resp.message(link or "Sorry, I couldn't find that song.")

    except Exception as e:
        logging.error(f"[whatsapp_reply] {e}")
        resp.message("⚠️ Something went wrong. Please try again later.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
