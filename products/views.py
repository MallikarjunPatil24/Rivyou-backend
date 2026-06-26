from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer

from .models import Product
from .serializers import ProductSerializer, ProductSearchResultSerializer
from .search import search_products

class ProductSearchView(APIView):
    """
    GET /api/products/search
    Requires JWT authentication.
    Returns sorted ranked products by query relevance.
    Includes spelling/typo correction, background search history logging, and caching.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
            OpenApiParameter(name='limit', description='Maximum results to return', required=False, type=int),
            OpenApiParameter(name='category_filter', description='Filter by category name', required=False, type=str),
        ],
        responses={
            200: inline_serializer(
                name='ProductSearchResponse',
                fields={
                    'query': serializers.CharField(),
                    'total_results': serializers.IntegerField(),
                    'results': ProductSearchResultSerializer(many=True)
                }
            )
        }
    )
    def get(self, request):
        query = request.query_params.get('q')
        if not query:
            return Response(
                {"error": "Search query 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        limit_param = request.query_params.get('limit', '20')
        try:
            limit = int(limit_param)
        except ValueError:
            limit = 20

        category_filter = request.query_params.get('category_filter')

        # Caching optimization
        user_prefix = f"user_{request.user.id}" if request.user.is_authenticated else "anon"
        cache_key = f"search_{user_prefix}_{query}_{limit}_{category_filter or ''}"
        
        cached_response = cache.get(cache_key)
        if cached_response:
            # Log the search in background (non-blocking)
            from analytics.utils import log_search_async
            log_search_async(request.user, query, cached_response.get("total_results", 0))
            return Response(cached_response, status=status.HTTP_200_OK)

        # Run search logic
        results = search_products(query, limit=None, category_filter=category_filter)
        total_results = len(results)

        if not results:
            response_data = {
                "query": query,
                "total_results": 0,
                "results": []
            }
            # Log search in background
            from analytics.utils import log_search_async
            log_search_async(request.user, query, 0)
            
            cache.set(cache_key, response_data, 300) # Cache for 5 mins
            return Response(response_data, status=status.HTTP_200_OK)

        # Apply page limit to results
        limited_results = results[:limit]

        # Map list of dicts to Product objects using the serializer for consistency,
        # preserving the rank order of the search results
        product_ids = [item['id'] for item in limited_results]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        ordered_products = []
        relevance_scores = {}
        rank_reasons = {}

        for item in limited_results:
            pid = item['id']
            if pid in product_map:
                ordered_products.append(product_map[pid])
                relevance_scores[pid] = item['relevance_score']
                rank_reasons[pid] = item['rank_reason']

        serializer = ProductSearchResultSerializer(
            ordered_products,
            many=True,
            context={
                'relevance_scores': relevance_scores,
                'rank_reasons': rank_reasons
            }
        )

        response_data = {
            "query": query,
            "total_results": total_results,
            "results": serializer.data
        }

        # Log search in background
        from analytics.utils import log_search_async
        log_search_async(request.user, query, total_results)

        cache.set(cache_key, response_data, 300) # Cache for 5 mins
        return Response(response_data, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """
    GET /api/products/<int:pk>
    Requires JWT authentication.
    Returns details of a single product.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ProductSerializer}
    )
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductByCategoryView(APIView):
    """
    GET /api/products/category/<str:category>
    Requires JWT authentication.
    Returns all products matching the specified category (case-insensitive).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ProductSerializer(many=True)}
    )
    def get(self, request, category):
        products = Product.objects.filter(category__iexact=category)
        if not products.exists():
            return Response(
                {"error": "No products found in this category"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
