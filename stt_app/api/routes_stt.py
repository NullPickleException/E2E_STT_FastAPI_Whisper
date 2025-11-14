from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from Services import stt_utils
from fastapi.responses import JSONResponse
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/stt/transcribe")
async def transcribe_get(request: Request):
    return templates.TemplateResponse("transcribe.html", {"request": request})

@router.post("/stt/transcribe")
async def transcribe_post(audio_file: UploadFile = File(...),
                          audio_language: str = Form(None)):
    tmp_path = os.path.join(stt_utils.RECORD_DIR, audio_file.filename)
    with open(tmp_path, "wb") as f:
        f.write(await audio_file.read())

    text = stt_utils.transcribe_audio(tmp_path)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    return {"text": text}

# -------------------------------
# New route: Save transcription
# -------------------------------
@router.post("/stt/save")
async def save_transcription_endpoint(text: str = Form(...)):
    if not text.strip():
        return JSONResponse({"error": "No text provided."}, status_code=400)

    file_path = stt_utils.save_transcription(text)
    return {"message": "Transcription saved.", "file": file_path}
