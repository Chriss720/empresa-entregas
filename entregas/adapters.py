import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Sugerencia:
    """
    Entidad del dominio que representa la recomendación logística homologada.
    El dominio SOLO entiende este contrato: medio sugerido y motivo.
    Términos externos como 'route_hint', 'score' o estructuras XML no existen aquí.
    """
    medio: str
    motivo: str


# =====================================================================
# Proveedores Externos Simulados (Vocabularios y formatos heterogéneos)
# =====================================================================

class ProveedorIAJsonSimulado:
    """
    Simula un servicio de IA moderno (HTTP REST) que responde en formato JSON
    con vocabulario técnico propietario ('route_hint', 'score', etc.).
    """

    @staticmethod
    def consultar_optimizador(datos: dict) -> str:
        # Simulamos respuesta basada en características del contexto
        tipo = datos.get("tipo_paquete", "ligero").lower()
        if tipo in ["urgente", "ligero", "documento"]:
            payload = {
                "route_hint": "sector_skyway_alpha_09",
                "score": 0.98,
                "selected_transport": "dron",
                "reasoning": "Paquete ultraligero y ventana de entrega urgente. Ruta aérea recomendada sin tráfico."
            }
        elif tipo in ["pesado", "voluminoso", "mudanza"]:
            payload = {
                "route_hint": "highway_arterial_beta_01",
                "score": 0.92,
                "selected_transport": "camioneta",
                "reasoning": "Carga de gran volumen requiere bahía de estiba terrestre."
            }
        else:
            payload = {
                "route_hint": "urban_inner_ring_delta_04",
                "score": 0.89,
                "selected_transport": "motocicleta",
                "reasoning": "Paquete mediano; ruta óptima por vías de tráfico moderado."
            }
        return json.dumps(payload)


class ProveedorIAXmlSimulado:
    """
    Simula un servicio externo heredado (Legacy SOAP/XML) con tags en XML.
    """

    @staticmethod
    def consultar_optimizador_legacy(datos: dict) -> str:
        tipo = datos.get("tipo_paquete", "estandar").lower()
        if tipo in ["ecologico", "centro", "bici"]:
            return """<?xml version="1.0" encoding="UTF-8"?>
            <logistics_recommendation>
                <vehicle>bicicleta</vehicle>
                <confidence>0.94</confidence>
                <notes>Zona peatonal céntrica con ciclovía designada y cero emisiones requeridas.</notes>
            </logistics_recommendation>"""
        elif tipo in ["pesado", "voluminoso"]:
            return """<?xml version="1.0" encoding="UTF-8"?>
            <logistics_recommendation>
                <vehicle>camioneta</vehicle>
                <confidence>0.91</confidence>
                <notes>Carga sobredimensionada requiere plataforma de carga pesada.</notes>
            </logistics_recommendation>"""
        else:
            return """<?xml version="1.0" encoding="UTF-8"?>
            <logistics_recommendation>
                <vehicle>motocicleta</vehicle>
                <confidence>0.87</confidence>
                <notes>Mensajería urbana estándar para tránsito ágil.</notes>
            </logistics_recommendation>"""


# =====================================================================
# Adaptadores (Adapter Pattern)
# Aíslan y traducen el idioma ajeno al concepto de dominio: Sugerencia
# =====================================================================

class AsesorLogisticoAdapter(ABC):
    """
    Interfaz esperada por el dominio para obtener sugerencias de transporte.
    """

    @abstractmethod
    def obtener_sugerencia(self, contexto: dict) -> Sugerencia:
        """
        Consulta al proveedor externo y devuelve una Sugerencia homologada.
        """
        pass


class JsonIAAdapter(AsesorLogisticoAdapter):
    """
    Adaptador para el proveedor JSON.
    Parsea 'route_hint' y 'score' y los traduce a Sugerencia(medio, motivo).
    Garantiza que 'route_hint' NUNCA escape a la vista o al dominio.
    """

    def __init__(self, cliente_api: Optional[ProveedorIAJsonSimulado] = None):
        self.cliente = cliente_api or ProveedorIAJsonSimulado()

    def obtener_sugerencia(self, contexto: dict) -> Sugerencia:
        raw_json = self.cliente.consultar_optimizador(contexto)
        data = json.loads(raw_json)

        # 'route_hint' y 'score' son procesados y absorbidos aquí en el Adapter
        route_hint = data.get("route_hint", "desconocida")
        score = data.get("score", 0.0)
        vehiculo = data.get("selected_transport", "camioneta").strip().lower()
        reasoning = data.get("reasoning", "Asignado por optimizador JSON")

        motivo_homologado = (
            f"IA JSON (Confianza: {score*100:.0f}%, Corredor: {route_hint}): {reasoning}"
        )

        return Sugerencia(
            medio=vehiculo,
            motivo=motivo_homologado
        )


class XmlIAAdapter(AsesorLogisticoAdapter):
    """
    Adaptador para el proveedor Legacy XML.
    Parsea los nodos <vehicle> y <notes> y produce una Sugerencia homologada.
    """

    def __init__(self, cliente_api: Optional[ProveedorIAXmlSimulado] = None):
        self.cliente = cliente_api or ProveedorIAXmlSimulado()

    def obtener_sugerencia(self, contexto: dict) -> Sugerencia:
        raw_xml = self.cliente.consultar_optimizador_legacy(contexto)
        root = ET.fromstring(raw_xml.strip())

        vehiculo_node = root.find("vehicle")
        notes_node = root.find("notes")
        conf_node = root.find("confidence")

        vehiculo = vehiculo_node.text.strip().lower() if vehiculo_node is not None else "camioneta"
        notes = notes_node.text.strip() if notes_node is not None else "Sin notas del proveedor"
        confidence = float(conf_node.text.strip()) if conf_node is not None else 1.0

        motivo_homologado = (
            f"IA Legacy XML (Confianza: {confidence*100:.0f}%): {notes}"
        )

        return Sugerencia(
            medio=vehiculo,
            motivo=motivo_homologado
        )


def obtener_adaptador_ia(proveedor: str = "json") -> AsesorLogisticoAdapter:
    """
    Función de utilidad para resolver la instancia del adaptador solicitado.
    Por defecto utiliza el adaptador JSON de IA moderna.
    """
    proveedor_limpio = (proveedor or "").strip().lower()
    if proveedor_limpio == "xml":
        return XmlIAAdapter()
    return JsonIAAdapter()
