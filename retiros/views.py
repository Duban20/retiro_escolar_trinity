from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Nivel, Grado, Alumno, Retiro
from django.contrib import messages
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.http import JsonResponse


def reset_diario_alumnos():
    hoy = timezone.localdate()

    if not Alumno.objects.filter(fecha_estado=hoy).exists():
        Alumno.objects.update(
            en_colegio=True,
            fecha_estado=hoy
        )


@login_required
def seleccionar_rol(request):

    reset_diario_alumnos()   # reset automático

    return render(request, 'seleccionar_rol.html')

# ===============================
# SECCIÓN ENTRADA (Portería)
# ===============================

@login_required
def seleccionar_nivel(request):
    reset_diario_alumnos()
    niveles = Nivel.objects.filter(activo=True)
    return render(request, 'seleccionar_nivel.html', {'niveles': niveles})


@login_required
def lista_grados(request, nivel_id):
    nivel = get_object_or_404(Nivel, id=nivel_id)
    grados = Grado.objects.filter(nivel=nivel, activo=True).order_by('orden')

    return render(request, 'lista_grados.html', {
        'nivel': nivel,
        'grados': grados
    })


@login_required
def lista_alumnos(request, grado_id):
    grado = get_object_or_404(Grado, id=grado_id)
    nivel = grado.nivel

    retiro_pendiente = Retiro.objects.filter(
        alumno=OuterRef('pk'),
        estado='PENDIENTE'
    )

    alumnos = (
        Alumno.objects
        .filter(grado=grado, activo=True, en_colegio=True)
        .annotate(tiene_retiro=Exists(retiro_pendiente))
        .order_by('nombre')   # orden alfabético
    )

    cantidad = alumnos.count()

    return render(request, 'lista_alumnos.html', {
        'grado': grado,
        'nivel': nivel,
        'alumnos': alumnos,
        'cantidad': cantidad
    })


@login_required
def crear_retiro(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)

    # Verificar si ya existe retiro pendiente
    existe_pendiente = Retiro.objects.filter(
        alumno=alumno,
        estado='PENDIENTE'
    ).exists()

    if existe_pendiente:
        messages.warning(request, f"{alumno.nombre} ya tiene un retiro pendiente.")
        return redirect(request.META.get('HTTP_REFERER'))

    # Crear retiro si no existe
    Retiro.objects.create(
        alumno=alumno,
        grado=alumno.grado,
        estado='PENDIENTE'
    )

    messages.success(request, f"Retiro avisado para {alumno.nombre}")
    return redirect(request.META.get('HTTP_REFERER'))


@require_POST
@login_required
def crear_retiros_masivos(request):

    ids = request.POST.getlist('alumnos')

    if not ids:
        messages.warning(request, "No seleccionó alumnos.")
        return redirect(request.META.get('HTTP_REFERER'))

    alumnos = Alumno.objects.filter(id__in=ids)

    creados = 0
    repetidos = 0

    for alumno in alumnos:

        existe = Retiro.objects.filter(
            alumno=alumno,
            estado='PENDIENTE'
        ).exists()

        if existe:
            repetidos += 1
            continue

        Retiro.objects.create(
            alumno=alumno,
            grado=alumno.grado,
            estado='PENDIENTE'
        )

        creados += 1

    if creados:
        messages.success(request, f"{creados} retiros creados correctamente.")

    if repetidos:
        messages.warning(request, f"{repetidos} alumnos ya tenían retiro pendiente.")

    return redirect(request.META.get('HTTP_REFERER'))



# SECCIÓN INTERNO (Preparación)
@login_required
def lista_pendientes(request):
    retiros = Retiro.objects.filter(estado='PENDIENTE').order_by('hora_aviso')

    return render(request, 'lista_pendientes.html', {
        'retiros': retiros
    })


@login_required
def marcar_entregado(request, retiro_id):
    retiro = get_object_or_404(Retiro, id=retiro_id)

    grado_id = retiro.grado.id  

    # Marcar retiro como entregado
    retiro.estado = 'ENTREGADO'
    retiro.hora_entrega = timezone.now()
    retiro.save(update_fields=['estado', 'hora_entrega'])

    # Sacar alumno del colegio
    alumno = retiro.alumno
    alumno.en_colegio = False
    alumno.fecha_estado = timezone.localdate()  
    alumno.save(update_fields=['en_colegio', 'fecha_estado'])

    messages.success(request, f"{alumno.nombre} fue entregado correctamente.")

    return redirect('docente_pendientes', grado_id=grado_id)


# ===============================
# SECCIÓN DOCENTE
# ===============================
@login_required
def docente_seleccionar_grado(request):
    grados = Grado.objects.filter(activo=True).order_by('orden')
    return render(request, 'docente_seleccionar_grado.html', {
        'grados': grados
    })


@login_required
def docente_pendientes(request, grado_id):

    grado = get_object_or_404(Grado, id=grado_id)

    retiros = (
        Retiro.objects
        .select_related('alumno', 'grado')
        .filter(
            estado='PENDIENTE',
            grado=grado
        )
        .order_by('hora_aviso')
    )

    return render(request, 'docente_pendientes.html', {
        'grado': grado,
        'retiros': retiros
    })

    

@login_required
def cantidad_pendientes(request, grado_id):
    cantidad = Retiro.objects.filter(
        estado='PENDIENTE',
        grado_id=grado_id
    ).count()

    return JsonResponse({'cantidad': cantidad})


@login_required
def lista_pendientes_json(request, grado_id):
    retiros = Retiro.objects.filter(
        estado='PENDIENTE',
        alumno__grado_id=grado_id
    ).select_related('alumno')

    data = []

    for r in retiros:
        data.append({
            'id': r.id,
            'nombre': r.alumno.nombre
        })

    return JsonResponse({'retiros': data})


# Buscador global
@login_required
def buscar_alumnos_ajax(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'results': []})

    # Permitir 1 carácter si es número (para grados)
    if len(query) < 2 and not query.isdigit():
        return JsonResponse({'results': []})

    palabras = query.split()

    filtros = Q()

    for palabra in palabras:
        filtros &= (
            Q(nombre__icontains=palabra) |
            Q(grado__nombre__icontains=palabra)
        )

    retiro_pendiente = Retiro.objects.filter(
        alumno=OuterRef('pk'),
        estado='PENDIENTE'
    )

    alumnos = (
        Alumno.objects
        .filter(
            filtros,
            activo=True,
            en_colegio=True
        )
        .annotate(tiene_pendiente=Exists(retiro_pendiente))
        .select_related('grado')
        .order_by('nombre')[:15]
    )

    results = [
        {
            'id': a.id,
            'nombre': a.nombre,
            'grado': a.grado.nombre,
            'tiene_pendiente': a.tiene_pendiente
        }
        for a in alumnos
    ]

    return JsonResponse({'results': results})