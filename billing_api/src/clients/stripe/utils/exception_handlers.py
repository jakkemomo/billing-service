"""Модуль с обработчиками кодов HTTP-ответов API платежной системы Stripe"""
from ..exceptions import (
    BadRequest,
    RequestFailed,
    TooManyRequests,
    Conflict,
    InternalError,
    Unauthorized,
    Forbidden,
    NotFound,
)
from ..models import HTTPResponse

EXCEPTIONS_MAPPING = {
    400: BadRequest,
    401: Unauthorized,
    402: RequestFailed,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    429: TooManyRequests,
    500: InternalError,
    502: InternalError,
    503: InternalError,
    504: InternalError,
}


def handle_response(response: HTTPResponse) -> HTTPResponse:
    exception_cls = EXCEPTIONS_MAPPING.get(response.status, None)
    if not exception_cls:
        return response
    raise exception_cls(response)
