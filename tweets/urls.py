from django.urls import path
from .views import TweetListCreateView, TweetDetailView, FeedView, LikeTweetView, CommentListCreateView

urlpatterns = [
    path('', TweetListCreateView.as_view(), name='tweet-list-create'),
    path('feed/', FeedView.as_view(), name='tweet-feed'),
    path('<int:pk>/', TweetDetailView.as_view(), name='tweet-detail'),
    path('<int:pk>/like/', LikeTweetView.as_view(), name='tweet-like'),
    path('<int:pk>/comments/', CommentListCreateView.as_view(), name='tweet-comments'),
]
