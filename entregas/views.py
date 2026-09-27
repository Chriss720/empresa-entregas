from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from .services import PedidoService

@require_http_methods(["GET", "POST"])
def crear_pedido_view(request):
    """
    Page Controller delgado para el trámite de alta de pedidos.
    Aplica el patrón PRG (Post-Redirect-Get).
    """
    if request.method == "POST":
        direccion = request.POST.get("direccion_destino", "Calle Ficticia #456")
        
        # Invocación a la Capa de Servicio (Trámite de Negocio)
        pedido = PedidoService.registrar_pedido(direccion_destino=direccion)
        
        # Redirección PRG: Evita resometer el formulario en F5
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    # Si es GET /pedidos, renderizamos el formulario de alta
    return render(request, 'entregas/formulario_pedido.html')


@require_http_methods(["GET"])
def detalle_pedido_view(request, pedido_id):
    """
    Page Controller para el seguimiento del pedido.
    Recupera los datos precalculados de la capa de servicio y construye
    el diccionario context sin realizar lógica ni consultas SQL en la plantilla.
    """
    pedido = PedidoService.obtener_pedido_por_id(pedido_id)
    
    # El contexto llega listo para la Template View
    context = {
        'pedido': pedido,
        'folio': pedido.folio,
        'direccion_destino': pedido.direccion_destino,
        'estado': pedido.get_estado_display(),
        'eta_estimado': pedido.eta_estimado,
        'fecha_creacion': pedido.fecha_creacion,
    }
    return render(request, 'entregas/seguimiento.html', context)
