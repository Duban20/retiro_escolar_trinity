from django.db import models
from django.db.models import Q
from django.utils import timezone


class Grado(models.Model):
    activo = models.BooleanField(default=True)
    nombre = models.CharField(max_length=50)
    orden = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre
    

class Transporte(models.Model):
    codigo_unico = models.CharField(max_length=20, unique=True, help_text="Ej: RUTA-01")
    nombre = models.CharField(max_length=100, help_text="Ej: Buseta Norte o Nombre del Conductor")
    conductor = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo_unico} - {self.nombre}"


class Alumno(models.Model):
    activo = models.BooleanField(default=True)
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    en_colegio = models.BooleanField(default=True)
    fecha_estado = models.DateField(default=timezone.localdate)
    transporte = models.ForeignKey(Transporte, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='alumnos')
    foto = models.ImageField(upload_to='alumnos_fotos/', null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    
class TurnoTransporte(models.Model):
    ESTADOS = [
        ('EN_COLA', 'En espera'),
        ('EMBARCANDO', 'Llamado / Abordando'),
        ('DESPACHADO', 'Ya se retiró'),
    ]

    transporte = models.ForeignKey(Transporte, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='EN_COLA')
    hora_llegada = models.DateTimeField(auto_now_add=True)
    hora_despacho = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Turno: {self.transporte.codigo_unico} - {self.estado}"
