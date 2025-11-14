Speech-To-Text Web App

A simple speech-to-text web app built with FastAPI and OpenAI Whisper.
Users can upload an audio file or record audio and get transcribed text — all with a clean, dynamic web interface.

Folder Structure
tts_app/
│
├─ app/
│  ├─ main.py              # FastAPI entry point
│  ├─ api/
│  │  └─ routes_stt.py     # API routes
│  ├─ Services/
│  │  └─ stt_utils.py      # Whisper + audio utils
│  └─ templates/
│     ├─ index.html        # Home page
│     └─ transcribe.html   # Transcription page
│
├─ Recorded_Audio/         # Temporary audio uploads
├─ Transcriptions/         # Saved transcriptions
└─ requirements.txt        # Python dependencies

Features:
-Upload or record audio files
-Transcription powered by Whisper (base model)
-Supports multiple languages
-Real-time and batch transcription modes
-Simple, dynamic web UI (FastAPI + HTML + CSS)
-Optional public access via Cloudflare Tunnel

Tech Stack:
-Backend: FastAPI
-Model: OpenAI Whisper (PyTorch)
-Frontend: HTML + Jinja2 Templates
-Audio: PyAudio, SoundDevice
-Deployment (optional): Cloudflare Tunnel




Setup & Run:

1.Install dependencies:
pip install -r requirements.txt


2. Run the FastAPI server in the first terminal:
uvicorn main:app --reload


3. This starts the server locally at:
http://127.0.0.1:8000

4.Run Cloudflare Tunnel in a second terminal (optional, for public access):
.\cloudflared.exe tunnel --url http://127.0.0.1:8000 --protocol http2 --loglevel info


The terminal will show a public URL like:
https://<random-name>.trycloudflare.com






Anyone can access your app via this URL.

Usage:
1.Open the app in your browser.
2.Upload an audio file or record audio using the mic.
3.Select the language (optional).
4.Click Transcribe.
5.The transcription appears dynamically in the same page.
6.Use the Copy button to copy the transcribed text.