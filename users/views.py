from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer, RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class FollowUserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        user_to_follow = get_object_or_404(User, pk=pk)
        
        if user_to_follow == request.user:
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.following.filter(pk=pk).exists():
            request.user.following.remove(user_to_follow)
            return Response({'message': f'You unfollowed {user_to_follow.username}'}, status=status.HTTP_200_OK)
        else:
            request.user.following.add(user_to_follow)
            return Response({'message': f'You followed {user_to_follow.username}'}, status=status.HTTP_200_OK)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
