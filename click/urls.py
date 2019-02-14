from django.urls import path
from . import views

urlpatterns = [
    path('process/click/prepare', views.prepare, name = 'prepare'),
    path('process/click/complete', views.complete, name = 'complete'),
    path('process/click/service/<service_type>', views.service, name = 'service')
]