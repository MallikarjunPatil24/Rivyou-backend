from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import SearchLog
from .serializers import SearchLogSerializer

class SearchHistoryView(APIView):
    """
    GET /api/analytics/history
    Requires JWT authentication.
    Returns search query history of the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: SearchLogSerializer(many=True)}
    )
    def get(self, request):
        logs = SearchLog.objects.filter(user=request.user)
        serializer = SearchLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
