from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProductSearchResultSerializer(serializers.ModelSerializer):
    relevance_score = serializers.SerializerMethodField()
    rank_reason = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'product_name', 'category', 'tags', 'relevance_score', 'rank_reason']

    def get_relevance_score(self, obj):
        # This will be populated dynamically in the view/context
        return self.context.get('relevance_scores', {}).get(obj.id, 0.0)

    def get_rank_reason(self, obj):
        # This will be populated dynamically in the view/context
        return self.context.get('rank_reasons', {}).get(obj.id, "N/A")
