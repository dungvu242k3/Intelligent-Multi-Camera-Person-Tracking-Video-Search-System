from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


def _message_from_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "Request validation failed"
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("detail") or "Request failed")
    return "Request failed"


def error_payload(code: str, message: str, request: Request, details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request.headers.get("X-Request-Id"),
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def register_exception_handlers(app: FastAPI, service_name: str) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=error_payload(
                code=f"{service_name.upper().replace('-', '_')}_{exc.status_code}",
                message=_message_from_detail(exc.detail),
                request=request,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_payload(
                code=f"{service_name.upper().replace('-', '_')}_422",
                message="Request validation failed",
                request=request,
                details=exc.errors(),
            ),
        )
