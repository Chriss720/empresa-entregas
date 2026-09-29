from django.test import TestCase, Client
from django.urls import reverse
from .models import Pedido
from .services import PedidoService
from .strategies import (
    MedioDeEntrega,
    EntregaCamioneta,
    EntregaMotocicleta,
    EntregaBicicleta,
    EntregaDron,
    PlanEntrega
)
from .adapters import (
    Sugerencia,
    JsonIAAdapter,
    XmlIAAdapter,
    ProveedorIAJsonSimulado,
    ProveedorIAXmlSimulado,
    obtener_adaptador_ia
)
from .factories import FabricaMediosEntrega


class Dia3PatronesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    # =========================================================================
    # 1. Pruebas de Strategy (MedioDeEntrega.planear)
    # =========================================================================
    def test_estrategias_cumplen_contrato(self):
        """Verifica que los 4 medios implementen el contrato MedioDeEntrega.planear"""
        medios = [
            EntregaCamioneta(),
            EntregaMotocicleta(),
            EntregaBicicleta(),
            EntregaDron(),
        ]
        for medio in medios:
            self.assertIsInstance(medio, MedioDeEntrega)
            plan = medio.planear(contexto={"direccion": "Prueba 123"})
            self.assertIsInstance(plan, PlanEntrega)
            self.assertTrue(len(plan.tiempo_estimado) > 0)
            self.assertTrue(plan.costo > 0)
            self.assertTrue(len(plan.instrucciones_ruta) > 0)

    def test_estrategia_dron_valores_especificos(self):
        plan = EntregaDron().planear()
        self.assertEqual(plan.medio, "Dron")
        self.assertIn("10 a 15", plan.tiempo_estimado)
        self.assertIn("Corredor aéreo", plan.instrucciones_ruta)

    # =========================================================================
    # 2. Pruebas de Adapter (Homologación y Aislamiento de dialectos ajenos)
    # =========================================================================
    def test_json_adapter_aísla_route_hint_y_score(self):
        """
        Verifica que JsonIAAdapter traduzca el JSON a Sugerencia(medio, motivo).
        'route_hint' y 'score' no deben ser atributos de la Sugerencia.
        """
        adapter = JsonIAAdapter()
        sugerencia = adapter.obtener_sugerencia({"tipo_paquete": "urgente"})
        
        self.assertIsInstance(sugerencia, Sugerencia)
        self.assertEqual(sugerencia.medio, "dron")
        self.assertFalse(hasattr(sugerencia, "route_hint"), "route_hint no debe colarse en el dominio")
        self.assertFalse(hasattr(sugerencia, "score"), "score no debe colarse en el dominio")
        self.assertIn("sector_skyway_alpha_09", sugerencia.motivo)

    def test_xml_adapter_traduce_correctamente(self):
        """Verifica que XmlIAAdapter traduzca el XML legacy a Sugerencia(medio, motivo)"""
        adapter = XmlIAAdapter()
        sugerencia = adapter.obtener_sugerencia({"tipo_paquete": "ecologico"})
        
        self.assertIsInstance(sugerencia, Sugerencia)
        self.assertEqual(sugerencia.medio, "bicicleta")
        self.assertFalse(hasattr(sugerencia, "vehicle"), "Tags XML no deben existir en el dominio")
        self.assertIn("ciclovía", sugerencia.motivo)

    # =========================================================================
    # 3. Pruebas de Quién hace el new (Simple Factory)
    # =========================================================================
    def test_fabrica_simple_instancia_correctamente(self):
        """Verifica que FabricaMediosEntrega devuelva la estrategia adecuada"""
        self.assertIsInstance(FabricaMediosEntrega.crear("dron"), EntregaDron)
        self.assertIsInstance(FabricaMediosEntrega.crear("motocicleta"), EntregaMotocicleta)
        self.assertIsInstance(FabricaMediosEntrega.crear("bicicleta"), EntregaBicicleta)
        self.assertIsInstance(FabricaMediosEntrega.crear("camioneta"), EntregaCamioneta)

    def test_fabrica_simple_fallback_ante_medio_desconocido(self):
        """Si llega un medio desconocido, no explota; aplica fallback a Camioneta"""
        medio = FabricaMediosEntrega.crear("cohete_espacial")
        self.assertIsInstance(medio, EntregaCamioneta)

    # =========================================================================
    # 4. Pruebas de Capa de Servicio y Orquestación
    # =========================================================================
    def test_servicio_orquesta_adapter_fabrica_strategy(self):
        """
        Verifica que registrar_pedido orqueste todo el flujo y persista el resultado
        con el medio correcto y sus planes generados.
        """
        pedido = PedidoService.registrar_pedido(
            direccion_destino="Av. Paseo de la Reforma #100",
            tipo_paquete="urgente",
            proveedor_ia="json"
        )
        self.assertIsNotNone(pedido.id)
        self.assertEqual(pedido.medio_transporte, "Dron")
        self.assertIn("10 a 15", pedido.eta_estimado)
        self.assertTrue(len(pedido.detalles_plan) > 0)
        self.assertEqual(pedido.estado, "REGISTRADO")

    def test_servicio_con_proveedor_xml(self):
        pedido = PedidoService.registrar_pedido(
            direccion_destino="Calle Madero #10, Centro Histórico",
            tipo_paquete="ecologico",
            proveedor_ia="xml"
        )
        self.assertEqual(pedido.medio_transporte, "Bicicleta")
        self.assertIn("IA Legacy XML", pedido.motivo_asignacion)

    # =========================================================================
    # 5. Pruebas de Vista Web (PRG) y Contrato Móvil (JSON)
    # =========================================================================
    def test_post_pedidos_prg_redireccion(self):
        """Flujo PRG en la vista web"""
        response = self.client.post(reverse('crear_pedido'), {
            'direccion_destino': 'Av. Central #50',
            'tipo_paquete': 'estandar',
            'proveedor_ia': 'json'
        })
        self.assertEqual(response.status_code, 302)
        pedido = Pedido.objects.latest('id')
        self.assertRedirects(response, reverse('detalle_pedido', args=[pedido.id]))

    def test_get_detalle_pedido_web(self):
        """Panel web renderiza seguimiento con datos sin ejecutar SQL en plantilla"""
        pedido = PedidoService.registrar_pedido("Calle Magnolia #20", "urgente")
        url = reverse('detalle_pedido', args=[pedido.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pedido.folio)
        self.assertContains(response, "Dron")
        self.assertContains(response, "10 a 15 minutos")

    def test_contrato_json_para_app_movil(self):
        """Contrato de la app móvil: GET /pedidos/<id>/json retorna JSON ligero y completo"""
        pedido = PedidoService.registrar_pedido("Blvd. Benito Juárez #300", "urgente")
        url = reverse('pedido_json', args=[pedido.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['folio'], pedido.folio)
        self.assertEqual(data['medio_transporte'], 'Dron')
        self.assertEqual(data['estado'], 'REGISTRADO')
        self.assertIn('10 a 15 minutos', data['eta_estimado'])
        self.assertIn('detalles_plan', data)


class Dia5ContratoMovilYDefensaTestCase(TestCase):
    """
    Pruebas unitarias para los objetivos del Día 5:
    1. El mismo folio servido en HTML (panel) y en JSON (GET /api/pedidos/<id>).
    2. Contrato mínimo JSON (folio, estado, eta) y recurso de agregación que evita 12 peticiones.
    3. Descarga directa de guía de envío (rechazo justificado a Event Sourcing y CQRS).
    4. Ensayo de extensibilidad del Triciclo sin reabrir la vista, el XML ni el trámite registrar.
    """

    def setUp(self):
        self.client = Client()

    def test_mismo_folio_en_panel_html_y_api_json(self):
        """El mismo folio se consulta como HTML en el panel y como JSON en la API móvil"""
        pedido = PedidoService.registrar_pedido("Av. Cuauhtémoc #50", "urgente")

        # 1. Consulta en Panel Web (HTML)
        url_html = reverse('detalle_pedido', args=[pedido.id])
        resp_html = self.client.get(url_html)
        self.assertEqual(resp_html.status_code, 200)
        self.assertContains(resp_html, pedido.folio)
        self.assertContains(resp_html, "Dron")

        # 2. Consulta en API Móvil (JSON vía /api/pedidos/<id>)
        url_api = reverse('api_pedido_json', args=[pedido.id])
        resp_api = self.client.get(url_api)
        self.assertEqual(resp_api.status_code, 200)
        self.assertEqual(resp_api['Content-Type'], 'application/json')
        data = resp_api.json()
        self.assertEqual(data['folio'], pedido.folio)
        self.assertEqual(data['estado'], pedido.estado)
        self.assertEqual(data['eta'], pedido.eta_estimado)

    def test_api_pedidos_json_minimo_y_recurso_agregacion(self):
        """GET /api/pedidos/<id> entrega el JSON mínimo y consolida datos para evitar 12 peticiones"""
        pedido = PedidoService.registrar_pedido("Calle Puebla #80", "estandar")
        url_api = reverse('api_pedido_json', args=[pedido.id])
        response = self.client.get(url_api)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Contrato mínimo explícito del Día 5:
        self.assertIn("folio", data)
        self.assertIn("estado", data)
        self.assertIn("eta", data)
        self.assertEqual(data["folio"], pedido.folio)
        self.assertEqual(data["estado"], "REGISTRADO")
        self.assertEqual(data["eta"], pedido.eta_estimado)

        # Campos consolidados en una sola llamada (evitan que la app móvil haga 12 requests):
        self.assertIn("medio_transporte", data)
        self.assertIn("motivo_asignacion", data)
        self.assertIn("detalles_plan", data)
        self.assertIn("direccion_destino", data)
        self.assertIn("fecha_creacion", data)

    def test_descargar_guia_directa_sin_event_sourcing(self):
        """Demuestra que generar una guía no requiere Event Sourcing, CQRS ni Redux (KISS/YAGNI)"""
        pedido = PedidoService.registrar_pedido("Calle Hidalgo #100", "urgente")
        url_guia = reverse('descargar_guia', args=[pedido.id])
        response = self.client.get(url_guia)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn(f'attachment; filename="guia_{pedido.folio}.txt"', response['Content-Disposition'])
        contenido = response.content.decode('utf-8')
        self.assertIn(pedido.folio, contenido)
        self.assertIn("GUIA DE ENVIO", contenido)
        self.assertIn(pedido.medio_transporte, contenido)

    def test_ensayo_triciclo_extensibilidad_sin_tocar_tramite(self):
        """
        Defensa del Día 5:
        'Si mañana hay triciclo, ¿cuántos archivos abrimos?'
        Demuestra que añadiendo la clase de estrategia y registrándola en la fábrica,
        el trámite registrar_pedido y las vistas siguen intactos sin abrirse.
        """
        class EntregaTriciclo(MedioDeEntrega):
            def planear(self, contexto=None):
                return PlanEntrega(
                    medio="Triciclo",
                    tiempo_estimado="25 a 35 minutos",
                    costo=30.0,
                    instrucciones_ruta="Ciclovías segundarias y andadores peatonales.",
                    detalles="Reparto sustentable de carga ligera en triciclo."
                )

        # 1. Se registra la nueva estrategia en la fábrica (Open/Closed Principle)
        FabricaMediosEntrega.registrar("triciclo", EntregaTriciclo)

        # 2. La fábrica crea el triciclo
        medio = FabricaMediosEntrega.crear("triciclo")
        self.assertIsInstance(medio, EntregaTriciclo)
        plan = medio.planear()
        self.assertEqual(plan.medio, "Triciclo")
        self.assertIn("25 a 35 minutos", plan.tiempo_estimado)

