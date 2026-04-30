from rest_framework import serializers


class RefreshTokenRequest(serializers.Serializer):
    refresh_token = serializers.CharField()


class RefreshTokenResponse(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()

