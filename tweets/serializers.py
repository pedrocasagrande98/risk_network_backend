from rest_framework import serializers
from .models import Tweet, Like, Comment
from users.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'tweet', 'content', 'created_at')
        read_only_fields = ('id', 'user', 'tweet', 'created_at')

from georisk.models import GeoEvent
from georisk.serializers import GeoEventSerializer

class TweetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    geo_event = GeoEventSerializer(read_only=True)
    geo_event_id = serializers.PrimaryKeyRelatedField(queryset=GeoEvent.objects.all(), source='geo_event', write_only=True, required=False)

    class Meta:
        model = Tweet
        fields = ('id', 'author', 'content', 'created_at', 'updated_at', 'likes_count', 'comments_count', 'is_liked', 'geo_event', 'geo_event_id')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
