from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: object | None = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_payload(code: str, message: str, request_id_value: str, details: object | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "requestId": request_id_value,
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, request_id(request), exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", "Request validation failed.", request_id(request), exc.errors()),
        )
