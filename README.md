# django-morest

`django-morest` is a small API utility package for Django and Django REST Framework that standardizes:

- JSON response envelopes
- exception handling
- request ids
- reusable query serializers for pagination, search, and ordering
- list/filter API views
- optional schema helpers for `drf-yasg`
- a simple encrypted text model field

## Installation

```bash
pip install django-morest
```

If you use `EncryptedTextField`, also install `pycryptodome`.

```bash
pip install pycryptodome
```

## Requirements

- Django
- djangorestframework

## Quick Start

Add `morest` to installed apps and merge the provided presettings into your Django settings.

```python
from morest.core import presettings

INSTALLED_APPS = [
    ...,
    "morest",
]

MIDDLEWARE = [
    *presettings.MOREST_MIDDLEWARES,
    ...,
]

REST_FRAMEWORK = {
    **presettings.MOREST_REST_FRAMEWORK,
}

LOGGING = presettings.LOGGING
```

If you want the built-in healthcheck endpoint:

```python
from morest.core import presettings

urlpatterns = [
    *presettings.HEALTHCHECK_URLPATTERNS,
    ...,
]
```

## Presettings

`morest.core.presettings` exposes reusable defaults for Django projects.

### `MOREST_MIDDLEWARES`

```python
MIDDLEWARE = [
    *presettings.MOREST_MIDDLEWARES,
    ...,
]
```

This currently enables:

- `morest.middlewares.RequestIDMiddleware`
- `morest.middlewares.ExceptionMiddleware`

`RequestIDMiddleware` reads the incoming `Request-ID` header when present, otherwise generates one, and adds it to the response headers.

`ExceptionMiddleware` converts unhandled API errors, `Http404`, and plain 404 responses into the standard JSON envelope.

### `MOREST_REST_FRAMEWORK`

```python
REST_FRAMEWORK = {
    **presettings.MOREST_REST_FRAMEWORK,
}
```

This currently sets:

```python
{
    "EXCEPTION_HANDLER": "morest.middlewares.DRFExceptionMiddleware",
}
```

That keeps DRF exceptions inside the same `morest` JSON response format.

### `LOGGING`

```python
LOGGING = presettings.LOGGING
```

The provided logging config:

- logs to console
- only emits through the handler when `DEBUG = False`
- attaches `request_id` to log records through `RequestIDLogFilter`
- exposes ready logger objects in `presettings`: `django_logger`, `django_request_logger`, `django_server_logger`, `morest_logger`

### `HEALTHCHECK_URLPATTERNS`

```python
urlpatterns = [
    *presettings.HEALTHCHECK_URLPATTERNS,
    ...,
]
```

This provides:

- `GET /healthcheck/`

Response:

```json
{
  "data": null,
  "status": "ok",
  "status_code": 200,
  "request_id": "4d06538d2d7b40db8e729757a363fe55",
  "message": "OK"
}
```

## Standard Response Envelope

The central API primitive is `morest.api.Response`.

```python
from morest.api import Response
```

All successful and error responses share the same JSON shape:

```json
{
  "data": {
    "key": "value"
  },
  "status": "ok",
  "status_code": 200,
  "request_id": "4d06538d2d7b40db8e729757a363fe55",
  "message": "OK"
}
```

For non-2xx responses, `error_details` is included.

```json
{
  "data": null,
  "status": "validation_error",
  "status_code": 400,
  "request_id": "4d06538d2d7b40db8e729757a363fe55",
  "message": "Request body or query params validation error",
  "error_details": {
    "email": ["This field is required."]
  }
}
```

## Using `Response`

### Basic success response

```python
from django.http import HttpRequest
from rest_framework.views import APIView
from morest.api import Response


class TestView(APIView):
    def get(self, request: HttpRequest):
        return Response({
            "key": "value",
        })
```

### Explicit status code and message

```python
return Response(
    data={"id": 10},
    status_code=201,
    status="created",
    message="User created",
)
```

### Validation errors from serializers

Use `Response.validation_error(serializer.errors)` whenever request input validation fails.

```python
from rest_framework import serializers
from rest_framework.views import APIView
from morest.api import Response


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()


class CreateUserView(APIView):
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response.validation_error(serializer.errors)

        return Response(serializer.validated_data, status_code=201, status="created", message="Created")
```

### Status-only responses

```python
return Response.from_status("ok")
return Response.from_status("fail")
return Response.from_status("error")
```

## Using Errors

The package exposes a base error type plus reusable application errors.

```python
from morest.errors import (
    BaseError,
    InternalError,
    ValidationError,
    NotFoundError,
    AlreadyExistsError,
    InsufficientBalanceError,
    FieldNotFoundError,
)
```

All `BaseError` subclasses can be raised inside views or helper functions. `ExceptionMiddleware` catches them and returns a `Response` automatically.

### Built-in errors

- `InternalError` -> HTTP `500`
- `ValidationError` -> HTTP `400`
- `NotFoundError` -> HTTP `404`
- `AlreadyExistsError` -> HTTP `409`
- `InsufficientBalanceError` -> HTTP `402`
- `FieldNotFoundError` -> HTTP `406`

### Raise a built-in error

```python
from morest.errors import NotFoundError


def get_user_or_fail(user_id: int):
    ...
    raise NotFoundError(message="User not found")
```

### Convert an error manually

```python
from morest.errors import ValidationError


error = ValidationError(
    message="Invalid payload",
    error_details={"field": ["This field is required."]},
)
return error.to_response()
```

### Helper constructors

```python
from morest.errors import AlreadyExistsError, InsufficientBalanceError, NotFoundError

raise AlreadyExistsError.with_object_details("User", "email", "john@example.com")
raise InsufficientBalanceError.with_balance_details(current_balance=10, required_balance=25)
raise NotFoundError.with_object_details("User", {"id": 15})
```

### Create your own error type

```python
from morest.errors import BaseError


class PermissionDeniedError(BaseError):
    status_code = 403
    status = "permission_denied"
    message = "You do not have permission to perform this action"
```

## Exception Handling

When you enable both presettings:

```python
MIDDLEWARE = [
    *presettings.MOREST_MIDDLEWARES,
    ...,
]

REST_FRAMEWORK = {
    **presettings.MOREST_REST_FRAMEWORK,
}
```

`morest` normalizes these cases into JSON:

- raised `BaseError`
- DRF `APIException`
- `Http404`
- unresolved routes and plain Django 404 responses
- unexpected exceptions as `InternalError`

Example 404 body:

```json
{
  "data": null,
  "status": "not_found",
  "status_code": 404,
  "request_id": "4d06538d2d7b40db8e729757a363fe55",
  "message": "The requested resource was not found on this server.",
  "error_details": {
    "path": "/missing-url/",
    "method": "GET"
  }
}
```

Note: place `morest.middlewares.ExceptionMiddleware` near the top of `MIDDLEWARE`. Exceptions raised by middleware that runs before it will not be normalized by `morest`.

## List and Filter Views

`morest.views.ListFilterView` is a reusable DRF `APIView` for list endpoints that support:

- plain filtering through serializer fields
- text search
- ordering
- pagination
- generated `drf-yasg` query docs when available

Import it from:

```python
from morest.views import ListFilterView
```

### Basic filtered list view

```python
from rest_framework import serializers
from morest.api import Response
from morest.views import ListFilterView
from morest.utils import PaginationSerializer, SearchSerializer, OrderSerializer
from app.models import Product


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class ProductListQuerySerializer(PaginationSerializer, SearchSerializer, OrderSerializer):
    category = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)


class ProductListView(ListFilterView):
    queryset = Product.objects.filter(is_deleted=False)
    serializer = ProductSerializer
    filter_serializer = ProductListQuerySerializer
    search_fields = ["name", "category", "=sku", "^name"]
    order_fields = ["id", "name", "price", "created_at"]
    rows_name = "products"
```

This gives you a `GET` endpoint that can accept query params like:

```text
/products/?category=books&is_active=true&page=1&limit=20&q=django&order_by=name&order_by=-created_at
```

### How filtering works

`ListFilterView.get()` executes in this order:

1. load the base queryset from `get_queryset()`
2. validate `request.GET` with `filter_serializer`
3. strip pagination/search/order fields out of the validated data
4. call `filter_queryset()` with the remaining fields
5. apply search through `SearchSerializer`
6. apply ordering through `OrderSerializer`
7. paginate if the query serializer inherits `PaginationSerializer`
8. serialize and return `Response(...)`

### Overriding queryset filtering

By default, `filter_queryset()` performs `qs.filter(**filters).all()`.

Override it when you need custom logic.

```python
class ProductListView(ListFilterView):
    ...

    def filter_queryset(self, request, qs, filters, **kwargs):
        if category := filters.pop("category", None):
            qs = qs.filter(category__slug=category)
        return qs.filter(**filters)
```

### Search behavior

`SearchSerializer` reads the `q` query param and applies `search_in_queryset()` using `search_fields`.

Supported prefixes in `search_fields`:

- `"name"` -> `name__icontains`
- `"^name"` -> `name__istartswith`
- `"=email"` -> `email__iexact`
- `"@body"` -> `body__search`

Example:

```python
search_fields = ["name", "description", "^sku", "=slug"]
```

### Ordering behavior

`OrderSerializer` reads `order_by` as a list.

```text
/products/?order_by=name&order_by=-created_at
```

Restrict allowed fields with `order_fields`:

```python
order_fields = ["name", "created_at", "price"]
```

If a field outside `order_fields` is requested, `FieldNotFoundError` is raised and returned as a `406` JSON error.

### Pagination behavior

`PaginationSerializer` supports:

- `page` with minimum `1`
- `limit` with minimum `1`

Default values:

- `page = 1`
- `limit = 20`

Paginated response shape:

```json
{
  "data": {
    "products": [],
    "rows_count": 0,
    "total_count": 0,
    "pages_count": 0
  },
  "status": "ok",
  "status_code": 200,
  "request_id": "4d06538d2d7b40db8e729757a363fe55",
  "message": "OK"
}
```

Use `rows_name` on the serializer or the view to rename the collection key.

```python
class ProductListQuerySerializer(PaginationSerializer):
    rows_name = "products"
```

or:

```python
class ProductListView(ListFilterView):
    rows_name = "products"
```

### Validation failures in list views

`ListFilterView` already uses `Response.validation_error(...)` for invalid query params.

That means invalid pagination, search, or custom filter serializer input automatically returns a standardized `400` response.

## Query Serializer Utilities

Import these from `morest.utils`:

```python
from morest.utils import PaginationSerializer, SearchSerializer, OrderSerializer, PaginationSearchSerializer
```

### `PaginationSerializer`

Adds:

- `page`
- `limit`
- `.paginate(qs, serializer, rows_name=...)`

### `SearchSerializer`

Adds:

- `q`
- `.filter(qs, search_fields)`

### `OrderSerializer`

Adds:

- `order_by`
- `.order(qs, order_fields=...)`

### `PaginationSearchSerializer`

Convenience serializer that combines:

- `PaginationSerializer`
- `SearchSerializer`

If you need all three features, inherit all three explicitly.

```python
class QuerySerializer(PaginationSerializer, SearchSerializer, OrderSerializer):
    ...
```

## Object Lookup Helpers

Import from:

```python
from morest.generics.get_object import get_object_or_404, get_objects_or_404
```

### `get_object_or_404`

```python
user = get_object_or_404(User.objects, id=user_id)
```

Raises `morest.errors.NotFoundError` instead of Django's default 404 type.

### `get_objects_or_404`

```python
user = get_objects_or_404(User.objects, with_error_details=True, id=user_id)
```

If `with_error_details=True`, the raised `NotFoundError` includes the lookup filters.

## Schema Helper for `drf-yasg`

Import from:

```python
from morest.core import docs
```

Use `docs.schema(...)` to wrap view methods with a response envelope schema.

```python
from rest_framework import serializers
from rest_framework.views import APIView
from morest.api import Response
from morest.core import docs


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField()


class UserCreateView(APIView):
    @docs.schema(request_body=CreateUserSerializer, response=UserSerializer)
    def post(self, request):
        ...
        return Response({"id": 1, "username": "john"}, status_code=201, status="created", message="Created")
```

If the request serializer inherits `PaginationSerializer`, `docs.schema()` wraps the response in a paginated envelope automatically.

`drf-yasg` is optional. If it is not installed, `ListFilterView.as_view()` silently skips schema decoration.

## Built-in Auth Views

The package ships simple session-based auth views under `morest.views.auth.session`.

### `LoginView`

- `GET` returns the current authenticated user serialized by `UserSerializer`
- `POST` expects `username` and `password`

Serializer validation errors are returned via:

```python
Response.validation_error(serializer.errors)
```

### `LogoutView`

- `POST` logs out the current session user
- returns `Response.from_status("ok")`

## Admin Form View

`morest.views.AdminFormView` is a DRF `APIView` that renders a Django admin-styled form page.

Use it when you need a custom admin action page backed by a Django form.

```python
from django import forms
from django.http import HttpResponseRedirect
from morest.views import AdminFormView


class SendCreditsForm(forms.Form):
    user_id = forms.IntegerField()
    amount = forms.DecimalField()


class SendCreditsView(AdminFormView):
    form = SendCreditsForm
    action_name = "Send Credits"
    breadcrumbs = (("Home", "/admin/"), ("Send Credits", ""))

    def handle(self, request, form, **kwargs):
        data = form.cleaned_data
        ...
        return HttpResponseRedirect("/admin/")
```

Override these hooks when needed:

- `get_template()`
- `get_action_name()`
- `get_breadcrumbs()`
- `get_context()`
- `handle()`

## Encrypted Text Field

Import from:

```python
from morest.db.fields import EncryptedTextField
```

Example:

```python
from django.db import models
from morest.db.fields import EncryptedTextField


class SecretNote(models.Model):
    title = models.CharField(max_length=255)
    content = EncryptedTextField()
```

You must provide a secret key either:

- per field
- or globally through `DEFAULT_ENCRYPTED_TEXT_FIELD_SECRET_KEY`

Per field:

```python
content = EncryptedTextField(secret_key="your-secret-key")
```

Global setting:

```python
DEFAULT_ENCRYPTED_TEXT_FIELD_SECRET_KEY = "your-secret-key"
```

Behavior:

- values are encrypted before saving to the database
- values are decrypted when loaded from the database
- empty strings are stored as `NULL`

## JSON Encoding

`Response` uses `morest.core.MorestJSONEncoder`, which supports:

- `datetime`
- `date`
- `time`
- `timedelta`
- `decimal.Decimal`
- `uuid.UUID`
- Django lazy `Promise`
- dataclasses

That means you can safely return many Python-native values inside `Response(data=...)` without hand-converting them first.

## Minimal End-to-End Example

```python
from rest_framework import serializers
from morest.api import Response
from morest.views import ListFilterView
from morest.utils import PaginationSerializer, SearchSerializer, OrderSerializer
from morest.errors import NotFoundError
from app.models import Product


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class ProductQuerySerializer(PaginationSerializer, SearchSerializer, OrderSerializer):
    category = serializers.CharField(required=False)


class ProductListView(ListFilterView):
    queryset = Product.objects.all()
    serializer = ProductSerializer
    filter_serializer = ProductQuerySerializer
    search_fields = ["name", "category"]
    order_fields = ["id", "name", "price"]
    rows_name = "products"


def create_product(request):
    serializer = ProductSerializer(data=request.data)
    if not serializer.is_valid():
        return Response.validation_error(serializer.errors)

    return Response(serializer.validated_data, status_code=201, status="created", message="Created")


def delete_product(product):
    if product is None:
        raise NotFoundError(message="Product not found")
```

## Export Summary

Common imports:

```python
from morest.api import Response
from morest.core import docs, get_queryset, search_in_queryset, MorestJSONEncoder, presettings
from morest.errors import *
from morest.utils import PaginationSerializer, SearchSerializer, OrderSerializer, PaginationSearchSerializer
from morest.views import ListFilterView, AdminFormView
```
