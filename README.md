# WhatsApp YouTube & Lyrics Bot 🎶

A WhatsApp bot built with **Python Flask**, **Twilio**, **YouTube Data API**, **Genius API**, and **Malayalam lyrics scraping**.  
Supports song link retrieval and lyrics lookup (including Malayalam), with typo tolerance and fallback logic.

---

## 🚀 Features

- Send any song name to receive:
  - YouTube video link (title + URL)
  - Lyrics (if available)
- Supports **typo-tolerant** querying using YouTube Data API
- Lyrics via:
  - ✔️ **Genius API** (English, Hindi)
  - ✔️ **Malayalam scraping** (multi-site)
- Commands:
  - `help` → Show usage guide
  - `suggest` → Random song recommendation
  - `lyrics <song>` → Retrieve lyrics
- Graceful fallback if lyrics are unavailable

---

## 🧠 Tech Stack & Dependencies

```text
Python 3.10+
Flask
twilio
google-api-python-client
lyricsgenius
beautifulsoup4
requests
```

`requirements.txt` example:

```
Flask
twilio
google-api-python-client
lyricsgenius
beautifulsoup4
requests
```

(You may omit `yt-dlp` since YouTube API is used in production.)

---

## 🔐 Environment Variables

Set these (via `.env`, `render.yaml`, or Render dashboard):

```bash
GENIUS_ACCESS_TOKEN=your_genius_api_token
YOUTUBE_API_KEY=your_youtube_data_api_key
```

- `GENIUS_ACCESS_TOKEN`: for lyrics via Genius API  
- `YOUTUBE_API_KEY`: used for fetching video title & link via official API

---

## 📁 Directory Structure

```
project-root/
│
├── app.py
├── requirements.txt
├── render.yaml       # Optional for Render GitHub deploy
└── README.md
```

---

## ⚙️ Running Locally (with ngrok)

1. Set your environment variables:
   ```bash
   export GENIUS_ACCESS_TOKEN=...
   export YOUTUBE_API_KEY=...
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask server:
   ```bash
   python app.py
   ```
4. In another terminal:
   ```bash
   ngrok http 5000
   ```
5. In Twilio Sandbox → Paste `https://<ngrok-id>.ngrok.io/whatsapp` as webhook URL.

Test commands like:

- `help`
- `suggest`
- `lyrics malare`
- `aaradhike`
- `tum hi ho`

---

## 🌐 Deploy on Render

Use this `render.yaml` or configure via web UI:

```yaml
services:
  - type: web
    name: whatsapp-song-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: GENIUS_ACCESS_TOKEN
        value: YOUR_GENIUS_TOKEN
      - key: YOUTUBE_API_KEY
        value: YOUR_YOUTUBE_API_KEY
```

Then push to GitHub → Render will auto-build & deploy.

---

## 🧪 Usage Examples

| Input             | Response                                                   |
|-------------------|-------------------------------------------------------------|
| `help`            | Lists available commands                                   |
| `suggest`         | Random song suggestion with link                           |
| `lyrics kesariya` | Lyric text via Genius API                                  |
| `lyrics aaradhike`| Malayalam lyric text via web scraping                      |
| `kesariya`        | YouTube link when lyrics missing or unavailable             |

---

## 🛠️ Troubleshooting

- `KeyError: 'GENIUS_ACCESS_TOKEN'`: confirm key is exactly named (case-sensitive), and Render env var is set.
- Missing YouTube link on Render? Likely `yt-dlp` blocked—use YouTube Data API instead.
- Lyrics not found? Testing Malayalam can be unpredictable—check logs to debug scrapers.
- Logs: monitor for HTTP errors or failed scrapes in Render’s dashboard.

---

## 🔄 Future Enhancements

- Add caching (file-based or Redis)
- Paginate long lyrics over multiple WhatsApp messages
- Send lyrics as audio (via TTS)
- Add user settings and song favorites
- Multilingual support beyond Malayalam

---

## 📄 License

MIT License (or choose your preferred one)

---

Thanks for building this tool—your mom’s bot now fetches song links and lyrics reliably! 😊

