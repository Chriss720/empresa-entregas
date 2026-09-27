import uuid
from django.db import transaction
from .models import Pedido

class PedidoService:
    @staticmethod
    def registrar_pedido(direccion_destino: str = "Calle Principal #123") -> Pedido:
        """
        Trámite de negocio: Registrar un nuevo pedido.
        Garantiza la transacción atómica (Unit of Work implícito).
        """
        with transaction.atomic():
            count = Pedido.objects.count() + 1
            folio_generado = f"PED-{count:04d}-{str(uuid.uuid4())[:4].upper()}"

            pedido = Pedido.objects.create(
                folio=folio_generado,
                direccion_destino=direccion_destino or "Calle Principal #123",
                estado='REGISTRADO',
                eta_estimado='30 - 45 minutos (ETA estimado de prueba)'
            )
            return pedido

    @staticmethod
    def obtener_pedido_por_id(pedido_id: int) -> Pedido:
        """
        Recupera un pedido por su identificador único primario.
        """
        return Pedido.objects.get(pk=pedido_id)
