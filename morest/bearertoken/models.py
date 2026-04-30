from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from morest.utils import generate_api_token


class BearerToken(models.Model):
    title = models.CharField(null=True, blank=True, max_length=255)
    key = models.CharField(_("Key"), max_length=40, primary_key=True, default=generate_api_token)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='bearer_tokens',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    metadata = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = 'morest.bearertoken' not in settings.INSTALLED_APPS
        verbose_name = _("Bearer Token")
        verbose_name_plural = _("Bearer Tokens")
        unique_together = ('title', 'user')
        
    def __str__(self):
        return self.key
