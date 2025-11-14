from fastapi import FastAPI
from api import routes_stt
from Services import stt_utils


app = FastAPI()

app.include_router(routes_stt.router)