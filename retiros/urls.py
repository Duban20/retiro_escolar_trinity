from django.urls import path
from . import views

urlpatterns = [
    # Selección de rol
    path('', views.seleccionar_rol, name='seleccionar_rol'),

    # Portería
    path('porteria/', views.seleccionar_nivel, name='seleccionar_nivel'),
    path('nivel/<int:nivel_id>/', views.lista_grados, name='lista_grados'),
    path('grado/<int:grado_id>/', views.lista_alumnos, name='lista_alumnos'),
    path('retiro/<int:alumno_id>/', views.crear_retiro, name='crear_retiro'),
    path('retiros/masivos/', views.crear_retiros_masivos, name='crear_retiros_masivos'),

    # Docente
    path('docente/', views.docente_seleccionar_grado, name='docente_seleccionar_grado'),
    path('docente/<int:grado_id>/', views.docente_pendientes, name='docente_pendientes'),
    path('docente/<int:grado_id>/cantidad/', views.cantidad_pendientes, name='cantidad_pendientes'),
    path('docente/<int:grado_id>/lista/', views.lista_pendientes_json, name='lista_pendientes_json'),

    # Entregar
    path('entregar/<int:retiro_id>/', views.marcar_entregado, name='marcar_entregado'),
]
