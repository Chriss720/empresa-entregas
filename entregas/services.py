import uuid
from typing import Optional
from django.db import transaction
from .models import Pedido
from .adapters import Sugerencia, AsesorLogisticoAdapter, obtener_adaptador_ia
from .factories import FabricaMediosEntrega
from .strategies import PlanEntrega


class PedidoService:
    """
    Capa de Servicio (Service Layer) que encapsula la lógica de negocio y trámites.
    Orquesta la interacción entre patrones:
      Adapter -> Simple Factory -> Strategy -> Persistencia (Unit of Work implícito)
    """

    @staticmethod
    def registrar_pedido(
        direccion_destino: str = "Calle Principal #123",
        tipo_paquete: str = "estandar",
        proveedor_ia: str = "json"
    ) -> Pedido:
        """
        Trámite de negocio principal:
        1. Adapter: Traduce la respuesta externa (JSON o XML) a Sugerencia(medio, motivo).
           'route_hint' y el formato ajeno mueren en el adaptador.
        2. Fábrica Simple: Resuelve quién hace el new instanciando el MedioDeEntrega.
        3. Strategy: Ejecuta medio.planear(pedido, contexto) para obtener el PlanEntrega.
        4. Persiste el pedido dentro de una transacción atómica.
        """
        with transaction.atomic():
            # Paso 1: Adapter (Homologación del proveedor externo a dominio)
            adaptador: AsesorLogisticoAdapter = obtener_adaptador_ia(proveedor_ia)
            contexto_ia = {
                "direccion": direccion_destino,
                "tipo_paquete": tipo_paquete
            }
            sugerencia: Sugerencia = adaptador.obtener_sugerencia(contexto_ia)

            # Paso 2: Quién hace el new (Fábrica Simple)
            medio_entrega = FabricaMediosEntrega.crear(sugerencia.medio)

            # Paso 3: Strategy (Cálculo del plan logístico según el medio)
            contexto_estrategia = {
                "direccion": direccion_destino,
                "tipo_paquete": tipo_paquete
            }
            plan: PlanEntrega = medio_entrega.planear(contexto=contexto_estrategia)

            # Paso 4: Persistencia atómica
            count = Pedido.objects.count() + 1
            folio_generado = f"PED-{count:04d}-{str(uuid.uuid4())[:4].upper()}"

            pedido = Pedido.objects.create(
                folio=folio_generado,
                direccion_destino=direccion_destino or "Calle Principal #123",
                estado='REGISTRADO',
                medio_transporte=plan.medio,
                motivo_asignacion=sugerencia.motivo,
                eta_estimado=plan.tiempo_estimado,
                detalles_plan=f"{plan.detalles} | Ruta: {plan.instrucciones_ruta} | Costo: ${plan.costo:.2f}"
            )
            return pedido

    @staticmethod
    def obtener_pedido_por_id(pedido_id: int) -> Pedido:
        """
        Recupera un pedido por su identificador primario.
        """
        return Pedido.objects.get(pk=pedido_id)
