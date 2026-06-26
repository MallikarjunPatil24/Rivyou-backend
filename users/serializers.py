from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        read_only_fields = ['id']

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError('Enter a valid email address.')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def create(self, validated_data):
        """Create user with hashed password."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

    def to_representation(self, instance):
        """Return only id, username, email (exclude password)."""
        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
        }


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Basic user info serializer."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']
