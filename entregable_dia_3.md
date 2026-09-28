# Entregable Día 3 — Strategy, Adapter y Quién Hace el New

**Materia:** Tópicos Selectos de Tecnologías Web y Móvil  
**Caso:** Plataforma / Empresa de Entregas  
**Objetivo:** Resolver el **Inconveniente 2** del enunciado (switch gigante de transportes y formatos incompatibles de IA) aplicando **Strategy**, **Adapter** y **Simple Factory**, orquestados limpiamente desde la Capa de Servicio (`PedidoService`) manteniendo la vista delgada e ignorante de las clases concretas y del vocabulario externo.

---

## 1. Una Frase por Patrón: Inconveniente y Qué Vecino NO Es

| Patrón | Inconveniente que resuelve | Qué vecino cercano NO es y por qué |
| :--- | :--- | :--- |
| **Strategy (`MedioDeEntrega`)** | Resuelve el `switch` gigante de transportes y la rigidez de cálculo de rutas y costos, encapsulando cada medio (`Camioneta`, `Motocicleta`, `Bicicleta`, `Dron`) bajo un contrato polimórfico uniforme `planear(pedido, contexto)`. | **No es *State* ni *Template Method*:** No es *State* porque el medio de entrega no representa estados transicionales de un ciclo de vida que cambian solos en tiempo de ejecución; y no es *Template Method* porque no buscamos heredar un esqueleto de algoritmo con ganchos protegidos fijos, sino intercambiar algoritmos de planificación logística independientes y desacoplados. |
| **Adapter (`JsonIAAdapter`, `XmlIAAdapter`)** | Resuelve la incompatibilidad de lenguajes externos (JSON con `route_hint`/`score` o XML con `<vehicle>`), traduciéndolos al único concepto que el dominio entiende: `Sugerencia(medio, motivo)`. | **No es *Facade* ni *Decorator*:** No es *Facade* porque su meta no es simplificar una interfaz compleja de muchas clases a una sencilla, sino convertir una interfaz existente incompatible a la esperada; y no es *Decorator* porque no agrega responsabilidades o comportamientos adicionales al servicio externo, solo traduce su dialecto. |
| **Fábrica Simple (`FabricaMediosEntrega`)** | Resuelve la responsabilidad de "quién hace el `new`", centralizando la instanciación de la estrategia concreta (`EntregaDron`, `EntregaCamioneta`, etc.) a partir del string normalizado de la sugerencia sin acoplar la vista ni la capa de servicio al constructor directo. | **No es *Factory Method* ni *Abstract Factory*:** No es *Factory Method* porque no existe una jerarquía paralela de creadores/subclases que sobreescriban un método gancho de fabricación; no lo montamos para disfrazar un despacho simple. Y no es *Abstract Factory* porque no creamos familias de objetos dependientes entre sí (como suites de UI o familias de transportes + refacciones). |

---

## 2. Justificación: ¿Por qué Fábrica Simple y NO Factory Method?

El enunciado advierte expresamente:  
> *«Factory Method (`LogisticaAerea.crearMedio`) solo si tienen familias de trámite que redefinen el gancho; no lo monten para disfrazar el switch.»*

En nuestro sistema:
1. **No hay familias de trámites creadores:** Todos los pedidos ingresan mediante el mismo caso de uso (`registrar_pedido`). No tenemos un `TramiteAereo` heredando de un `TramiteBase` con polimorfismo en el método creador.
2. **Evitar la sobreingeniería (YAGNI):** Introducir clases abstractas creadoras (`CreadorLogistica`, `CreadorAereo`, `CreadorTerrestre`) cuando el input es simplemente un string que viene de una sugerencia (`"dron"`, `"camioneta"`) solo inflaría el código con clases vacías que únicamente hacen `return EntregaDron()`.
3. **Abierto a Extensión mediante Registro (OCP):** La clase `FabricaMediosEntrega` utiliza un diccionario de registro `_MEDIOS: dict[str, Type[MedioDeEntrega]]`. Agregar un nuevo transporte (p. ej. `barco` o `patineta`) requiere registrar la nueva clase en el catálogo sin alterar el contrato del cliente ni fabricar una jerarquía paralela de fábricas.

---

## 3. Demostración de Aislamiento: El dialecto externo no entra al Dominio

La regla de oro del Día 3 establece:
> *«Si `route_hint` aparece en la vista o en el `planear`, el idioma ajeno se coló.»*

### Recorrido y Encapsulamiento del Dialecto:
1. **Proveedor Externo Simulado (JSON):**
   Devuelve un payload técnico propietario:
   ```json
   {
     "route_hint": "sector_skyway_alpha_09",
     "score": 0.98,
     "selected_transport": "dron",
     "reasoning": "Paquete ultraligero y ventana de entrega urgente."
   }
   ```
2. **Frontera de Traducción (`JsonIAAdapter`):**
   - Consume el JSON.
   - Extrae internamente `route_hint` y `score`.
   - Construye el objeto de dominio limpio:
     ```python
     Sugerencia(
         medio="dron",
         motivo="IA JSON (Confianza: 98%, Corredor: sector_skyway_alpha_09): Paquete ultraligero..."
     )
     ```
3. **Dominio, Servicio y Vista:**
   - `Sugerencia` solo expone `medio` y `motivo`.
   - `MedioDeEntrega.planear(contexto)` recibe únicamente el contexto del pedido; **jamás recibe ni conoce `route_hint`**.
   - La vista (`views.py`) solo manipula el modelo `Pedido` y llama a `PedidoService.registrar_pedido(...)`.

---

## 4. Orquestación del Trámite en `PedidoService.registrar_pedido`

El camino del trámite dentro del método atómico de servicio:

```
[Request POST] 
       │ (direccion, tipo_paquete, proveedor_ia)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ views.py -> crear_pedido_view (Page Controller Delgado)                │
│ Solo pasa los parámetros limpios al servicio. Cero lógica de medios.   │
└────────────────────────────────────────────────────────────────────────┘
       │  invoca PedidoService.registrar_pedido(...)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PedidoService.registrar_pedido (Service Layer)                         │
│                                                                        │
│  [1. ADAPTER]                                                         │
│  adaptador = obtener_adaptador_ia(proveedor_ia)                        │
│  sugerencia = adaptador.obtener_sugerencia(contexto_ia)               │
│  --> Retorna Sugerencia(medio="dron", motivo="...")                   │
│                                                                        │
│  [2. FÁBRICA SIMPLE]                                                   │
│  medio_entrega = FabricaMediosEntrega.crear(sugerencia.medio)          │
│  --> Retorna instancia concreta: EntregaDron()                         │
│                                                                        │
│  [3. STRATEGY]                                                         │
│  plan = medio_entrega.planear(contexto=contexto_estrategia)            │
│  --> Retorna PlanEntrega(tiempo_estimado, costo, ruta, detalles)       │
│                                                                        │
│  [4. PERSISTENCIA ATÓMICA (ORM)]                                       │
│  Pedido.objects.create(..., medio_transporte=plan.medio, ...)          │
└────────────────────────────────────────────────────────────────────────┘
       │ Retorna pedido creado
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ views.py: PRG -> redirect('detalle_pedido', pedido_id=pedido.id)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Alcance Web y Móvil (Contrato JSON)

Cumpliendo con la especificación de los 5 días:
- **Panel Web (`GET /pedidos/<id>`):** Renderiza la vista `Template View` sin consultas en plantilla, mostrando el badge del medio asignado (🚁 Dron, 🚲 Bicicleta, 🛵 Motocicleta, 🚚 Camioneta), el motivo formulado por el adaptador y las especificaciones operativas del plan.
- **Contrato Móvil (`GET /pedidos/<id>/json` o `GET /api/pedidos/<id>`):**
  Retorna el recurso en una sola llamada para el cliente móvil:
  ```json
  {
    "folio": "PED-0001-A1B2",
    "direccion_destino": "Av. Insurgentes Sur #1230, CDMX",
    "estado": "REGISTRADO",
    "medio_transporte": "Dron",
    "motivo_asignacion": "IA JSON (Confianza: 98%, Corredor: sector_skyway_alpha_09): Paquete ultraligero y ventana de entrega urgente. Ruta aérea recomendada sin tráfico.",
    "eta_estimado": "10 a 15 minutos",
    "detalles_plan": "Vuelo autónomo punto a punto esquivando tráfico terrestre y semáforos. | Ruta: Corredor aéreo automatizado a 120m AGL. Vector directo punto a punto. | Costo: $95.00",
    "fecha_creacion": "2026-09-28T12:35:00"
  }
  ```

---

## 6. Verificación de Pruebas Automatizadas

Se crearon y ejecutaron 11 pruebas unitarias en `entregas/tests.py`:
- **Strategy:** Verificación del contrato `MedioDeEntrega.planear` para las 4 clases concretas.
- **Adapter:** Verificación de aislamiento estricto (comprobando con `hasattr` que ni `route_hint` ni `score` forman parte de la clase `Sugerencia`).
- **Fábrica Simple:** Pruebas de instanciación dinámica y fallback seguro ante medios inexistentes.
- **Service Layer:** Integración de la orquestación completa con proveedores JSON y XML.
- **PRG & API Móvil:** Comprobación del código HTTP 302 hacia GET y del contenido `application/json` para la app móvil.

**Resultado:**
```bash
Ran 11 tests in 0.087s
OK
```
