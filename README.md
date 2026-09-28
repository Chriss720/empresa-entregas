# Plataforma de Envíos — La Empresa de Entregas

Aplicación web desarrollada en **Django** que resuelve la arquitectura y los inconvenientes de dominio planteados en el caso *La empresa de entregas*, aplicando patrones de software sin sobreingeniería (*YAGNI*).

---

## 1. Cómo Ejecutar el Proyecto

### Requisitos previos:
- Python 3.10+ (o superior)
- `uv` o `pip`

### Pasos de instalación y arranque:

```bash
# 1. Clonar el repositorio y entrar al directorio
cd empresa-entregas

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Linux/macOS
# o con uv: uv venv .venv && source .venv/bin/activate

# 3. Instalar dependencias (Django)
pip install django
# o con uv: uv pip install django

# 4. Aplicar migraciones
python manage.py migrate

# 5. Ejecutar la suite de pruebas unitarias
python manage.py test

# 6. Iniciar el servidor local
python manage.py runserver
```

El panel web estará disponible en: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (redirige a `/pedidos`).

---

## 2. Mapa de Conflictos del Caso y Patrón Asociado

| # | Conflicto / Inconveniente del Enunciado | Patrón de Diseño Aplicado | Pieza en el Código | Justificación Arquitectónica |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Código repetido en trámites y revisión manual de sesiones.** | **Front Controller + Intercepting Filter / Middleware** | Django Core (`urls.py` + `settings.py:MIDDLEWARE`) | El Front Controller centraliza el despacho y los middlewares procesan sesiones y seguridad de forma transversal antes de llegar a la vista. |
| **2** | **Switch gigante de transportes y formatos incompatibles de IA.** | **Strategy + Adapter + Simple Factory** | `entregas/strategies.py`, `entregas/adapters.py`, `entregas/factories.py` | • **Strategy:** 4 medios (`Camioneta`, `Motocicleta`, `Bicicleta`, `Dron`) bajo `planear()`.<br>• **Adapter:** homologa JSON (`route_hint`, `score`) y XML a `Sugerencia(medio, motivo)`.<br>• **Simple Factory:** centraliza la instanciación sin inventar familias abstractas. |
| **3** | **La plantilla ejecuta SQL y la vista conoce la bodega.** | **Template View + Service Layer** | `entregas/templates/` y `entregas/services.py` | La plantilla solo pinta variables procesadas del contexto. Cero SQL en el HTML. |
| **4** | **Cobros dobles por recargar y transacciones rotas.** | **Post-Redirect-Get (PRG) + Unit of Work** | `views.py` (`redirect`) y `services.py` (`transaction.atomic`) | `POST` redirige a `GET /pedidos/<id>`, haciendo imposible duplicar órdenes con F5. |
| **5** | **Clientes web y móvil con contratos diferentes.** | **Single Backend Service + Agregación JSON** | `entregas/views.py` (`pedido_json_view`) | Mismo servicio atiende panel HTML y expone `GET /pedidos/<id>/json` para la app móvil en una sola petición. |

---

## 3. Endpoints Disponibles

- **`GET /pedidos`**: Formulario web para dar de alta pedidos (permite seleccionar tipo de paquete y proveedor de optimización externa).
- **`POST /pedidos`**: Trámite de alta delegando a `PedidoService.registrar_pedido` y respondiendo con redirección HTTP 302 (PRG).
- **`GET /pedidos/<id>`**: Panel web de seguimiento que muestra el folio, estado, medio asignado, motivo de la IA y plan operativo.
- **`GET /pedidos/<id>/json`** o **`GET /api/pedidos/<id>`**: Contrato JSON para la app móvil (consume el mismo modelo y servicio).

---

## 4. Notas y Entregables por Día

Las justificaciones conceptuales detalladas de cada sesión se encuentran en:
- **Día 1:** [`entregable_dia_1.md`](entregable_dia_1.md) — Tabla comparativa Enunciado vs. Framework vs. Patrones de libro; Front Controller y análisis de SELECT en plantillas.
- **Día 2:** [`entregable_dia_2.md`](entregable_dia_2.md) — Diagrama del camino de `POST /pedidos`, patrón PRG, Service Layer y separación de capas.
- **Día 3:** [`entregable_dia_3.md`](entregable_dia_3.md) — Strategy (`MedioDeEntrega`), Adapter (aislamiento de `route_hint` y formatos externos), Fábrica Simple vs. Factory Method, y orquestación en la capa de servicio.
