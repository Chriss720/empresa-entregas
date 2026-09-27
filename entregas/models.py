from django.db import models

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('REGISTRADO', 'Registrado'),
        ('EN_CAMINO', 'En camino'),
        ('ENTREGADO', 'Entregado'),
    ]

    folio = models.CharField(max_length=50, unique=True, editable=False)
    direccion_destino = models.CharField(max_length=255, default='Dirección por defecto')
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='REGISTRADO')
    eta_estimado = models.CharField(max_length=50, default='45 minutos (estimado)')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.folio} - {self.estado}"
