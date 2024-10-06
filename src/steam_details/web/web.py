import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import app as api_app
from ..service_manager import service_manager

app = FastAPI(openapi_url=None, on_startup=[service_manager.load_services])

app.mount("/api", api_app)

app.mount("/static", StaticFiles(
    directory=os.path.join(os.path.dirname(__file__), "static")
), name="static")

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "name": "error"
        },
        status_code=exc.status_code
    )


@app.get("/")
async def index(request: Request):
    """Get the index page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "name": ""
        }
    )


@app.get("/analytics")
async def analytics(request: Request):
    """Get the analytics page."""
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "name": "analytics"
        }
    )
