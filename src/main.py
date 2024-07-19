from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from steam import get_steam_details, wishlist_data


app = FastAPI(openapi_url=None)

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
    data = await wishlist_data(profile_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found")
    items = []
    for item in data:
        items.append(item.model_dump())
    return items


@app.get("/details")
async def details(appid: str):
    steam_data = await get_steam_details(appid)
    return {
        "steam": steam_data.model_dump()
    }
