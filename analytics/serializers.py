from rest_framework import serializers
from .models import SearchLog

class SearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchLog
        fields = ['id', 'query', 'results_count', 'created_at']
        read_only_fields = ['id', 'created_at']
