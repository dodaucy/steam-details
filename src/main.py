from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from how_long_to_beat import get_game_length
from protondb import get_linux_support
from steam import download_app_list, get_app, get_steam_details, wishlist_data


app = FastAPI(openapi_url=None, on_startup=[download_app_list])

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.get("/wishlist")
async def wishlist(profile_id: str):
    game_appids = await wishlist_data(profile_id)
    if game_appids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found")
    return game_appids


@app.get("/details")
async def details(appid_or_name: str):
    if appid_or_name.strip() == "":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empty search")
    steam = await get_steam_details(appid_or_name)
    if steam is None:
        appid = await get_app(appid_or_name)
        if appid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
        steam = await get_steam_details(appid)
        if steam is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get steam details")
    if steam.released:
        return {
            "steam": steam.model_dump(),
            "linux_support": None if steam.native_linux_support else await get_linux_support(steam.appid),
            "game_length": await get_game_length(steam.appid, steam.name)
        }
    else:
        return {
            "steam": steam.model_dump(),
            "linux_support": None,
            "game_length": None
        }
