import logging
from traceback import format_exc
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from morest.errors import BaseError, InternalError
from morest.api import Response
from morest.errors import NotFoundError


logger = logging.getLogger("morest.exceptions")


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _build_not_found_response(self, request: HttpRequest | None = None):
        error_details = None
        if request is not None:
            error_details = {
                "path": request.path,
                "method": request.method,
            }
        return NotFoundError(
            message="The requested resource was not found on this server.",
            error_details=error_details,
        ).to_response()
    
    def _handle_exception(self, exc, request: HttpRequest = None):
        if isinstance(exc, BaseError):
            return exc.to_response()
        elif isinstance(exc, APIException):
            return Response(
                status=exc.detail.code,
                status_code=exc.status_code,
                message=str(exc.detail),
                error_details=exc.get_full_details(),
            )
        elif isinstance(exc, Http404):
            return self._build_not_found_response(request=request)
        else:
            exception = format_exc()
            logger.error(exception)
            if settings.DEBUG:
                return InternalError(error_details={
                    "exception": exception,
                }).to_response()

            return InternalError().to_response()
        
    def __call__(self, request: HttpRequest):
        try:
            response: HttpResponse = self.get_response(request)
            if response.status_code == 404 and not isinstance(response, Response):
                return self._build_not_found_response(request=request)
            return response
        except BaseException as e:
            return self._handle_exception(e, request=request)

    def process_exception(self, request: HttpRequest, exception: Exception):
        return self._handle_exception(exception, request=request)


def DRFExceptionMiddleware(exc, context):
    response = exception_handler(exc, context)
    if exc is not None:
        request = context.get("request") if context else None
        return ExceptionMiddleware(None)._handle_exception(exc, request=request)
    return response
