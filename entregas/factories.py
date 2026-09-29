from typing import Type
from .strategies import (
    MedioDeEntrega,
    EntregaCamioneta,
    EntregaMotocicleta,
    EntregaBicicleta,
    EntregaDron,
)


class FabricaMediosEntrega:
    """
    Fábrica Simple (Simple Factory):
    Responsable de instanciar la clase concreta adecuada de MedioDeEntrega (Strategy)
    a partir del string normalizado provisto en la Sugerencia.

    ¿Por qué Fábrica Simple y NO Factory Method?
    No existen familias de trámite ni jerarquías de creadores que requieran
    polimorfismo o sobreescritura del gancho de creación en subclases.
    Usar Factory Method aquí solo inflaría la jerarquía para disfrazar una
    selección directa. La Fábrica Simple concentra el 'new' en un único punto desacoplado.
    """

    _MEDIOS: dict[str, Type[MedioDeEntrega]] = {
        "camioneta": EntregaCamioneta,
        "motocicleta": EntregaMotocicleta,
        "bicicleta": EntregaBicicleta,
        "dron": EntregaDron,
    }

    @classmethod
    def crear(cls, medio: str) -> MedioDeEntrega:
        """
        Instancia y retorna la estrategia correspondiente al nombre del medio.
        Si el medio no se reconoce, recurre a Camioneta como fallback seguro.
        """
        clave = (medio or "").strip().lower()
        clase_estrategia = cls._MEDIOS.get(clave, EntregaCamioneta)
        return clase_estrategia()

    @classmethod
    def registrar(cls, nombre: str, clase_estrategia: Type[MedioDeEntrega]):
        """
        Registra una nueva estrategia de transporte (principio Abierto/Cerrado).
        Permite añadir nuevos medios (ej. triciclo) sin modificar el código interno de la fábrica.
        """
        cls._MEDIOS[nombre.strip().lower()] = clase_estrategia

