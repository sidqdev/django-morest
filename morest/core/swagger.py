from rest_framework import serializers


def build_response_serializer(serializer) -> serializers.Serializer:
    class Response(serializers.Serializer):
        data = serializer()
        status = serializers.CharField()
        status_code = serializers.IntegerField()
        request_id = serializers.CharField()
        message = serializers.CharField()
    
    return Response