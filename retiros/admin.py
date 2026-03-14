from django.contrib import admin
from .models import Alumno, Transporte, TurnoTransporte


@admin.register(Transporte)
class TransporteAdmin(admin.ModelAdmin):
    list_display = ('codigo_unico', 'nombre', 'conductor', 'activo')
    search_fields = ('codigo_unico', 'nombre', 'conductor')
    list_filter = ('activo',)

@admin.register(TurnoTransporte)
class TurnoTransporteAdmin(admin.ModelAdmin):
    list_display = ('transporte', 'estado', 'hora_llegada', 'hora_despacho')
    list_filter = ('estado', 'hora_llegada')

# Si no tenías registrado el Alumno, o quieres mejorarlo para que muestre su transporte:
@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grado', 'transporte', 'en_colegio')
    list_filter = ('grado', 'en_colegio', 'transporte')
    search_fields = ('nombre',)
