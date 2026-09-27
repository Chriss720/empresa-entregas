from django.urls import path
from . import views

urlpatterns = [
    path('pedidos', views.crear_pedido_view, name='crear_pedido'),
    path('pedidos/<int:pedido_id>', views.detalle_pedido_view, name='detalle_pedido'),
]
