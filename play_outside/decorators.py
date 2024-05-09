import inspect
import time
from functools import wraps
from inspect import signature

from fastapi import Request
from fastapi.responses import JSONResponse

from play_outside.config import get_config

config = get_config()


admin_routes = []
not_cached_routes = []
cached_routes = []


def not_found(request):
    hx_request_header = request.headers.get("hx-request")
    user_agent = request.headers.get("user-agent", "").lower()

    if "mozilla" in user_agent or "webkit" in user_agent or hx_request_header:
        return config.templates.TemplateResponse(
            "error.html",
            {"status_code": 404, "detail": "Not Found", "request": request},
            status_code=404,
        )
    else:
        return JSONResponse(
            content={
                "status_code": 404,
                "detail": "Not Found",
            },
            status_code=404,
        )


def no_cache(func):
    not_cached_routes.append(f"{func.__module__}.{func.__name__}")

    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        # my_header will be now available in decorator
        if "request" in signature(func).parameters:
            kwargs["request"] = request

        if inspect.iscoroutinefunction(func):
            response = await func(*args, **kwargs)
        else:
            response = func(*args, **kwargs)

        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return wrapper


def cache(max_age=86400):
    def inner_wrapper(func):
        cached_routes.append(f"{func.__module__}.{func.__name__}")

        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            if "request" in signature(func).parameters:
                kwargs["request"] = request
            if inspect.iscoroutinefunction(func):
                response = await func(*args, **kwargs)
            else:
                response = func(*args, **kwargs)
            response.headers[
                "Cache-Control"
            ] = f"public, max-age={max_age}, stale-while-revalidate=31536000, stale-if-error=31536000"
            response.headers["Expires"] = f"{int(time.time()) + max_age}"

            return response

        return wrapper

    return inner_wrapper


default_data = {}


def defaults(data=default_data):
    def inner_wrapper(func):
        default_data[f"{func.__module__}.{func.__name__}"] = data

        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            if "request" in signature(func).parameters:
                kwargs["request"] = request
            if inspect.iscoroutinefunction(func):
                response = await func(*args, **kwargs)
            else:
                response = func(*args, **kwargs)
            return response

        return wrapper

    return inner_wrapper
