from __future__ import annotations

from fastapi import HTTPException, status


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(f"{resource} not found", status_code=404)


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(detail, status_code=409)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(detail, status_code=403)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(detail, status_code=401)


class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed") -> None:
        super().__init__(detail, status_code=422)


class RateLimitError(AppException):
    def __init__(self) -> None:
        super().__init__("Rate limit exceeded", status_code=429)
