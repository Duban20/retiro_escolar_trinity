from django.contrib import admin
from .models import Grado, Alumno, Retiro, Nivel

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_nivel', 'grado', 'activo')
    list_filter = ('grado__nivel', 'grado', 'activo')
    search_fields = ('nombre',)

    def get_nivel(self, obj):
        return obj.grado.nivel.nombre
    get_nivel.short_description = 'Nivel'

admin.site.register(Nivel)
admin.site.register(Grado)
admin.site.register(Retiro)
