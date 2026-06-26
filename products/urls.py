from django.urls import path
from .views import ProductSearchView, ProductDetailView, ProductByCategoryView

urlpatterns = [
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('category/<str:category>/', ProductByCategoryView.as_view(), name='product-by-category'),
]
