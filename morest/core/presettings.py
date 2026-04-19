import logging
from django.urls import path
from morest.api import Response


class RequestIDLogFilter(logging.Filter):
    def filter(self, record):
        try:
            from morest.middlewares.requestid import RequestID

            record.request_id = RequestID.get("-")
        except Exception:
            record.request_id = "-"
        return True


MOREST_MIDDLEWARES = [
    "morest.middlewares.RequestIDMiddleware",
    "morest.middlewares.ExceptionMiddleware",
]


MOREST_REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "morest.middlewares.DRFExceptionMiddleware",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "request_id": {
            "()": "morest.core.presettings.RequestIDLogFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "filters": ["require_debug_false", "request_id"],
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "morest": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

HEALTHCHECK_URLPATTERNS = [
    path("healthcheck/", lambda _: Response())
]


django_logger = logging.getLogger("django")
django_request_logger = logging.getLogger("django.request")
django_server_logger = logging.getLogger("django.server")
morest_logger = logging.getLogger("morest")

    
