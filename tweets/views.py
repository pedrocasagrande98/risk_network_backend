from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Tweet, Like, Comment
from .serializers import TweetSerializer, CommentSerializer

class TweetListCreateView(generics.ListCreateAPIView):
    queryset = Tweet.objects.all().order_by('-created_at')
    serializer_class = TweetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class TweetDetailView(generics.RetrieveDestroyAPIView):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_destroy(self, instance):
        if instance.author == self.request.user:
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own tweets.")

class FeedView(generics.ListAPIView):
    serializer_class = TweetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        followed_users = user.following.all()
        return Tweet.objects.filter(author__in=followed_users).order_by('-created_at')

class LikeTweetView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)
        
        if not created:
            like.delete()
            return Response({'message': 'Tweet unliked'}, status=status.HTTP_200_OK)
        return Response({'message': 'Tweet liked'}, status=status.HTTP_201_CREATED)

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Comment.objects.filter(tweet_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        tweet = get_object_or_404(Tweet, pk=self.kwargs['pk'])
        serializer.save(user=self.request.user, tweet=tweet)
