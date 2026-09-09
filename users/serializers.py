from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    followers_list = serializers.SerializerMethodField()
    following_list = serializers.SerializerMethodField()
    current_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'current_password', 'password', 'bio', 'avatar', 'followers_count', 'following_count', 'followers_list', 'following_list')
        read_only_fields = ('id', 'email')

    def validate(self, attrs):
        new_password = attrs.get('password')
        current_password = attrs.get('current_password')

        if new_password:
            if not current_password:
                raise serializers.ValidationError({"current_password": "É necessário informar a senha atual para alterá-la."})
            if not self.instance.check_password(current_password):
                raise serializers.ValidationError({"current_password": "A senha atual está incorreta."})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('current_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_followers_list(self, obj):
        return obj.followers.values('id', 'username')

    def get_following_list(self, obj):
        return obj.following.values('id', 'username')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.avatar:
            try:
                url = instance.avatar.url
                request = self.context.get('request')
                if request and not url.startswith(('http://', 'https://')):
                    ret['avatar'] = request.build_absolute_uri(url)
                else:
                    ret['avatar'] = url
            except Exception:
                ret['avatar'] = None
        return ret

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
