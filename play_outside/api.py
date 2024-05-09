from dataclasses import dataclass
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI
import time
from datetime import datetime
from fastapi import Request
from fastapi import Header
import httpx
from play_outside.config import get_config
from play_outside.decorators import cache, no_cache
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from fastapi import Depends
import arel


def set_prefers(
    request: Request,
):
    hx_request_header = request.headers.get("hx-request")
    user_agent = request.headers.get("user-agent", "").lower()
    if "mozilla" in user_agent or "webkit" in user_agent or hx_request_header:
        request.state.prefers_html = True
        request.state.prefers_json = False
    else:
        request.state.prefers_html = False
        request.state.prefers_json = True


app = FastAPI(
    dependencies=[Depends(set_prefers)],
)
config = get_config()


if config.env == "local":
    hot_reload = arel.HotReload(
        paths=[arel.Path("fokais"), arel.Path("templates"), arel.Path("static")]
    )
    app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")
    app.add_event_handler("startup", hot_reload.startup)
    app.add_event_handler("shutdown", hot_reload.shutdown)
    config.templates.env.globals["DEBUG"] = True
    config.templates.env.globals["hot_reload"] = hot_reload


async def get_lat_long(ip_address):
    if ip_address is None:
        ip_address = "140.177.140.75"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://ipwho.is/{ip_address}")
        return response.json()


async def get_weather(lat_long=None):
    if not lat_long:
        lat_long = {"latitude": 40.7128, "longitude": -74.0060}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather?units=imperial&lat={lat_long['latitude']}&lon={lat_long['longitude']}&appid={config.open_weather_api_key}"
        )
        return response.json()


async def get_forecast(lat_long=None):
    if not lat_long:
        lat_long = {"latitude": 40.7128, "longitude": -74.0060}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/forecast?units=imperial&lat={lat_long['latitude']}&lon={lat_long['longitude']}&appid={config.open_weather_api_key}"
        )
        return response.json()["list"]


async def get_air_quality(lat_long):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat_long['latitude']}&lon={lat_long['longitude']}&appid={config.open_weather_api_key}"
        )
        return response.json()


@app.get("/htmx.org@1.9.8", include_in_schema=False)
@cache()
async def get_htmx(request: Request):
    return FileResponse("static/htmx.org@1.9.8")


@app.get("/favicon.ico", include_in_schema=False)
@cache()
async def get_favicon(request: Request):
    return FileResponse("static/favicon.ico")


@app.get("/app3.css", include_in_schema=False)
@cache()
async def get_app_css(request: Request):
    """
    return app.css for development updates
    """
    return FileResponse("static/app.css")


def make_text_response(request, data, color):
    template_response = config.templates.TemplateResponse(
        "index.txt", {"request": request, "color": color, **data}
    )

    return PlainTextResponse(template_response.body, status_code=200)


@app.get("/")
@no_cache
async def get_home(request: Request, color: bool = False, n_forecast: int = None):
    data = await get_data(request, n_forecast)
    print(n_forecast)
    print(len(data["forecast"]))
    if request.state.prefers_html:
        return config.templates.TemplateResponse(
            "index.html", {"request": request, **data}
        )
    else:
        return make_text_response(request, data, color=color)


def hours_till_sunset(weather):
    if "sys" not in weather:
        return ""
    if "sunset" not in weather["sys"]:
        return ""

    sunset = (
        datetime.fromtimestamp(weather["sys"]["sunset"])
        - datetime.fromtimestamp(weather["dt"])
    ).total_seconds() / 60

    if sunset < 0:
        return "it is after sunset"
    elif sunset > 120:
        return ""
    elif sunset > 60:
        return f"Time till sunset is {round(int(sunset)/60)} hours. "
    else:
        return f"Time till sunset is {round(int(sunset))} minutes. "


ANSI_RED = r"\x1b[1;31m"
ANSI_GREEN = r"\x1b[1;32m"
ANSI_YELLOW = r"\x1b[1;33m"


@dataclass
class PlayCondition:
    message: str = ""
    color: str = "bg-green-500"
    ansi_color: str = ANSI_GREEN


def determine_play_condition(weather, aqi=0):
    play_condition = PlayCondition()

    feels_like_temperature = weather["main"]["feels_like"]
    # visibility = weather["visibility"]

    play_condition.message += hours_till_sunset(weather)

    if "after" in play_condition.message:
        play_condition.color = "bg-red-500"
        play_condition.ansi_color = ANSI_RED

    # if visibility < 1000:
    #     play_condition.message += "It's too foggy. Find better activities inside!"
    #     play_condition.color = "bg-red-500"
    #     play_condition.ansi_color = ANSI_RED

    if aqi > 150:
        play_condition.message += "It's too polluted. Find better activities inside!"
        play_condition.color = "bg-red-500"
        play_condition.ansi_color = ANSI_RED
    elif aqi > 100:
        play_condition.message += "limit your time outside due to the poor air quality"
        play_condition.color = "bg-yellow-500"
        play_condition.ansi_color = ANSI_YELLOW
    elif aqi > 50:
        play_condition.message += "Check the air quality outside at your discression."
        play_condition.color = "bg-yellow-500"
        play_condition.ansi_color = ANSI_YELLOW
    else:
        play_condition.message += ""

    if feels_like_temperature < 10:
        play_condition.message += "It's too cold. Stay indoors and keep warm!"
        play_condition.color = "bg-red-500"
        play_condition.ansi_color = ANSI_RED
    elif feels_like_temperature < 30:
        play_condition.message += (
            "You can play outside, but limit your time in this cold!"
        )
        play_condition.color = "bg-yellow-500"
        play_condition.ansi_color = ANSI_YELLOW
    elif feels_like_temperature < 40:
        play_condition.message += (
            "Coats and winter gear required for outdoor play. Stay cozy!"
        )
    elif feels_like_temperature < 50:
        play_condition.message += "Grab a warm jacket and enjoy your time outside!"
    elif feels_like_temperature < 60:
        play_condition.message += "Grab some long sleeves and enjoy your time outside!"
    elif feels_like_temperature > 90:
        play_condition.message += (
            "You can play outside, but limit your time in this heat!"
        )
        play_condition.color = "bg-yellow-500"
        play_condition.ansi_color = ANSI_YELLOW
    elif feels_like_temperature > 109:
        play_condition.message += (
            "It's too hot for outdoor play. Find cooler activities indoors!"
        )
        play_condition.color = "bg-red-500"
        play_condition.ansi_color = ANSI_RED
    else:
        play_condition.message += "Enjoy your time outside!"
    return play_condition


async def get_data(request: Request, n_forecast: int = None):
    user_ip = request.headers.get("CF-Connecting-IP")
    lat_long = await get_lat_long(user_ip)
    weather = await get_weather(lat_long)
    forecast = await get_forecast(lat_long)
    if n_forecast is not None:
        forecast = forecast[: n_forecast + 2]
    air_quality = await get_air_quality(lat_long)
    weather["play_condition"] = determine_play_condition(
        weather,
        air_quality["list"][0]["main"]["aqi"],
    )

    forecast = [
        {"play_condition": determine_play_condition(x), **x}
        for x in forecast
        if datetime.fromtimestamp(x["dt"]).hour >= 6
        and datetime.fromtimestamp(x["dt"]).hour <= 21
    ]

    return {
        "request.client": request.client,
        "request.client.host": request.client.host,
        "user_ip": user_ip,
        "lat_long": lat_long,
        "weather": weather,
        "forecast": forecast,
        "air_quality": air_quality,
        "sunset": weather["sys"]["sunset"],
    }


@app.get("/metadata")
async def root(
    request: Request,
):
    return await get_data(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
