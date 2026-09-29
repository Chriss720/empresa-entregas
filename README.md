# Plataforma de Envíos — La Empresa de Entregas

Aplicación web desarrollada en **Django** que resuelve la arquitectura y los inconvenientes de dominio planteados en el caso *La empresa de entregas*, aplicando patrones de software sin sobreingeniería (*YAGNI*, *KISS*).

---

## 1. Cómo Ejecutar el Proyecto

### Requisitos previos:
- Python 3.10+ (o superior)
- `pip` o `uv`

### Pasos de instalación y arranque:

```bash
# 1. Entrar al directorio del proyecto
cd empresa-entregas

# 2. Crear y activar entorno virtual
# En Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
# python3 -m venv .venv && source .venv/bin/activate

# 3. Instalar dependencias (Django)
pip install django

# 4. Aplicar migraciones de base de datos
python manage.py migrate

# 5. Ejecutar la suite completa de 15 pruebas unitarias
python manage.py test

# 6. Iniciar el servidor de desarrollo local
python manage.py runserver
```

El panel web estará disponible en: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (redirige automáticamente a `/pedidos`).

---

## 2. Qué Patrones ya Traía Django (y NO Reescribimos)

Siguiendo el principio de **no reinventar la rueda**, el proyecto aprovecha las piezas que el marco de trabajo ya provee de forma nativa:

1. **Front Controller (`django.core.handlers` + `empresa_entregas/urls.py`):**
   Django cuenta con un despachador central que recibe todas las peticiones HTTP entrantes, resuelve la ruta mediante expresiones de URL declarativas y delega el flujo a los controladores específicos (`views.py`). No tuvimos que programar un enrutador manual ni servlets despachadores.
2. **Intercepting Filter / Middleware (`settings.py:MIDDLEWARE`):**
   La verificación de sesiones, la protección CSRF contra falsificación de peticiones y las políticas de seguridad se procesan a través de la tubería de middlewares antes de que la petición toque una sola línea de la vista. Esto resolvió el **Inconveniente 1** sin tener que copiar encabezados o validaciones en 40 archivos sueltos.
3. **Template View (`Django Templates`):**
   El motor de plantillas separa estrictamente la capa de presentación de la capa de datos. Las plantillas HTML (`formulario_pedido.html`, `seguimiento.html`) son componentes visuales pasivos: consumen variables precalculadas provistas en el diccionario `context` y **tienen cero consultas SQL o lógica de negocio incrustada**, eliminando el problema N+1 y resolviendo el **Inconveniente 3**.
4. **Unit of Work Implícito (`django.db.transaction.atomic()`):**
   Django gestiona las fronteras transaccionales a nivel de conexión relacional. Usamos `transaction.atomic()` para garantizar que el cobro simulado y el alta del pedido se confirmen juntos o hagan rollback completo ante cualquier error, postergando los avisos externos hasta después del guardado mediante `transaction.on_commit()`. No tuvimos que escribir un gestor de objetos modificados en memoria.

---

## 3. Mapeo de Archivos: Dónde Viven los Patrones y el Trámite

El código de diseño desacoplado se organiza estrictamente por responsabilidades:

| Rol Arquitectónico / Patrón | Archivo en el Repositorio | Responsabilidad Concreta |
| :--- | :--- | :--- |
| **Adapter (Adaptador)** | [`entregas/adapters.py`](entregas/adapters.py) | Aísla y traduce las respuestas externas de IA (JSON con `route_hint`/`score`, XML legacy con `<vehicle>` y simulador de timeout) al contrato de dominio unificado: `Sugerencia(medio, motivo)`. El dialecto ajeno **muere aquí** y jamás contamina las vistas ni el modelo. |
| **Strategy (Estrategia)** | [`entregas/strategies.py`](entregas/strategies.py) | Define la interfaz común `MedioDeEntrega` y sus estrategias logísticas concretas: `EntregaCamioneta`, `EntregaMotocicleta`, `EntregaBicicleta`, `EntregaDron` (y extensible a `EntregaTriciclo`). Cada una calcula sus propios tiempos, rutas y costos mediante `planear(contexto) -> PlanEntrega`. |
| **Simple Factory (Fábrica Simple)** | [`entregas/factories.py`](entregas/factories.py) | Resuelve **quién hace el `new`** (`FabricaMediosEntrega.crear(medio)`), asociando el string de la sugerencia con la clase de estrategia adecuada. Incluye método `registrar()` para incorporar nuevos transportes dinámicamente sin tocar código cliente. |
| **El Trámite (Service Layer)** | [`entregas/services.py`](entregas/services.py) | Clase `PedidoService.registrar_pedido`: Encapsula el caso de uso principal dentro de una transacción atómica. Orquesta la secuencia: `Adapter -> Simple Factory -> Strategy -> Persistencia -> Hook de Notificación`. |
| **Page Controller (Vistas Delgadas)** | [`entregas/views.py`](entregas/views.py) | Controladores delgados que atienden las peticiones web y móviles (`crear_pedido_view`, `detalle_pedido_view`, `pedido_json_view`, `descargar_guia_view`). Aplican el patrón Post-Redirect-Get (PRG) y delegan toda la lógica a la capa de servicio. |

---

## 4. Qué se Rechazó: El Inconveniente 7 y Saber Decir que NO

El punto 7 del caso describe la propuesta de un proveedor externo:
> *«Un proveedor propone Event Sourcing, CQRS y Redux global para generar un PDF de guía. El trámite real es: autenticar, consultar un pedido existente y generar un archivo. Eso no es madurez: es ceremonia. Parte del semestre es saber decir que no.»*

### Justificación Técnica del Rechazo:
1. **Antipatrón *Golden Hammer*:** Event Sourcing y CQRS son herramientas diseñadas para dominios altamente distribuidos o sistemas financieros con auditoría forense inmutable de eventos. Usarlos para emitir una guía de despacho representa una **sobreingeniería injustificada**.
2. **Complejidad y Fragilidad Operativa:** Implementar Event Sourcing habría requerido levantar un *Event Store*, definir esquemas de eventos inmutables (`PedidoCreado`, `GuiaGenerada`), coordinar proyecciones asíncronas con consistencia eventual y configurar Redux en el cliente web.
3. **Nuestra Solución (KISS / YAGNI):**  
   Implementamos la vista directa `descargar_guia_view` en [`entregas/views.py`](entregas/views.py) (`GET /pedidos/<id>/guia`), la cual consulta el registro existente en la base de datos y responde de manera inmediata (< 5 ms) mediante un `HttpResponse` con cabecera `Content-Disposition`.  
   **Saber decir que no a la ceremonia innecesaria es una de las habilidades centrales de un arquitecto de software.**

---

## 5. Mapa de Conflictos del Caso y Solución Arquitectónica

| # | Conflicto / Inconveniente del Enunciado | Patrón o Solución Aplicada | Pieza en el Código | Justificación Arquitectónica |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Código repetido en trámites y revisión manual de sesiones.** | **Front Controller + Intercepting Filter / Middleware** | Django Core (`urls.py` + `settings.py:MIDDLEWARE`) | Despacho centralizado y pila transversal de seguridad y sesiones antes de la vista. |
| **2** | **Switch gigante de transportes y formatos incompatibles de IA.** | **Strategy + Adapter + Simple Factory** | `strategies.py`, `adapters.py`, `factories.py` | • **Strategy:** 4 medios polimórficos bajo `planear()`.<br>• **Adapter:** homologa JSON (`route_hint`) y XML a `Sugerencia`.<br>• **Simple Factory:** concentra el `new` sin jerarquías abstractas vacías. |
| **3** | **La plantilla ejecuta SQL y la vista conoce la bodega.** | **Template View + Service Layer** | `templates/entregas/` y `services.py` | Plantilla pasiva libre de SQL; datos pre-empaquetados en el `context`. |
| **4** | **Cobros dobles por recargar y transacciones rotas.** | **Post-Redirect-Get (PRG) + Unit of Work** | `views.py` (`redirect`) y `services.py` (`transaction.atomic`) | `POST /pedidos` redirige con HTTP 302 a `GET /pedidos/<id>`. Avisos con `transaction.on_commit`. |
| **5** | **Clientes web y móvil con contratos diferentes.** | **Recurso de Agregación JSON** | `views.py` (`pedido_json_view` en `/api/pedidos/<id>`) | Mismo servicio y modelo expone contrato mínimo (`folio, estado, eta`) en 1 sola llamada, evitando 12 peticiones. |
| **6** | **Caídas de la IA congelan el sistema.** | **Tolerancia a Fallos + Degradación Elegante** | `services.py` (`try-except TimeoutError`) | Si la IA cae, se captura el error y se asigna un fallback seguro sin colapsar el alta ni las consultas locales. |
| **7** | **Propuesta de sobreingeniería para generar guía.** | **Rechazo de Event Sourcing / Vista Directa** | `views.py` (`descargar_guia_view`) | Rechazo formal a CQRS/Redux. Generación y descarga directa del documento en 5 líneas de código. |

---

## 6. Ensayo de Tres Minutos para la Defensa Oral

> **Pregunta Clave:** *«Si mañana hay triciclo eléctrico, ¿cuántos archivos abrimos?»*

### Respuesta Técnica:
**Abrimos exactamente DOS archivos (o UNO si el registro es por reflexión/decorador):**
1. **`entregas/strategies.py`:** Escribimos la nueva clase `EntregaTriciclo(MedioDeEntrega)` con su lógica de cálculo en `planear()`.
2. **`entregas/factories.py`:** Registramos la nueva estrategia: `FabricaMediosEntrega.registrar("triciclo", EntregaTriciclo)`.

### ¿Qué archivos quedan blindados y NO se tocan?
* **NO abrimos la vista (`views.py`):** Sigue delgada e ignora qué transportes existen.
* **NO abrimos los adaptadores (`adapters.py`):** La IA sigue devolviendo su string y el adaptador lo entrega intacto en `Sugerencia.medio`.
* **NO abrimos el trámite (`PedidoService.registrar_pedido` en `services.py`):** El flujo es polimórfico y está cerrado a modificación (Principio Abierto/Cerrado).
* **NO abrimos las plantillas HTML ni modificamos la base de datos.**

> **Diagnóstico:** Si la respuesta de un equipo fuera *"hay que abrir la vista, el XML y el método registrar"*, significa que no implementaron Strategy ni Adapter: dejaron un `switch` de 200 líneas acoplado en el controlador y el dialecto de la IA contaminó el trámite de negocio.

---

## 7. Endpoints Disponibles en la Plataforma

- **`GET /`**: Redirección automática a `/pedidos`.
- **`GET /pedidos`**: Formulario web para dar de alta pedidos (permite probar proveedor JSON, XML y simulación de IA caída).
- **`POST /pedidos`**: Trámite de alta delegando a `PedidoService.registrar_pedido` con respuesta HTTP 302 (PRG).
- **`GET /pedidos/<id>`**: Panel web de seguimiento con mapa simulado, ETA, badge de transporte y plan operativo.
- **`GET /api/pedidos/<id>`** (o `/pedidos/<id>/json`): Contrato API móvil con JSON mínimo (`folio`, `estado`, `eta`) y datos agregados.
- **`GET /pedidos/<id>/guia`**: Descarga directa de la guía de envío oficial sin sobreingeniería.

---

## 8. Documentos Entregables por Día

Cada etapa del desarrollo cuenta con su correspondiente documento de justificación técnica y análisis arquitectónico:
- **Día 1:** [`entregable_dia_1.md`](entregable_dia_1.md) — Tabla comparativa Enunciado vs. Framework vs. Patrones de libro; Front Controller y análisis de consultas SQL en plantillas.
- **Día 2:** [`entregable_dia_2.md`](entregable_dia_2.md) — Diagrama del camino de `POST /pedidos`, patrón PRG, Service Layer y separación de capas.
- **Día 3:** [`entregable_dia_3.md`](entregable_dia_3.md) — Strategy (`MedioDeEntrega`), Adapter (aislamiento de `route_hint` y formatos externos), Fábrica Simple vs. Factory Method, y orquestación en la capa de servicio.
- **Día 4:** [`entregable_dia_4.md`](entregable_dia_4.md) — Plantilla limpia, transacciones atómicas (`Unit of Work`), aviso post-commit (`on_commit` vs. Observer) y resiliencia ante IA caída.
- **Día 5:** [`entregable_dia_5.md`](entregable_dia_5.md) — El mismo pedido en JSON (`GET /api/pedidos/<id>`), recurso de agregación frente a las 12 peticiones, rechazo al Event Sourcing del Inconveniente 7 y guion de defensa de 3 minutos.
