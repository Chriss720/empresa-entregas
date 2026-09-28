from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PlanEntrega:
    """
    Representa el resultado de la planificación logística efectuada por una estrategia.
    Contiene la estimación de tiempos, costos e instrucciones operativas.
    """
    medio: str
    tiempo_estimado: str
    costo: float
    instrucciones_ruta: str
    detalles: str


class MedioDeEntrega(ABC):
    """
    Contrato Strategy: MedioDeEntrega.planear(pedido, contexto) -> PlanEntrega
    Cada medio implementa su propio algoritmo de cálculo y despacho.
    """

    @abstractmethod
    def planear(self, pedido: Any = None, contexto: Optional[dict] = None) -> PlanEntrega:
        """
        Calcula y genera el plan de entrega específico para este medio.
        """
        pass


class EntregaCamioneta(MedioDeEntrega):
    """
    Estrategia para entregas terrestres de carga pesada o volumen medio/alto.
    Utiliza vialidades principales y considera tiempos de tráfico vehicular estándar.
    """

    def planear(self, pedido: Any = None, contexto: Optional[dict] = None) -> PlanEntrega:
        return PlanEntrega(
            medio="Camioneta",
            tiempo_estimado="45 a 60 minutos",
            costo=120.00,
            instrucciones_ruta="Vialidades principales y avenidas de alto flujo. Carga en bahía norte.",
            detalles="Ruta vehicular terrestre optimizada para paquetes voluminosos o consolidados."
        )


class EntregaMotocicleta(MedioDeEntrega):
    """
    Estrategia para entregas urbanas intermedias con agilidad ante tráfico vehicular.
    """

    def planear(self, pedido: Any = None, contexto: Optional[dict] = None) -> PlanEntrega:
        return PlanEntrega(
            medio="Motocicleta",
            tiempo_estimado="25 a 35 minutos",
            costo=65.00,
            instrucciones_ruta="Filtrado en zonas de tráfico denso y corredores urbanos primarios.",
            detalles="Despacho ágil en moto para paquetes medianos o entrega exprés urbana."
        )


class EntregaBicicleta(MedioDeEntrega):
    """
    Estrategia de última milla ecológica, ideal para radios urbanos cortos y zonas peatonales.
    """

    def planear(self, pedido: Any = None, contexto: Optional[dict] = None) -> PlanEntrega:
        return PlanEntrega(
            medio="Bicicleta",
            tiempo_estimado="20 a 30 minutos",
            costo=35.00,
            instrucciones_ruta="Red de ciclovías y andadores peatonales autorizados. Radio < 5km.",
            detalles="Transporte sustentable con cero emisiones en perímetro céntrico."
        )


class EntregaDron(MedioDeEntrega):
    """
    Estrategia de despacho aéreo no tripulado para paquetería ligera y máxima urgencia.
    """

    def planear(self, pedido: Any = None, contexto: Optional[dict] = None) -> PlanEntrega:
        return PlanEntrega(
            medio="Dron",
            tiempo_estimado="10 a 15 minutos",
            costo=95.00,
            instrucciones_ruta="Corredor aéreo automatizado a 120m AGL. Vector directo punto a punto.",
            detalles="Vuelo autónomo punto a punto esquivando tráfico terrestre y semáforos."
        )
