from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from morest.bearertoken.models import BearerToken


User = get_user_model()


class BearerTokenAdmin(admin.ModelAdmin):
    list_display = ('title', 'key', 'user', 'is_active', 'expires_at', 'created_at')
    readonly_fields = ('key',)
    list_filter = ('is_active', 'expires_at', 'created_at',)
    autocomplete_fields = ('user',)
    search_fields = ('title', 'key', 'user__%s' % User.USERNAME_FIELD,)


admin.site.register(BearerToken, BearerTokenAdmin)
