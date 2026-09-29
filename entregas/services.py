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
            # Simulación de cobro seguro dentro de la transacción
            # Si esto fallara (ej. ValueError), la transacción haría rollback automático.
            print(f"[Transaccion] Realizando cobro simulado para paquete '{tipo_paquete}'...")

            # Paso 1: Adapter (Homologación del proveedor externo a dominio)
            adaptador: AsesorLogisticoAdapter = obtener_adaptador_ia(proveedor_ia)
            contexto_ia = {
                "direccion": direccion_destino,
                "tipo_paquete": tipo_paquete
            }
            
            try:
                # Intento de comunicación externa
                sugerencia: Sugerencia = adaptador.obtener_sugerencia(contexto_ia)
            except TimeoutError:
                # Degradación elegante: La IA se cayó, pero el sistema no debe fallar.
                print("[Fallo Externo] La IA no respondio (Timeout). Asignando fallback seguro...")
                sugerencia = Sugerencia(
                    medio="camioneta",
                    motivo="IA no disponible (Fallo de conexión). Asignación por defecto en modo Offline."
                )

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
            
            # El aviso (correo) va DESPUÉS de que la transacción confirmó. 
            # Si el aviso falla, el pedido SÍ quedó persistido. Observer no sustituye la transacción.
            transaction.on_commit(
                lambda: print(f"[Aviso/Correo] El pedido {pedido.folio} ha sido confirmado con exito. Notificando al cliente.")
            )

            return pedido

    @staticmethod
    def obtener_pedido_por_id(pedido_id: int) -> Pedido:
        """
        Recupera un pedido por su identificador primario.
        """
        return Pedido.objects.get(pk=pedido_id)
