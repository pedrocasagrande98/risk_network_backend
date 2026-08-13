from rest_framework import serializers
from .models import GeoEvent

class GeoEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GeoEvent
        fields = ['id', 'user', 'username', 'type', 'severity', 'description', 'latitude', 'longitude', 'event_date', 'created_at']
        read_only_fields = ['user']
