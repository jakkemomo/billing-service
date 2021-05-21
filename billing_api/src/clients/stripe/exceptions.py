class StripeBaseException(Exception):
    pass


class ArgumentValueError(StripeBaseException):
    msg = "Argument has wrong value"


class ArgumentOmittedError(StripeBaseException):
    msg = "Argument is omitted"


class TooManyRequests(StripeBaseException):
    msg = "Too many requests"


class ResourceNotFound(StripeBaseException):
    msg = "Resource does not exists"


class BadRequest(StripeBaseException):
    msg = "Missing a required parameter"


class RequestFailed(StripeBaseException):
    msg = "Request failed"


class RequestConflict(StripeBaseException):
    msg = "Request conflicts"


class StripeInternalError(StripeBaseException):
    msg = "Stripe internal error"
