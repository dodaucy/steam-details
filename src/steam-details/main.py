import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import app as api_app
from service_manager import service_manager
from utils import ANSICodes

app = FastAPI(openapi_url=None, on_startup=[service_manager.load_services])

app.mount("/api", api_app)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: ANSICodes.GREEN,
        logging.INFO: ANSICodes.BLUE,
        logging.WARNING: ANSICodes.YELLOW,
        logging.ERROR: ANSICodes.RED,
        logging.CRITICAL: ANSICodes.MAGENTA
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        return super().format(record).replace(
            "{LEVEL_COLOR}",
            self.COLORS.get(record.levelno, ANSICodes.RESET),
            1
        )


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logging.getLogger().handlers[0].setFormatter(ColorFormatter(
    f"%(asctime)s {{LEVEL_COLOR}}{ANSICodes.BOLD}[%(levelname)s]{ANSICodes.RESET} %(name)s ({ANSICodes.BLUE}%(filename)s:%(lineno)d{ANSICodes.RESET}) %(message)s"  # noqa
))


logger = logging.getLogger(f"{ANSICodes.MAGENTA}main{ANSICodes.RESET}")


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
