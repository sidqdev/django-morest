from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import empty
from morest.services import CloudflareCaptchaService
from morest.errors import CaptchaTokenIsInvalidError


class CloudflareCaptchaSerializer(serializers.Serializer):
    captcha_token = serializers.CharField()

    def get_captcha_service(self):
        return CloudflareCaptchaService(
            secret_key=getattr(settings, 'CLOUDFLARE_CAPTCHA_SECRET_KEY'),
            super_token=getattr(settings, 'CLOUDFLARE_CAPTCHA_SUPER_TOKEN', None),
        )
    
    def to_internal_value(self, data):
        if not hasattr(data, 'get'):
            return super().to_internal_value(data)

        if not self.get_captcha_service().verify(
            token=data.get('captcha_token', empty),
        ):
            raise CaptchaTokenIsInvalidError

        attrs = super().to_internal_value(data)
        attrs.pop('captcha_token', None)
        return attrs
