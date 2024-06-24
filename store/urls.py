from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductList.as_view()),
    path('products/<int:id>/', views.ProductDetail.as_view()),
    path('collections/<int:pk>/', views.CollectionDetail.as_view(), name='collection-detail'),
    path('collections/', views.CollectionList.as_view(), name='collection'),
]
