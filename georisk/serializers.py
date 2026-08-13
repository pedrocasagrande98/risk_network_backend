from rest_framework import serializers
from .models import GeoEvent

class GeoEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GeoEvent
        fields = ['id', 'user', 'username', 'type', 'severity', 'description', 'latitude', 'longitude', 'event_date', 'created_at']
        read_only_fields = ['user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Retorna o campo data para o frontend ler
        representation['data'] = representation.get('event_date')
        return representation

    def to_internal_value(self, data):
        # Permite que o frontend envie 'data' no POST e mapeia para 'event_date'
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        if 'data' in mutable_data:
            mutable_data['event_date'] = mutable_data['data']
        return super().to_internal_value(mutable_data)
