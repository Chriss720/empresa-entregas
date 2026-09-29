from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .services import PedidoService
from .models import Pedido


@require_http_methods(["GET", "POST"])
def crear_pedido_view(request):
    """
    Page Controller delgado para el alta de pedidos.
    Aplica el patrón PRG (Post-Redirect-Get).
    No contiene lógica de medios, ni conoce clases como EntregaDron,
    ni sabe qué es route_hint. Todo se delega a PedidoService.
    """
    if request.method == "POST":
        direccion = request.POST.get("direccion_destino", "Calle Principal #123")
        tipo_paquete = request.POST.get("tipo_paquete", "estandar")
        proveedor_ia = request.POST.get("proveedor_ia", "json")

        # Invocación a la Capa de Servicio (orquesta Adapter -> Factory -> Strategy)
        pedido = PedidoService.registrar_pedido(
            direccion_destino=direccion,
            tipo_paquete=tipo_paquete,
            proveedor_ia=proveedor_ia
        )

        # Redirección PRG: Evita resometer el formulario con F5
        return redirect('detalle_pedido', pedido_id=pedido.id)

    # Si es GET /pedidos, renderiza el formulario de registro
    return render(request, 'entregas/formulario_pedido.html')


@require_http_methods(["GET"])
def detalle_pedido_view(request, pedido_id):
    """
    Page Controller para el panel web de seguimiento.
    Obtiene los datos precalculados de PedidoService y construye el context.
    CERO lógica o consultas SQL en la plantilla (Template View).
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    context = {
        'pedido': pedido,
        'folio': pedido.folio,
        'direccion_destino': pedido.direccion_destino,
        'estado': pedido.get_estado_display(),
        'medio_transporte': pedido.medio_transporte,
        'motivo_asignacion': pedido.motivo_asignacion,
        'eta_estimado': pedido.eta_estimado,
        'detalles_plan': pedido.detalles_plan,
        'fecha_creacion': pedido.fecha_creacion,
    }
    return render(request, 'entregas/seguimiento.html', context)


@require_http_methods(["GET"])
def pedido_json_view(request, pedido_id):
    """
    Contrato API para el cliente móvil: GET /pedidos/<id>/json (o /api/pedidos/<id>)
    Retorna el pedido estructurado en formato JSON ligero en una sola petición.
    Reutiliza la misma capa de servicio/modelo sin duplicar lógica.
    Resuelve el inconveniente 5: El panel y la app no tienen la misma hambre.
    Evita las doce peticiones para pintar el inicio mediante un recurso de agregación.
    """
    try:
        pedido = PedidoService.obtener_pedido_por_id(pedido_id)
    except Pedido.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado", "id": pedido_id}, status=404)

    return JsonResponse({
        # JSON mínimo solicitado explícitamente para el cliente móvil:
        "folio": pedido.folio,
        "estado": pedido.estado,
        "eta": pedido.eta_estimado,
        # Recurso de agregación consolidado (evita que la app móvil haga 12 peticiones para el inicio):
        "medio_transporte": pedido.medio_transporte,
        "motivo_asignacion": pedido.motivo_asignacion,
        "eta_estimado": pedido.eta_estimado,
        "direccion_destino": pedido.direccion_destino,
        "detalles_plan": pedido.detalles_plan,
        "fecha_creacion": pedido.fecha_creacion.isoformat(),
    })


@require_http_methods(["GET"])
def descargar_guia_view(request, pedido_id):
    """
    Generación de Guía de Envío descargable (Inconveniente 7 del enunciado):
    Demuestra cómo 'saber decir que no' al Golden Hammer (Event Sourcing, CQRS, Redux global).
    El trámite real es directo: consultar el pedido existente y emitir el documento.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    contenido_guia = (
        f"====================================================\n"
        f"       GUIA DE ENVIO - EMPRESA DE ENTREGAS\n"
        f"====================================================\n"
        f"Folio:             {pedido.folio}\n"
        f"Estado:            {pedido.get_estado_display()}\n"
        f"Fecha de Creacion: {pedido.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"----------------------------------------------------\n"
        f"Destino:           {pedido.direccion_destino}\n"
        f"Medio Asignado:    {pedido.medio_transporte}\n"
        f"ETA Estimado:      {pedido.eta_estimado}\n"
        f"Motivo Asignacion: {pedido.motivo_asignacion}\n"
        f"Detalles Plan:     {pedido.detalles_plan}\n"
        f"====================================================\n"
        f"Generado limpiamente en Django sin sobreingenieria.\n"
        f"Rechazo formal de Event Sourcing / CQRS innecesario.\n"
        f"====================================================\n"
    )

    response = HttpResponse(contenido_guia, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="guia_{pedido.folio}.txt"'
    return response
