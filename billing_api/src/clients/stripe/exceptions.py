from .models import HTTPResponse


class StripeBaseException(Exception):
    def __init__(self, response: HTTPResponse, *args):
        super().__init__(*args)
        self._response = response

    @property
    def response(self):
        return self._response


class Unauthorized(StripeBaseException):
    msg = "No valid API key provided"


class Forbidden(StripeBaseException):
    msg = "The API key doesn't have permissions to perform the request"


class TooManyRequests(StripeBaseException):
    msg = "Too many requests hit the API too quickly"


class NotFound(StripeBaseException):
    msg = "The requested resource doesn't exist"


class BadRequest(StripeBaseException):
    msg = "The request was unacceptable, often due to missing a required parameter"


class RequestFailed(StripeBaseException):
    msg = "The parameters were valid but the request failed"


class Conflict(StripeBaseException):
    msg = "The request conflicts with another request"


class InternalError(StripeBaseException):
    msg = "Something went wrong on Stripe's end"
