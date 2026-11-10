from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.api.v1.network_activities import router as network_activities_router
from src.api.v1.users import router as users_router

app = FastAPI(
    title="Bandwidth Router Calc API",
    description="REST API сервиса расчета пропускной способности Wi-Fi роутера",
    version="1.0.0",
)

# Роутеры REST API
app.include_router(network_activities_router)
app.include_router(users_router)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive API docs."""
    return RedirectResponse(url="/docs")
