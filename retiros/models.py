from django.db import models
from django.db.models import Q
from django.utils import timezone


class Nivel(models.Model):
    activo = models.BooleanField(default=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    

class Grado(models.Model):
    activo = models.BooleanField(default=True)
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    orden = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class Alumno(models.Model):
    activo = models.BooleanField(default=True)
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    en_colegio = models.BooleanField(default=True)
    fecha_estado = models.DateField(default=timezone.localdate)

    def __str__(self):
        return self.nombre


class Retiro(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ENTREGADO', 'Entregado'),
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    hora_aviso = models.DateTimeField(auto_now_add=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['alumno'],
                condition=Q(estado='PENDIENTE'),
                name='unique_pendiente_por_alumno'
            )
        ]

    def __str__(self):
        return f"{self.alumno.nombre} - {self.estado}"
