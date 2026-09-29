# Entregable Día 2 — Pensar el primer corte y arrancar Django

**Materia:** Tópicos Selectos de Tecnologías Web y Móvil  
**Caso:** Plataforma / Empresa de Entregas  
**Objetivo:** Crear el proyecto Django, la app `entregas`, implementar el primer trámite (`POST /pedidos` -> PRG -> `GET /pedidos/<id>`), mantener la vista delgada (Page Controller) delegando en la Capa de Servicio (`PedidoService`), y garantizar cero SQL en la plantilla.

---

## 1. El Camino de `POST /pedidos` (Trazabilidad y Patrones)

A continuación se detalla el recorrido completo de la petición desde que el cliente pulsa "Enviar pedido" hasta que ve la pantalla de seguimiento:

```
[Cliente Browser] 
       │
       │  1. POST /pedidos (Form Data)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Django Core: WSGI Handler & Middleware Stack                           │
│ (SecurityMiddleware, SessionMiddleware, CsrfViewMiddleware, etc.)       │
└────────────────────────────────────────────────────────────────────────┘
       │  2. Procesa sesión y valida token CSRF
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Front Controller / Router: urls.py                                     │
│ path('pedidos', views.crear_pedido_view, name='crear_pedido')           │
└────────────────────────────────────────────────────────────────────────┘
       │  3. Enruta la petición a la vista
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Page Controller (Vista delgada): views.py -> crear_pedido_view()       │
│ Extrae datos del request y delega a la capa de servicio                │
└────────────────────────────────────────────────────────────────────────┘
       │  4. Invoca registrar_pedido(...)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Service Layer: services.py -> PedidoService.registrar_pedido()         │
│ Ejecuta la transacción de negocio (with transaction.atomic())          │
│ Instancia el Modelo Pedido, asigna Folio único, Estado y ETA ficticio   │
└────────────────────────────────────────────────────────────────────────┘
       │  5. Retorna el pedido creado / ID de folio
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PRG (Post-Redirect-Get): views.py                                      │
│ Retorna HttpResponseRedirect(reverse('detalle_pedido', args=[id]))     │
└────────────────────────────────────────────────────────────────────────┘
       │  6. HTTP 302 Redirect a /pedidos/<id>/
       ▼
[Cliente Browser] 
       │
       │  7. GET /pedidos/<id>/ (Petición limpia)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Page Controller: views.py -> detalle_pedido_view(request, pk)          │
│ Obtiene pedido listo de PedidoService y construye el context           │
└────────────────────────────────────────────────────────────────────────┘
       │  8. render(request, 'entregas/seguimiento.html', context)
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Template View: entregas/seguimiento.html                               │
│ Recibe el contexto empaquetado. CERO SQL ni lazy loading en el HTML.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Desglose paso a paso y distinción de patrones

| Componente | Archivo / Pieza Django | Patrón Asociado | ¿Instanciado por Django o escrito por nosotros? | Justificación / Marcaje |
| :--- | :--- | :--- | :--- | :--- |
| **Pila de Middleware** | `settings.py` (`MIDDLEWARE`) | Chain of Responsibility / Intercepting Filter | **Instanciado por Django** | Django ejecuta la cadena de middlewares de forma automática antes de tocar la vista. **No es una clase GoF que escribamos a mano.** |
| **Enrutador Central** | `empresa_entregas/urls.py` | Front Controller | **Instanciado por Django** | El enrutado global de Django es el Front Controller. Nosotros solo declaramos las tuplas `path(...)`. |
| **Vista de Alta** | `entregas/views.py` (`crear_pedido_view`) | Page Controller (Vista delgada) | **Escrito por nosotros** | Extrae la información del `POST` y llama al servicio. No contiene lógica de transportes ni decisiones de logística. |
| **Capa de Servicio** | `entregas/services.py` (`PedidoService`) | Service Layer | **Escrito por nosotros** | Encapsula el caso de uso `registrar_pedido(...)` y la transacción de base de datos. Independiente del marco web. |
| **Redirección HTTP** | `redirect('detalle_pedido', ...)` | PRG (Post-Redirect-Get) | **Patrón Web (Uso de utilidades Django)** | Envía una respuesta HTTP 302/303. Garantiza que si el usuario recarga la página ($F5$), no se duplica el folio ni la transacción. |
| **Vista de Seguimiento** | `entregas/views.py` (`detalle_pedido_view`) | Page Controller | **Escrito por nosotros** | Recupera los datos mediante el servicio y arma el diccionario `context` con variables ya calculadas (`folio`, `estado`, `eta_estimado`). |
| **Plantilla HTML** | `entregas/templates/entregas/seguimiento.html` | Template View | **Escrito por nosotros (sobre motor Django)** | Recibe el contexto y renderiza la interfaz. **Strictly NO SQL**: No realiza consultas ni invoca relaciones ORM no precargadas. |

---

## 3. Demostración de las Reglas Arquitectónicas Cumplidas

1. **PRG (Post-Redirect-Get):**
   - El cliente hace `POST /pedidos`. Se registra el pedido en `PedidoService` y la respuesta del servidor es inmediatamente un `302 Redirect` a `/pedidos/<id>/`. Recargar la página solo re-ejecuta el `GET` de consulta, haciendo imposible crear folios duplicados por F5.
2. **Page Controller Delgado:**
   - La vista no contiene `if medio == 'camioneta':`, ni interactúa directamente con SQL. Solamente invoca a `PedidoService.registrar_pedido(...)`.
3. **Cero SQL en la Plantilla:**
   - El contexto llega con los campos primitivos/objetos ya procesados (`folio`, `estado`, `eta_estimado`). La plantilla no realiza llamadas ORM ni consultas diferidas.
