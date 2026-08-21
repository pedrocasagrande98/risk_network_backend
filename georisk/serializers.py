from rest_framework import serializers
from .models import GeoEvent

class GeoEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = GeoEvent
        fields = ['id', 'user', 'username', 'user_avatar', 'type', 'severity', 'description', 'latitude', 'longitude', 'event_date', 'created_at', 'status', 'flood_geojson', 'streets_geojson']
        read_only_fields = ['user', 'status', 'flood_geojson', 'streets_geojson']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            # Retorna o campo data para o frontend ler
            if 'event_date' in representation:
                representation['data'] = representation['event_date']
        except Exception:
            pass
        return representation

    def to_internal_value(self, data):
        try:
            # Permite que o frontend envie 'data' no POST e mapeia para 'event_date'
            if hasattr(data, 'copy'):
                mutable_data = data.copy()
            elif isinstance(data, dict):
                mutable_data = dict(data)
            else:
                mutable_data = data

            if 'data' in mutable_data:
                mutable_data['event_date'] = mutable_data['data']
            return super().to_internal_value(mutable_data)
        except Exception:
            return super().to_internal_value(data)
