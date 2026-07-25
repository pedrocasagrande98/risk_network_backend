from django.contrib import admin
from .models import Tweet, Like, Comment

admin.site.register(Tweet)
admin.site.register(Like)
admin.site.register(Comment)
