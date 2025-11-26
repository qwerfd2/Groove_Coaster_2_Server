from functools import wraps
from starlette.responses import JSONResponse

from starlette.requests import Request
from config import AUTHORIZATION_MODE, DISCORD_BOT_API_KEY

def require_authorization(mode_required):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if AUTHORIZATION_MODE not in mode_required:
                print(f"Authorization mode {AUTHORIZATION_MODE} not in required modes {mode_required}")
                return JSONResponse({"state": 0, "message": "Authorization mode is not enabled."}, status_code=400)
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def validate_form_fields(required_fields):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            form = await request.form()
            for field in required_fields:
                if not form.get(field):
                    return JSONResponse({"state": 0, "message": f"Missing {field}."}, status_code=402)
            return await func(request, form, *args, **kwargs)
        return wrapper
    return decorator

def check_discord_api_key():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            api_key = request.headers.get("X-API-KEY")
            if api_key != DISCORD_BOT_API_KEY:
                return JSONResponse({"state": 0, "message": "Invalid API key."}, status_code=403)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
