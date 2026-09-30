from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.api.network_activities import router


app = FastAPI(title="Bandwidth Router Calc")

app.mount("/static", StaticFiles(directory="./static"), name="static")

app.include_router(router)


@app.get("/")
def root_redirect():
    return RedirectResponse(url="/network-activities/feed")
