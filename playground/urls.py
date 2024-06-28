from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.say_hello),
    path('mails/', views.mails),
    path('celery-tasks/', views.send_marketing_mails),
    path('cache-test/', views.cache_test),
    path('cache-test2/', views.cache_test2),
    path('cache-test3/', views.HelloCache.as_view())
]
