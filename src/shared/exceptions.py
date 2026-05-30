# src/shared/exceptions.py
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger()


class InsufficientPermissionError(Exception): ...


class ErrorResponse(BaseModel):
    code: str  # machine-readable error code e.g. "NOT_FOUND"
    message: str  # human-readable description
    request_id: str  # ties the error to a specific request


HTTP_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    500: "INTERNAL_ERROR",
}


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        await logger.aerror("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected error happened",
                request_id=getattr(request.state, "request_id", "unknown"),
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def httpexception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=HTTP_STATUS_CODES.get(exc.status_code, "HTTP_ERROR"),
                message=exc.detail,
                request_id=getattr(request.state, "request_id", "unknown"),
            ).model_dump(),
        )
