from django.urls import path, include
from rest_framework.routers import SimpleRouter, DefaultRouter
from . import views

router = DefaultRouter()
router.register('products', views.ProductViewSets)
router.register('collections', views.CollectionViewSet)
# router.urls
print(router.urls)

urlpatterns = [
        path('', include(router.urls)),
        path('products/', views.ProductList.as_view()),
        path('products/<int:id>/', views.ProductDetail.as_view()),
        path('collections/<int:pk>/', views.CollectionDetail.as_view(), name='collection-detail'),
        path('collections/', views.CollectionList.as_view(), name='collection')
]

#urlpatterns = router.urls