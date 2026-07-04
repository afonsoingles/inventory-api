from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sentry_sdk
from fastapi.responses import RedirectResponse

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    send_default_pii=True,
)

app = FastAPI()

load_dotenv()


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url=os.environ.get("BEAVER_BASE_URL", "http://localhost:3000/"), status_code=308)

