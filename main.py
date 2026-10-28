from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.api.network_activities import router as web_network_activities_router
from src.api.api_v1.network_activities import router as network_activities_router
from src.api.api_v1.users import router as users_router

app = FastAPI(title="Bandwidth Router Calc API")

app.mount("/static", StaticFiles(directory="./static"), name="static")

# Роутер веб-шаблонов HTML (Лента, Черновик/Добавление, Каталог)
app.include_router(web_network_activities_router)

# Роутеры REST API
app.include_router(network_activities_router)
app.include_router(users_router)


@app.get("/")
def root_redirect():
    return RedirectResponse(url="/network-activities/feed")
