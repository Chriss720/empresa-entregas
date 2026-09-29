# Entregable Día 5 — El Mismo Pedido en JSON y la Defensa

**Materia:** Tópicos Selectos de Tecnologías Web y Móvil  
**Caso:** Plataforma de Entregas  
**Objetivo:** Resolver el Inconveniente 5 (recurso de agregación JSON mínimo), justificar el rechazo a la sobreingeniería del Inconveniente 7 (guía sin Event Sourcing/CQRS) y preparar la defensa oral técnica («pregunta del triciclo»).

---

## 1. Inconveniente 5: El Panel y la App (Recurso de Agregación)

* **Problema (*Chatty API*):** La app móvil hacía 12 peticiones HTTP para pintar la pantalla de inicio (CRUD anémico), causando latencia innecesaria y consumo excesivo de datos.
* **Solución:** Recurso de agregación en `GET /api/pedidos/<id>` (alias `GET /pedidos/<id>/json`).
  * Reutiliza `PedidoService.obtener_pedido_por_id` sin duplicar consultas ni lógica de negocio.
  * Responde en una sola llamada el contrato mínimo requerido por el cliente móvil (`folio`, `estado`, `eta`):

```json
{
  "folio": "PED-0001-A8F2",
  "estado": "REGISTRADO",
  "eta": "10 a 15 minutos",
  "medio_transporte": "Dron",
  "direccion_destino": "Av. Insurgentes Sur #1200",
  "detalles_plan": "Vuelo autónomo punto a punto...",
  "fecha_creacion": "2026-09-28T21:40:00"
}
```

* **¿Por qué NO un BFF externo?:** Por principio **YAGNI** (*You Aren't Gonna Need It*). Para un monolito con un solo cliente móvil y un modelo de datos simple, montar un servicio BFF independiente (Node/Go) añade sobrecarga de despliegue y mantenimiento. La agregación directa en la vista de Django resuelve el problema en pocas líneas de código.

---


## 3. Ensayo de menos de Tres Minutos 

### Pregunta Clave: *«Si mañana hay triciclo, ¿cuántos archivos abrimos?»*

> **Respuesta: EXACTAMENTE 2 ARCHIVOS.**

1. **`entregas/strategies.py`:** Creamos la clase `EntregaTriciclo` implementando `MedioDeEntrega.planear(contexto)`.
2. **`entregas/factories.py`:** Registramos la nueva estrategia en el catálogo (`FabricaMediosEntrega.registrar('triciclo', EntregaTriciclo)`).

