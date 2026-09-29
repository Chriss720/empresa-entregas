from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda req: redirect('crear_pedido')),
    path('', include('entregas.urls')),
]
