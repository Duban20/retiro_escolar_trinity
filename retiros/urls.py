from django.urls import path
from . import views

urlpatterns = [
    # Inicio / Selección de rol
    path('', views.seleccionar_rol, name='seleccionar_rol'),

    # 1. Portería (Solo encolar)
    path('porteria/', views.porteria_encolar, name='porteria_encolar'),
    
    # 2. Pantalla General (Docentes, Micrófono, Entregas)
    path('pantalla/', views.panel_cola_transportes, name='panel_cola_transportes'),

    # 3. Acciones lógicas (Endpoints)
    path('transportes/encolar/', views.encolar_transporte, name='encolar_transporte'),
    path('transportes/despachar/<int:turno_id>/', views.despachar_transporte, name='despachar_transporte'),
    path('transportes/buscar-ajax/', views.buscar_transporte_ajax, name='buscar_transporte_ajax'),
    path('transportes/verificar-cola/', views.verificar_cambios_cola, name='verificar_cambios_cola'),

    # 4. Directorio Escolar
    path('directorio/', views.directorio_estudiantes, name='directorio_estudiantes'),
    path('directorio/editar/<int:alumno_id>/', views.editar_estudiante, name='editar_estudiante'),
]