from django.urls import path, include
# from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSets, basename='products')
router.register('collections', views.CollectionViewSet, basename='collections')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product') #Prefix for lookup pk (product_pk)
products_router.register('reviews', views.ReviewViewSet, basename='product-reviews')
# router.urls

urlpatterns = [
        path('', include(router.urls)),
        path('', include(products_router.urls)),
        path('products/', views.ProductList.as_view()),
        path('products/<int:id>/', views.ProductDetail.as_view()),
        path('collections/<int:pk>/', views.CollectionDetail.as_view(), name='collection-detail'),
        path('collections/', views.CollectionList.as_view(), name='collection')
]

#urlpatterns = router.urls