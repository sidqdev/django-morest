import typing
from morest.errors import NotFoundError
from django.db.models.manager import BaseManager
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404

T = typing.TypeVar("T")

def get_objects_or_404(qs: T, with_error_details: bool = False, **filters) -> T:
    try:
        return _get_object_or_404(qs, **filters)
    except (TypeError, ValueError, ValidationError, Http404):    
        if with_error_details:
            raise NotFoundError.with_object_details(qs.__name__, filters)
        else:
            raise NotFoundError
