"""Module with Stripe API status codes handler"""
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
    """
    Handle Stripe API responses

    @param response: `aiohttp.ClientResponse` response object
    @return: `aiohttp.ClientResponse` object for the cases where response has status code 200,
    otherwise, raise exception
    @raise: one of the exceptions from `EXCEPTIONS_MAPPING` dictionary depending on response status code
    """
    exception_cls = EXCEPTIONS_MAPPING.get(response.status, None)
    if not exception_cls:
        return response
    raise exception_cls(response)
