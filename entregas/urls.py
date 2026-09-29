from django.urls import path
from . import views

urlpatterns = [
    path('pedidos', views.crear_pedido_view, name='crear_pedido'),
    path('pedidos/<int:pedido_id>', views.detalle_pedido_view, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/json', views.pedido_json_view, name='pedido_json'),
    path('api/pedidos/<int:pedido_id>', views.pedido_json_view, name='api_pedido_json'),
    path('pedidos/<int:pedido_id>/guia', views.descargar_guia_view, name='descargar_guia'),
]
