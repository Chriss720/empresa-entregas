from django.test import TestCase, Client
from django.urls import reverse
from .models import Pedido
from .services import PedidoService

class PedidoDia2TestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_servicio_registrar_pedido(self):
        """Prueba de la capa de servicio (PedidoService)"""
        pedido = PedidoService.registrar_pedido("Calle Test #123")
        self.assertIsNotNone(pedido.id)
        self.assertTrue(pedido.folio.startswith("PED-"))
        self.assertEqual(pedido.estado, "REGISTRADO")

    def test_post_pedidos_prg_redireccion(self):
        """Prueba del patrón PRG (POST /pedidos -> 302 -> GET /pedidos/<id>)"""
        response = self.client.post(reverse('crear_pedido'), {'direccion_destino': 'Av. Central #50'})
        
        # 1. Verifica redirección 302
        self.assertEqual(response.status_code, 302)
        
        pedido = Pedido.objects.first()
        expected_url = reverse('detalle_pedido', args=[pedido.id])
        self.assertRedirects(response, expected_url)

    def test_get_pedidos_detalle_sin_duplicar(self):
        """Prueba que el GET de seguimiento muestre los datos y que F5 no duplique folios"""
        pedido = PedidoService.registrar_pedido("Av. Universidad #40")
        initial_count = Pedido.objects.count()

        url = reverse('detalle_pedido', args=[pedido.id])
        response = self.client.get(url)

        # 2. Verifica GET 200 OK y contexto listo
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pedido.folio)
        self.assertContains(response, "30 - 45 minutos")

        # Simular recarga (F5) enviando otro GET
        response_f5 = self.client.get(url)
        self.assertEqual(response_f5.status_code, 200)

        # 3. Verifica que la cantidad de pedidos en la BD no cambió
        self.assertEqual(Pedido.objects.count(), initial_count)
