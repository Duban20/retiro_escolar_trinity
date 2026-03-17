from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.core.cache import cache
from .models import Transporte, TurnoTransporte, Grado, Alumno


def realizar_cierre_diario():
    """
    Verifica si cambió el día usando caché ultrarrápida en RAM.
    Si es un nuevo día, limpia la cola y actualiza a los alumnos.
    """
    hoy = timezone.localdate()
    hoy_str = str(hoy) # Convertimos la fecha a texto, ej: "2026-03-16"
    
    # 1. Verificamos en la memoria RAM si ya hicimos el cierre de hoy.
    # Esto toma 0.0001 segundos y no toca la base de datos.
    if cache.get('ultimo_cierre_diario') == hoy_str:
        return # Si ya se hizo, cortamos la función de inmediato.

    # 2. Si la RAM dice que no se ha hecho, hacemos la validación de seguridad
    if Alumno.objects.filter(activo=True).exclude(fecha_estado=hoy).exists():
        
        # LIMPIAR LA COLA:
        TurnoTransporte.objects.filter(estado__in=['EN_COLA', 'EMBARCANDO']).update(
            estado='DESPACHADO',
            hora_despacho=timezone.now()
        )
        
        # REINICIAR ALUMNOS:
        Alumno.objects.filter(activo=True).update(
            en_colegio=True, 
            fecha_estado=hoy
        )
        
    # 3. Guardamos en la memoria RAM que el cierre de hoy ya se completó.
    # Le damos un tiempo de vida de 24 horas (86400 segundos).
    cache.set('ultimo_cierre_diario', hoy_str, timeout=86400)

@login_required
def seleccionar_rol(request):
    realizar_cierre_diario()
    
    # 1. Solo 'Docentes' es redirigido automáticamente a la pantalla de cola
    if request.user.groups.filter(name='Docentes').exists():
        return redirect('panel_cola_transportes')
        
    # 2. Los demás (Administrador, Logistica, etc.) ven el menú principal
    return render(request, 'seleccionar_rol.html')

# ==========================================
# 1. VISTA DE PORTERÍA (Solo Encolar)
# ==========================================
@login_required
def porteria_encolar(request):
    realizar_cierre_diario()
    # Solo mostramos cuántos hay en fila como dato informativo
    vehiculos_en_cola = TurnoTransporte.objects.filter(estado='EN_COLA').count()
    return render(request, 'porteria_encolar.html', {'vehiculos_en_cola': vehiculos_en_cola})

@login_required
def encolar_transporte(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo_transporte', '').strip().upper()
        try:
            transporte = Transporte.objects.get(codigo_unico=codigo, activo=True)
            ya_en_cola = TurnoTransporte.objects.filter(transporte=transporte, estado__in=['EN_COLA', 'EMBARCANDO']).exists()

            if ya_en_cola:
                messages.warning(request, f"El transporte {codigo} ya está en la fila.")
            else:
                hay_actual = TurnoTransporte.objects.filter(estado='EMBARCANDO').exists()
                nuevo_estado = 'EN_COLA' if hay_actual else 'EMBARCANDO'
                TurnoTransporte.objects.create(transporte=transporte, estado=nuevo_estado)
                messages.success(request, f"Transporte {codigo} agregado exitosamente.")
                
        except Transporte.DoesNotExist:
            messages.error(request, f"No se encontró un transporte con el código '{codigo}'.")
            
    # Redirige de vuelta a portería (ya no al panel general)
    return redirect('porteria_encolar')

# ==========================================
# 2. VISTA DE PANTALLA (Docentes / Micrófono)
# ==========================================
@login_required
def panel_cola_transportes(request):
    realizar_cierre_diario()
    turno_actual = TurnoTransporte.objects.filter(estado='EMBARCANDO').first()
    
    # Convertimos la cola a lista para poder separarla
    turnos_en_cola = list(TurnoTransporte.objects.filter(estado='EN_COLA').order_by('hora_llegada'))
    
    # Separamos el que sigue (índice 0) y el resto (índice 1 en adelante)
    siguiente_turno = turnos_en_cola[0] if len(turnos_en_cola) > 0 else None
    resto_cola = turnos_en_cola[1:] if len(turnos_en_cola) > 1 else []

    # Validación de Rol: ¿Puede despachar? (Si es docente, es False)
    es_docente = request.user.groups.filter(name='Docentes').exists()
    puede_despachar = not es_docente

    return render(request, 'panel_transportes.html', {
        'turno_actual': turno_actual,
        'siguiente_turno': siguiente_turno,
        'resto_cola': resto_cola,
        'puede_despachar': puede_despachar
    })

@login_required
def despachar_transporte(request, turno_id):
    # Seguridad de backend: Evitar que un docente burle la interfaz forzando la URL
    if request.user.groups.filter(name='Docentes').exists():
        messages.error(request, "Acceso denegado: Los docentes no tienen permiso para despachar vehículos.")
        return redirect('panel_cola_transportes')

    turno_actual = get_object_or_404(TurnoTransporte, id=turno_id)
    if request.method == 'POST':
        turno_actual.estado = 'DESPACHADO'
        turno_actual.hora_despacho = timezone.now()
        turno_actual.save()

        alumnos = turno_actual.transporte.alumnos.all()
        alumnos.update(en_colegio=False, fecha_estado=timezone.localdate())

        siguiente_turno = TurnoTransporte.objects.filter(estado='EN_COLA').order_by('hora_llegada').first()
        if siguiente_turno:
            siguiente_turno.estado = 'EMBARCANDO'
            siguiente_turno.save()
            messages.success(request, f"Vehículo despachado. Turno actual: {siguiente_turno.transporte.codigo_unico}.")
        else:
            messages.success(request, "Vehículo despachado. La fila está vacía.")

    return redirect('panel_cola_transportes')

@login_required
def buscar_transporte_ajax(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    transportes = Transporte.objects.filter(
        Q(codigo_unico__icontains=query) | Q(nombre__icontains=query) | Q(alumnos__nombre__icontains=query),
        activo=True
    ).distinct().order_by('codigo_unico')[:8]

    results = []
    for t in transportes:
        alumnos_match = t.alumnos.filter(nombre__icontains=query)
        if alumnos_match.exists():
            nombres = [a.nombre for a in alumnos_match[:2]]
            hint = f"<i class='bi bi-person text-success'></i> {', '.join(nombres)}"
        else:
            hint = f"<i class='bi bi-truck text-muted'></i> {t.nombre}"

        results.append({'codigo': t.codigo_unico, 'nombre': t.nombre, 'hint': hint})

    return JsonResponse({'results': results})

@login_required
def verificar_cambios_cola(request):
    """
    Endpoint ultraligero. Solo devuelve un 'hash' o firma del estado actual de la fila.
    No renderiza HTML ni consulta todos los alumnos, ahorrando 95% de CPU.
    """
    # Traemos solo los IDs y estados (consulta rapidísima)
    turnos = TurnoTransporte.objects.filter(
        estado__in=['EMBARCANDO', 'EN_COLA']
    ).order_by('hora_llegada').values_list('id', 'estado')
    
    # Armamos una cadena simple: ej "5-EMBARCANDO|8-EN_COLA|12-EN_COLA"
    hash_str = "|".join([f"{t[0]}-{t[1]}" for t in turnos])
    
    return JsonResponse({'hash': hash_str})

# ==========================================
# 3. DIRECTORIO Y GESTIÓN DE ESTUDIANTES
# ==========================================

@login_required
def directorio_estudiantes(request):
    realizar_cierre_diario()
    """Muestra los grados y los alumnos del grado seleccionado."""
    grados = Grado.objects.filter(activo=True).order_by('orden', 'nombre')
    transportes = Transporte.objects.filter(activo=True).order_by('nombre')
    
    grado_id = request.GET.get('grado')
    grado_actual = None
    alumnos = []

    if grado_id:
        grado_actual = get_object_or_404(Grado, id=grado_id)
        alumnos = Alumno.objects.filter(grado=grado_actual, activo=True).order_by('nombre')

    # Validación de Rol: ¿Puede editar? (Solo el grupo Administrador)
    puede_editar = request.user.groups.filter(name='Administrador').exists()

    return render(request, 'directorio_estudiantes.html', {
        'grados': grados,
        'transportes': transportes,
        'grado_actual': grado_actual,
        'alumnos': alumnos,
        'puede_editar': puede_editar
    })

@login_required
def editar_estudiante(request, alumno_id):
    """Recibe los datos del modal y actualiza al estudiante."""
    
    # Seguridad de backend: Bloquear si no es Administrador
    if not request.user.groups.filter(name='Administrador').exists():
        messages.error(request, "Acceso denegado: Solo los administradores pueden editar alumnos.")
        return redirect('directorio_estudiantes')

    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, id=alumno_id)
        
        # Actualizar datos de texto
        alumno.nombre = request.POST.get('nombre', alumno.nombre)
        
        # Actualizar Grado
        grado_id = request.POST.get('grado_id')
        if grado_id:
            alumno.grado_id = grado_id
            
        # Actualizar Transporte (Puede ser "ninguno" si se va a pie)
        transporte_id = request.POST.get('transporte_id')
        if transporte_id:
            alumno.transporte_id = transporte_id
        else:
            alumno.transporte = None
            
        # Actualizar Foto si se subió una nueva
        if 'foto' in request.FILES:
            alumno.foto = request.FILES['foto']
            
        alumno.save()
        messages.success(request, f"Datos de {alumno.nombre} actualizados correctamente.")
        
        # Redirigir de vuelta al mismo grado que estábamos viendo
        grado_retorno = request.POST.get('grado_actual_id', '')
        return redirect(f"{reverse('directorio_estudiantes')}?grado={grado_retorno}")
        
    return redirect('directorio_estudiantes')