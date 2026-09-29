# Entregable Día 4 — Plantilla limpia, transacción e IA caída

**Materia:** Tópicos Selectos de Tecnologías Web y Móvil  
**Caso:** Plataforma / Empresa de Entregas  
**Objetivo:** Resolver los inconvenientes 3, 4 y 6, aplicando resiliencia, control transaccional atómico y manteniendo la pureza de la vista.

---

## 1. El Conflicto de la Doble Petición (Inconveniente 4 y la Sobreingeniería)

**Escenario:** El usuario pulsa dos veces "Crear", o pulsa *F5* justo después de someter el formulario. 
**Propuesta inicial rechazada:** Implementar *Event Sourcing* para esto es un caso clásico de *Golden Hammer*. *Event Sourcing* es un patrón arquitectónico mayor que cambia todo el paradigma de persistencia (guardar eventos inmutables en lugar del estado actual); usarlo solo para evitar un doble cobro es una sobreingeniería excesiva.

**Nuestra Solución Arquitectónica (Web Estándar):**
1. **Flujo PRG (Post-Redirect-Get):** Ya se encuentra operando en `views.py`. Cuando el navegador envía el `POST /pedidos`, el servidor procesa el trámite y responde con un HTTP `302 Found` (Redirect) apuntando a `GET /pedidos/<id>`. Al recibir esto, el navegador cambia su estado interno. Si el usuario presiona *F5*, el navegador refrescará la petición `GET` (inofensiva), y no re-enviará el formulario `POST`.
2. **Idempotencia (Protección contra doble clic rápido):** Para evitar que un doble clic rápido en el front-end alcance a disparar dos `POST` concurrentes antes del redirect, la solución industrial estándar es la **Clave de Idempotencia**. 
   * Se genera un *Token UUID* único al renderizar el formulario y se incluye como un campo oculto (`<input type="hidden">`).
   * Al recibir la petición, la Capa de Servicio revisa una caché rápida (o la DB) para ver si ese Token ya fue procesado. Si llega una segunda petición con el mismo Token (el doble clic), se ignora el intento de cobro repetido y simplemente se devuelve el Folio ya generado, garantizando que el dinero del cliente esté seguro.

---

## 2. Plantilla Limpia y Libre de SQL (Inconveniente 3)

**Conflicto original:** La plantilla ejecutaba consultas SQL directas o provocaba *Lazy Loading* (Carga perezosa) del ORM, lo que generaba el problema *N+1* y acoplaba la vista al motor de base de datos.

**Solución aplicada (`seguimiento.html`):**
* La plantilla se comporta estrictamente como un **Template View** pasivo.
* Se agregó un recuadro visual (`.map-box`) simulando la renderización de un mapa y se destacó el **ETA** (Tiempo Estimado de Llegada).
* **Cero Consultas:** Absolutamente toda la información que pinta la plantilla (`folio`, `estado`, `detalles_plan`, etc.) viene pre-empaquetada en el diccionario `context` desde la Vista (Page Controller), la cual a su vez lo obtuvo de la Capa de Servicio (`PedidoService`). No hay una sola llamada a métodos del modelo dentro del HTML.

---

## 3. Transacción Atómica y el Problema del Observer (Inconveniente 4)

**Conflicto original:** Si el envío del correo de confirmación falla, el sistema aborta el registro del envío.

**Solución aplicada (`services.py`):**
Se implementó el patrón **Unit of Work** (Unidad de Trabajo) de forma implícita usando el manejador `transaction.atomic()` de Django.
* **El Cobro Simulado:** Se ejecuta **dentro** del bloque atómico. Si la pasarela de pagos simulada lanza una excepción (`ValueError`, `Timeout`), toda la transacción hace un *Rollback* de la base de datos de manera automática. No se guarda un pedido si no se cobró.
* **El Aviso (Notificación/Correo):** Enviar un correo electrónico es una operación de Entrada/Salida (I/O) lenta y propensa a fallos de red. Si se pusiera dentro de la transacción, una falla en el servidor SMTP desharía el pago y el registro en DB de forma injusta.
* **`transaction.on_commit()`:** Para evitar esto, utilizamos un *hook* post-transaccional. El código `transaction.on_commit(lambda: enviar_correo())` le indica al motor: *"Solo envía el correo una vez que estés 100% seguro de que los datos del pedido y el cobro ya están firmes y guardados en el disco duro (Commit exitoso)"*.
* **¿Por qué el patrón Observer no basta?** El patrón Observer (Eventos/Señales) solo sirve para desacoplar el código que envía el aviso del código que guarda, pero **no gestiona fronteras transaccionales**. Si emites una señal/evento normal antes del Commit, sigues acoplado al éxito de la transacción. El `on_commit` es el puente correcto entre la integridad relacional y la notificación externa.

---

## 4. IA Caída y Resiliencia del Sistema (Inconveniente 6)

**Conflicto original:** Cuando el proveedor del mapa o de la inteligencia artificial (IA) falla, el sistema colapsa dejando al usuario con una "rueda infinita" de carga.

**Solución aplicada (`adapters.py` y `services.py`):**
* **Inyección de la Falla:** Se diseñó el `TimeoutIAAdapter` (Proveedor C en el formulario) capaz de arrojar deliberadamente un `TimeoutError`, simulando una caída total del proveedor.
* **Degradación Elegante (Graceful Degradation):** El sistema central (`PedidoService.registrar_pedido`) no asume que la IA siempre estará disponible. Al invocar al Adaptador, se envuelve la llamada en un bloque defensivo `try-except`.
* Si se captura un `TimeoutError`, el sistema **no detiene el negocio**. Intercepta la falla, loguea la indisponibilidad y genera un plan de contingencia offline (Fallback): *"Asignar Camioneta por defecto"*.
* **El GET ya guardado:** Tal como lo requiere el enunciado, la consulta de seguimiento (`GET /pedidos/<id>`) no depende de llamar a la IA de nuevo. Como la ruta y el medio ya quedaron calculados y guardados en la tabla de la DB, la página carga instantáneamente, logrando una arquitectura resiliente y asíncrona respecto a fallos de terceros.
