from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    """
    POST /api/auth/register
    Creates a new user and returns user info + access token.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                name='RegisterSuccessResponse',
                fields={
                    'id': serializers.IntegerField(),
                    'username': serializers.CharField(),
                    'token': serializers.CharField()
                }
            )
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    'id': user.id,
                    'username': user.username,
                    'token': tokens['access'],
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login
    Validates credentials and returns JWT access token + user info.
    Returns 401 on invalid credentials.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name='LoginSuccessResponse',
                fields={
                    'token': serializers.CharField(),
                    'user': inline_serializer(
                        name='LoginUserResponse',
                        fields={
                            'id': serializers.IntegerField(),
                            'username': serializers.CharField(),
                        }
                    )
                }
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = get_tokens_for_user(user)

        return Response(
            {
                'token': tokens['access'],
                'user': {
                    'id': user.id,
                    'username': user.username
                },
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout
    Requires Authorization: Bearer <token> header.
    Blacklists the refresh token to invalidate the session.
    Returns {"message": "Logged out successfully"}.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name='LogoutRequest',
            fields={
                'refresh': serializers.CharField()
            }
        ),
        responses={
            200: inline_serializer(
                name='LogoutResponse',
                fields={
                    'message': serializers.CharField()
                }
            )
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
        except Exception:
            # Even if blacklist fails, acknowledge logout
            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
